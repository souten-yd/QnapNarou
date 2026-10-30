#!/usr/bin/env python3
"""Fail-closed QNAP-only build overlay for pest's stack-intensive preprocess parser.

Upstream narou.rs remains a pinned gitlink. The real DSL grammar and site YAML
are unchanged; only the compilation thread and source-size guard are patched.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

PINNED_UPSTREAM = "47bee6ba703441d3aa989e29694e3df485c4c643"
EXPECTED_PARSER_BLOB = "41d61b8351ec7518bcdf1fda3e8c9be966260942"
PARSER_FILE = Path("src/downloader/preprocess/parser.rs")
ENTRY = "pub fn parse_preprocess(source: &str) -> Result<Vec<Stmt>, String> {\n"
NEXT = "\nfn build_stmt("
MARKER = "QNAP_PREPROCESS_STACK_FIX"

# pest 2.9.4 prevents unchecked native stack exhaustion. Its ordinary caller
# stack may be too small for reviewed bundled DSLs. Give the parser a bounded
# dedicated 16 MiB stack; never disable pest's own overflow checks.
PROLOGUE = """// QNAP_PREPROCESS_STACK_FIX: keep the pest parser on a dedicated stack.
const QNAP_PREPROCESS_STACK_BYTES: usize = 16 * 1024 * 1024;
const QNAP_PREPROCESS_MAX_SOURCE_BYTES: usize = 256 * 1024;

pub fn parse_preprocess(source: &str) -> Result<Vec<Stmt>, String> {
    if source.len() > QNAP_PREPROCESS_MAX_SOURCE_BYTES {
        return Err("preprocess DSL exceeds QNAP source-size limit".to_string());
    }
    let owned = source.to_owned();
    std::thread::Builder::new()
        .name("narou-preprocess-parse".to_owned())
        .stack_size(QNAP_PREPROCESS_STACK_BYTES)
        .spawn(move || parse_preprocess_on_large_stack(&owned))
        .map_err(|err| format!("preprocess parser worker start failed: {err}"))?
        .join()
        .map_err(|_| "preprocess parser worker panicked".to_string())?
}

"""
TESTS = """
#[cfg(test)]
mod qnap_preprocess_stack_tests {
    use super::*;

    #[test]
    fn bundled_pixiv_and_alphapolis_parse_from_small_caller_stack() {
        let source_pairs = [
            ("Pixiv", include_str!("../../../webnovel/www.pixiv.net.yaml")),
            ("Alphapolis", include_str!("../../../webnovel/www.alphapolis.co.jp.yaml")),
        ];
        // QTS may invoke compilation from a worker with a modest native stack.
        // Successful parsing must not depend on the caller's stack size.
        let result = std::thread::Builder::new()
            .stack_size(2 * 1024 * 1024)
            .spawn(move || {
                for (name, yaml) in source_pairs {
                    let doc: serde_yaml::Value = serde_yaml::from_str(yaml).unwrap();
                    let src = doc.get("preprocess").and_then(|v| v.as_str()).unwrap();
                    assert!(
                        !parse_preprocess(src)
                            .unwrap_or_else(|err| panic!("{name}: {err}"))
                            .is_empty(),
                        "{name}: empty parsed DSL"
                    );
                }
            })
            .unwrap();
        result.join().unwrap();
    }

    #[test]
    fn oversized_dsl_fails_before_thread_spawn() {
        let source = "a".repeat(QNAP_PREPROCESS_MAX_SOURCE_BYTES + 1);
        assert!(parse_preprocess(&source).unwrap_err().contains("source-size limit"));
    }
}
"""

def rewritten_source(source: str) -> str:
    if source.count(ENTRY) != 1 or source.count(NEXT) != 1 or MARKER in source:
        raise ValueError("upstream preprocess parser changed or QNAP fix already applied")
    start = source.index(ENTRY)
    end = source.index(NEXT, start)
    original = source[start:end]
    if original.count("PreprocessParser::parse(Rule::program, source)") != 1:
        raise ValueError("unexpected pest parse implementation")
    if original.count("Ok(stmts)") != 1 or not original.rstrip().endswith("}"):
        raise ValueError("unexpected preprocess AST builder")
    worker = original.replace(ENTRY, "fn parse_preprocess_on_large_stack(source: &str) -> Result<Vec<Stmt>, String> {\n", 1)
    return source[:start] + PROLOGUE + worker + source[end:] + TESTS

def apply(repo: Path) -> None:
    repo = repo.resolve()
    root = repo.parent.parent
    gitlink = subprocess.check_output(["git", "rev-parse", "HEAD:upstream/narou.rs"], cwd=root, text=True).strip()
    checkout = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    if gitlink != PINNED_UPSTREAM or checkout != gitlink:
        raise ValueError("upstream gitlink/checkout is not the reviewed v0.5.5 commit")
    parser = repo / PARSER_FILE
    raw = parser.read_bytes()
    blob_hash = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob_hash != EXPECTED_PARSER_BLOB:
        raise ValueError("upstream parser source drift; refusing unreviewed QNAP patch")
    new_text = rewritten_source(raw.decode("utf-8"))
    parser.write_text(new_text, encoding="utf-8")

def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--source", type=Path, required=True)
    args = cli.parse_args()
    try:
        apply(args.source)
    except (OSError, ValueError, subprocess.CalledProcessError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
