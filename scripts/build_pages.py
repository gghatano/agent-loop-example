"""GitHub Pages 用のレポートを site/ に生成する。

  uv run python scripts/build_pages.py

scripts/vrt.py を実行して、画面ごとのモック・実装・差分の画像と数値を並べる。
あわせて docs/failures.md と docs/walkthrough.md、main の履歴を載せる。
VRT が赤くてもレポートは作る（赤い状態を見せるのが目的）。
"""

import html
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
VRT = ROOT / ".agent" / "vrt"
LINE = re.compile(r"^(ok  |FAIL) (\w+)\s+diff=(\d+)px \(([\d.]+)%\) console_errors=(\d+)")
LABELS = {"list": "一覧 /projects", "detail": "詳細 /projects/101", "new": "新規登録 /projects/new"}

CSS = """
:root { --ink:#1f2328; --muted:#656d76; --line:#d0d7de; --bg:#ffffff; --panel:#f6f8fa; --ok:#1a7f37; --ng:#cf222e; }
@media (prefers-color-scheme: dark) {
  :root { --ink:#e6edf3; --muted:#9198a1; --line:#3d444d; --bg:#0d1117; --panel:#151b23; --ok:#3fb950; --ng:#f85149; }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.7 system-ui, sans-serif; }
main { max-width:1200px; margin:0 auto; padding:24px 16px 64px; }
h1 { font-size:24px; margin:0 0 4px; } h2 { font-size:19px; margin:40px 0 12px; border-bottom:1px solid var(--line); padding-bottom:6px; }
.meta { color:var(--muted); font-size:13px; }
.status { display:inline-block; padding:2px 10px; border-radius:12px; font-weight:600; font-size:13px; border:1px solid currentColor; }
.ok { color:var(--ok); } .ng { color:var(--ng); }
.screen { border:1px solid var(--line); border-radius:8px; padding:16px; margin:16px 0; background:var(--panel); }
.screen h3 { margin:0 0 8px; font-size:16px; display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
.shots { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; }
.shots figure { margin:0; } .shots figcaption { font-size:12px; color:var(--muted); }
.shots img { width:100%; border:1px solid var(--line); border-radius:4px; background:#fff; display:block; }
@media (max-width: 720px) { .shots { grid-template-columns:1fr; } }
table { border-collapse:collapse; width:100%; font-size:13px; display:block; overflow-x:auto; }
th, td { border:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }
th { background:var(--panel); }
code { font-size:0.9em; background:var(--panel); padding:1px 4px; border-radius:4px; }
pre { background:var(--panel); padding:12px; overflow-x:auto; border-radius:6px; }
ol.log { padding-left:20px; font-size:13px; } ol.log code { background:none; padding:0; color:var(--muted); }
a { color:inherit; }
"""


def run_vrt() -> list[dict]:
    out = subprocess.run([sys.executable, "scripts/vrt.py"], check=False, cwd=ROOT, capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        if m := LINE.match(line):
            rows.append({"ok": m[1] == "ok  ", "name": m[2], "px": int(m[3]), "pct": m[4], "errors": int(m[5])})
    return rows


def md(path: Path) -> str:
    if not path.exists():
        return ""
    return markdown.markdown(path.read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])


def git_log() -> str:
    out = subprocess.run(
        ["git", "log", "--format=%h%x09%ad%x09%s", "--date=format:%Y-%m-%d %H:%M", "-n", "30"],
        check=False, cwd=ROOT, capture_output=True, text=True,
    ).stdout
    items = []
    for line in out.splitlines():
        sha, date, subject = line.split("\t", 2)
        items.append(f"<li><code>{sha} {date}</code> {html.escape(subject)}</li>")
    return "<ol class='log'>" + "".join(items) + "</ol>"


def main() -> int:
    shutil.rmtree(SITE, ignore_errors=True)
    (SITE / "vrt").mkdir(parents=True)
    rows = run_vrt()
    for png in VRT.glob("*.png"):
        shutil.copy(png, SITE / "vrt" / png.name)
    shutil.copytree(ROOT / "mock", SITE / "mock")

    all_ok = bool(rows) and all(r["ok"] for r in rows)
    screens = []
    for r in rows:
        cls = "ok" if r["ok"] else "ng"
        screens.append(f"""
<section class="screen">
  <h3>{html.escape(LABELS.get(r['name'], r['name']))}
    <span class="status {cls}">{'一致' if r['ok'] else '不一致'}</span>
    <span class="meta">diff {r['px']:,}px（{r['pct']}%）・console error {r['errors']}件・<a href="mock/{r['name']}.html">モックを開く</a></span>
  </h3>
  <div class="shots">
    <figure><img loading="lazy" src="vrt/{r['name']}.mock.png" alt="モック"><figcaption>モック（mock/{r['name']}.html）</figcaption></figure>
    <figure><img loading="lazy" src="vrt/{r['name']}.app.png" alt="実装"><figcaption>実装</figcaption></figure>
    <figure><img loading="lazy" src="vrt/{r['name']}.diff.png" alt="差分"><figcaption>差分（赤 = 不一致の画素）</figcaption></figure>
  </div>
</section>""")

    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], check=False, cwd=ROOT, capture_output=True, text=True).stdout.strip()
    built = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    walkthrough = md(ROOT / "docs" / "walkthrough.md")
    page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>agent-loop-example</title><style>{CSS}</style></head>
<body><main>
<h1>agent-loop-example</h1>
<p class="meta"><a href="https://github.com/gghatano/agent-loop-template">agent-loop-template</a> の利用例。
main <code>{sha}</code> 時点・{built} 生成</p>
<p>モックと実装の一致（Issue #1）:
<span class="status {'ok' if all_ok else 'ng'}">{'3画面とも一致' if all_ok else '未達'}</span></p>
<h2>画面差分</h2>
{''.join(screens) or '<p>VRT を実行できなかった。</p>'}
{f'<h2>経過</h2>{walkthrough}' if walkthrough else ''}
<h2>失敗ログ（docs/failures.md）</h2>
{md(ROOT / 'docs' / 'failures.md')}
<h2>main の履歴</h2>
{git_log()}
</main></body></html>
"""
    (SITE / "index.html").write_text(page, encoding="utf-8")
    print(f"site/index.html built ({len(rows)} screens, all_ok={all_ok})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
