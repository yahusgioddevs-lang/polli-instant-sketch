#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse
import json, os, urllib.request

API = "https://gen.pollinations.ai"
KEY = os.environ.get("POLLINATIONS_API_KEY", "")

HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Instant Polli Sketch</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; background: #0b0b0e; color: #e8e8ec; }
    h1 { font-size: 1.25rem; margin-bottom: .5rem; }
    input[type=text] { width: 100%; padding: .7rem; border-radius: .5rem; border: 1px solid #2a2a30; background: #14141a; color: #fff; }
    button { margin-top: .5rem; padding: .6rem 1rem; border-radius: .5rem; border: 0; background: #6c5ce7; color: #fff; cursor: pointer; }
    img { max-width: 100%; border-radius: .75rem; margin-top: 1rem; background: #14141a; }
    .err { color: #ff6b6b; margin-top: .5rem; }
    .row { display: flex; gap: .5rem; }
    .row > * { flex: 1; }
  </style>
</head>
<body>
  <h1>Instant Polli Sketch</h1>
  <input id="p" placeholder="Describe an image…"/>
  <div class="row">
    <input id="w" type="number" value="1024" placeholder="W"/>
    <input id="h" type="number" value="1024" placeholder="H"/>
  </div>
  <button onclick="go()">Generate</button>
  <pre id="o" class="err"></pre>
  <img id="r" hidden alt="result"/>
  <script>
    async function go(){
      const p=document.getElementById('p').value.trim();
      if(!p)return;
      const w=parseInt(document.getElementById('w').value)||1024;
      const h=parseInt(document.getElementById('h').value)||1024;
      document.getElementById('o').textContent='Generating…';
      document.getElementById('r').hidden=true;
      try{
        const url=`${location.origin}/generate?${new URLSearchParams({p,w,h}).toString()}`;
        const j=await (await fetch(url)).json();
        if(j.ok){ document.getElementById('r').src=j.url; document.getElementById('r').hidden=false; document.getElementById('o').textContent=''; }
        else { document.getElementById('o').textContent=j.error||'error'; }
      }catch(e){ document.getElementById('o').textContent=String(e); }
    }
  </script>
</body>
</html>
"""

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.respond(200, "text/html", HTML)
            return
        if self.path.startswith("/generate"):
            q = urlparse(self.path).query
            params = dict(x.split("=",1) for x in q.split("&") if "=" in x)
            prompt = params.get("p","")
            w = params.get("w","1024")
            h = params.get("h","1024")
            if not prompt:
                self.respond(400, "application/json", json.dumps({"error":"missing prompt"}))
                return
            url = f"{API}/image/{urllib.parse.quote(prompt)}?model=flux&width={w}&height={h}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KEY}"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    final = r.geturl()
                    self.respond(200, "application/json", json.dumps({"ok": True, "url": final}))
                    return
            except Exception as e:
                self.respond(502, "application/json", json.dumps({"error": str(e)}))
                return
        self.respond(404, "text/plain", "not found")

    def respond(self, code, ctype, body):
        body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype+"; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT","8080"))), H).serve_forever()
