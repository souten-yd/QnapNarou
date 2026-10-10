#!/usr/bin/env python3
"""QNAP-only management UI. Upstream Narou Web UI remains at :8888.

No background polling, no persistent access log, no manually entered token.
Update requests require a same-origin browser and an ephemeral CSRF nonce.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import platform
import secrets
import subprocess
import sys
from urllib.parse import urlsplit

try:
    from tools.installer import architecture, fetch_release, STATUS_FILE, STATUS_DIR, write_status
    from tools.update_check import validate_release, parse_version
except ModuleNotFoundError:
    from installer import architecture, fetch_release, STATUS_FILE, STATUS_DIR, write_status
    from update_check import validate_release, parse_version

PORTAL_PORT = 8889
UPDATE_SCRIPT = Path(__file__).resolve().with_name("installer.py")
LAN_NETS = [ipaddress.ip_network(x) for x in
            ("127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12",
             "192.168.0.0/16", "100.64.0.0/10")]


def permitted_peer(ip):
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(address in net for net in LAN_NETS)


def current_version():
    cmd = ["/sbin/getcfg", "QnapNarou", "Version", "-f", "/etc/config/qpkg.conf"]
    value = subprocess.check_output(cmd, timeout=5, text=True).strip()
    return ".".join(map(str, parse_version(value)))


def html_page(nonce):
    # Original UI is preserved at :8888, this QNAP portal is separate.
    return """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QnapNarou 管理</title><style>
:root{color-scheme:dark;font-family:system-ui,-apple-system,sans-serif}
body{margin:0;background:#101823;color:#eaf2fd;min-height:100vh}
header{background:#182433;border-bottom:1px solid #304156;padding:19px 26px}
h1{font-size:1.25rem;margin:0}small{color:#9ab0c5}
main{max-width:760px;margin:auto;padding:24px}
section{background:#1b2939;border:1px solid #34445a;border-radius:18px;padding:24px;margin-bottom:16px}
h2{margin-top:0;font-size:1.05rem}
a,button{display:inline-block;border-radius:10px;padding:12px 16px;background:#4c98eb;color:#061626;border:0;
font:inherit;font-weight:650;text-decoration:none;cursor:pointer}
button:disabled{opacity:.45;cursor:not-allowed}
.secondary{background:#324456;color:#edf6ff}
.actions{display:flex;flex-wrap:wrap;gap:12px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;color:#afc3d8}
p{line-height:1.65}
</style></head><body>
<header><h1>QnapNarou <small>QTS 管理</small></h1></header>
<main><section><h2>小説ライブラリ</h2>
<p>本家 narou.rs の画面・操作方法をそのまま利用します。</p>
<a id="open" href="#">Narou Web UI を開く</a></section>
<section><h2>アプリ更新</h2>
<p>GitHub Releases から最新版を確認します。更新に個別トークンは不要です。更新時のみディスクに書き込みます。</p>
<div class="actions"><button id="check">最新版を確認</button>
<button id="install" disabled>最新版へ更新</button>
<button id="status" class="secondary">更新状況</button></div>
<pre id="result">更新確認を押してください。</pre></section>
<section><h2>アクセスとデータ保護</h2><p>LAN / Tailscale 内のみを想定しています。NASのポートをインターネットへ公開しないでください。
小説データはアプリ本体と別領域へ保存します。停電に備えてQNAPのバックアップも維持してください。</p></section></main>
<script>
const nonce="__NONCE__";
const out=document.getElementById('result');
document.getElementById('open').href=location.protocol+'//'+location.hostname+':8888/';
document.getElementById('check').onclick=async()=>{
  out.textContent='確認中...';document.getElementById('install').disabled=true;
  try{const r=await fetch('/api/check',{cache:'no-store'});const j=await r.json();
    if(!r.ok)throw Error(j.error||'取得失敗');
    out.textContent='現在: '+j.current_version+' / 最新: '+j.latest_version+
      (j.update_available?'（更新可能）':'（最新版）');
    document.getElementById('install').disabled=!j.update_available;
  }catch(e){out.textContent=String(e)}
};
document.getElementById('install').onclick=async()=>{
  if(!confirm('検証済みQPKGでアプリを更新します。実行中の小説処理は終了してから続けてください。'))return;
  document.getElementById('install').disabled=true;out.textContent='更新開始中...';
  try{const r=await fetch('/api/install',{method:'POST',headers:{'X-QN-Nonce':nonce}});
    const j=await r.json();if(!r.ok)throw Error(j.error||'更新開始失敗');
    out.textContent='更新処理を開始しました。更新状況ボタンで確認できます。';
  }catch(e){out.textContent=String(e)}
};
document.getElementById('status').onclick=async()=>{
  try{const r=await fetch('/api/status',{cache:'no-store'});out.textContent=JSON.stringify(await r.json(),null,2)}
  catch(e){out.textContent=String(e)}
};
</script></body></html>""".replace("__NONCE__", nonce)


class Handler(BaseHTTPRequestHandler):
    server_version = "QnapNarou/1"
    def log_message(self, *args):
        # QNAP HDD should remain idle when handling Web UI requests.
        pass

    def respond(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def allowed(self):
        if permitted_peer(self.client_address[0]):
            return True
        self.respond(403, {"error": "LAN or Tailscale peers only"})
        return False

    def do_GET(self):
        if not self.allowed(): return
        path = urlsplit(self.path).path
        if path == "/":
            page = html_page(self.server.csrf).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(page)
        elif path == "/api/status":
            try:
                value = json.loads(STATUS_FILE.read_text()) if STATUS_FILE.is_file() else {"phase": "idle"}
                self.respond(200, value)
            except (OSError, ValueError):
                self.respond(500, {"error": "status unavailable"})
        elif path == "/api/check":
            try:
                result = validate_release(fetch_release(), current_version(), architecture())
                self.respond(200, result)
            except Exception as exc:
                self.respond(502, {"error": str(exc)[:160]})
        else:
            self.respond(404, {"error": "not found"})

    def do_POST(self):
        if not self.allowed(): return
        if urlsplit(self.path).path != "/api/install":
            self.respond(404, {"error": "not found"}); return
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin", "")
        if (origin not in ("http://" + host, "https://" + host) or
                self.headers.get("X-QN-Nonce") != self.server.csrf or
                self.headers.get("Content-Length", "0") != "0"):
            self.respond(403, {"error": "same-origin update confirmation required"}); return
        if STATUS_FILE.is_file():
            try:
                if json.loads(STATUS_FILE.read_text()).get("phase") in (
                    "queued", "downloading", "installing", "rollback"):
                    self.respond(409, {"error": "update already in progress"}); return
            except (OSError, ValueError):
                pass
        try:
            current = current_version()
            if not validate_release(fetch_release(), current, architecture())["update_available"]:
                self.respond(409, {"error": "no update available"}); return
            write_status("queued")
            subprocess.Popen([sys.executable, str(UPDATE_SCRIPT), "--current", current,
                              "--staging", str(Path(os.environ["NAROU_DATA"]) / "updates")],
                             start_new_session=True, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             close_fds=True)
            self.respond(202, {"started": True})
        except Exception as exc:
            write_status("failed", str(exc)[:160])
            self.respond(500, {"error": "update could not start: " + str(exc)[:120]})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=PORTAL_PORT)
    args = parser.parse_args()
    if not os.environ.get("NAROU_DATA"):
        raise SystemExit("NAROU_DATA is required")
    if not 0 < args.port < 65536:
        raise SystemExit("invalid port")
    STATUS_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.csrf = secrets.token_urlsafe(32)
    httpd.serve_forever(poll_interval=2.0)


if __name__ == "__main__":
    main()
