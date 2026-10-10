"""モック HTML と実装の画面を同じブラウザで撮り、ピクセル差分を測る。

  uv run python scripts/vrt.py          # 差分が 0 でない画面があれば exit 1
差分画像は .agent/vrt/ に出る（赤い画素が不一致）。
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".agent" / "vrt"
VIEWPORT = {"width": 1280, "height": 800}
# モック → 実装の URL パス
SCREENS = {
    "list": "/projects",
    "detail": "/projects/101",
    "new": "/projects/new",
}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def launch(p):
    exe = os.environ.get("PW_CHROMIUM") or ("/opt/pw-browsers/chromium" if Path("/opt/pw-browsers/chromium").exists() else None)
    return p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()


def shoot(page, url: str, path: Path) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url, wait_until="networkidle")
    page.screenshot(path=path, full_page=True)
    return errors


def diff(a: Path, b: Path, out: Path) -> tuple[int, int]:
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    w, h = max(ia.width, ib.width), max(ia.height, ib.height)
    pa, pb = Image.new("RGB", (w, h), "white"), Image.new("RGB", (w, h), "white")
    pa.paste(ia), pb.paste(ib)
    mask = ImageChops.difference(pa, pb).convert("L").point(lambda v: 255 if v else 0)
    bad = mask.histogram()[255]
    overlay = pb.copy()
    overlay.paste(Image.new("RGB", (w, h), (255, 0, 0)), mask=mask)
    Image.blend(pb, overlay, 0.6).save(out)
    return bad, w * h


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT,
    )
    failed = False
    try:
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        with sync_playwright() as p:
            browser = launch(p)
            for name, path in SCREENS.items():
                ctx = browser.new_context(viewport=VIEWPORT)
                mock_png, app_png = OUT / f"{name}.mock.png", OUT / f"{name}.app.png"
                shoot(ctx.new_page(), (ROOT / "mock" / f"{name}.html").as_uri(), mock_png)
                errors = shoot(ctx.new_page(), f"http://127.0.0.1:{port}{path}", app_png)
                bad, total = diff(mock_png, app_png, OUT / f"{name}.diff.png")
                ok = bad == 0 and not errors
                failed |= not ok
                print(f"{'ok  ' if ok else 'FAIL'} {name:7s} diff={bad}px ({bad / total:.4%}) console_errors={len(errors)}")
                for e in errors:
                    print(f"       console: {e}")
                ctx.close()
            browser.close()
    finally:
        server.terminate()
    if failed:
        print(f"差分画像: {OUT.relative_to(ROOT)}/<screen>.diff.png（赤 = 不一致）")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
