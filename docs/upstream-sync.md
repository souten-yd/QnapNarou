# Upstream sync procedure

QnapNarou pins **the entire** original Rust source as a Git submodule at
`upstream/narou.rs`. Never manually copy random parts of an upstream release,
because doing so risks losing the original Web UI, site definitions, and
licensing changes.

To check for an upstream update **on demand**, from the QnapNarou Git repo:

```sh
git submodule update --init --recursive
python3 tools/update_upstream.py
```

Review listed upstream commits for UI/API changes, dependency updates,
license notices, and breaking behavior. Then explicitly choose the printed SHA:

```sh
git checkout -b sync/narou-YYYYMMDD
python3 tools/update_upstream.py --apply --expected-sha <printed-40-char-SHA>
python3 -m unittest discover -s tests -v
git diff --cached --submodule=log
git commit -m "chore(upstream): track reviewed narou.rs SHA"
git push -u origin sync/narou-YYYYMMDD
```

Open a PR and complete the QDK build, QTS Web UI, update and persistence
acceptance gates before merge. **Do not automatically approve or merge an
upstream sync PR.** No scheduled background GitHub Action or CI build is
required for this update check. The downloader has no ongoing idle workload.

Maintaining a pinned, explicit upstream SHA also makes rollback/reproduction
possible and avoids silently changing source during QPKG releases.
