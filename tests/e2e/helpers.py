import http.server
import io
import random
import threading

from PIL import Image, ImageDraw


def pattern_jpeg(width=1200, height=800, seed=0, quality=88):
    rng = random.Random(seed)
    img = Image.new("RGB", (width, height), (rng.randint(30, 90), rng.randint(30, 90), rng.randint(30, 90)))
    d = ImageDraw.Draw(img)
    for _ in range(10):
        x0 = rng.randint(0, width - 100)
        y0 = rng.randint(0, height - 100)
        x1 = min(width, x0 + rng.randint(100, width // 2))
        y1 = min(height, y0 + rng.randint(100, height // 2))
        d.rectangle([x0, y0, x1, y1], fill=(rng.randint(120, 245), rng.randint(120, 245), rng.randint(120, 245)))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def serve(routes):
    store = dict(routes)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = store.get(self.path)
            if body is None:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
