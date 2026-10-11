"""HTTP レベルの結合テスト。

案件データを fixtures とは別のデータに差し替えて描画し、画面のすべての項目を期待値の表と完全一致で比べる。
一部の項目だけを見るテストは、見ていない項目の直書きや取り違えを通してしまう（docs/failures.md 2026-10-10 #3）。
"""

import copy
import re
from html import escape

import pytest
from fastapi.testclient import TestClient

from app import formatting
from app.main import ROOT, app, get_projects

ALT = [
    # 担当者が先頭メンバーではない / 完了 / うるう年をまたぐ
    {"id": 7, "name": "物流最適化", "client": "西海運輸", "status": "closed", "owner": "中村", "budget": 1500,
     "start": "2028-02-28", "end": "2028-03-01", "description": "配送ルートの最適化。", "members": ["小林", "中村"]},
    # 0円 / 開始日と終了日が同じ / メンバーなし
    {"id": 3, "name": "価格改定シミュレーター", "client": "北辰電機", "status": "active", "owner": "山本",
     "budget": 0, "start": "2027-05-01", "end": "2027-05-01", "description": "価格改定の影響試算。", "members": []},
    # HTML を含む値 / 未知の状態 / 担当者名を含む別名・同名の重複
    {"id": 9, "name": "<b>x</b>", "client": "<i>c</i>", "status": "archived", "owner": "佐藤", "budget": 1,
     "start": "2027-01-01", "end": "2027-01-02", "description": "<script>alert(1)</script>",
     "members": ["佐", "佐藤", "佐藤"]},
]

# 期待値は表として手で書く（実装と同じ関数で組み立てると、実装の誤りをそのまま写してしまう）
EXPECTED_LIST = [
    ["7", '<a href="/projects/7">物流最適化</a>', "西海運輸", '<span class="badge closed">完了</span>', "中村",
     "¥1,500", "2028/02/28 – 2028/03/01"],
    ["3", '<a href="/projects/3">価格改定シミュレーター</a>', "北辰電機", '<span class="badge active">進行中</span>',
     "山本", "¥0", "2027/05/01 – 2027/05/01"],
    ["9", f'<a href="/projects/9">{escape("<b>x</b>")}</a>', escape("<i>c</i>"),
     '<span class="badge archived">archived</span>', "佐藤", "¥1", "2027/01/01 – 2027/01/02"],
]
EXPECTED_DETAIL = {
    7: {
        "title": "物流最適化 | 案件管理",
        "h1": "物流最適化",
        "dl": [("案件ID", "7"), ("顧客", "西海運輸"), ("状態", '<span class="badge closed">完了</span>'),
               ("担当", "中村"), ("予算", "¥1,500"), ("期間", "2028/02/28 – 2028/03/01（3日）")],
        "description": "配送ルートの最適化。",
        "members_heading": "メンバー（2名）",
        "members": [["1", "小林", "メンバー"], ["2", "中村", "担当"]],
    },
    3: {
        "title": "価格改定シミュレーター | 案件管理",
        "h1": "価格改定シミュレーター",
        "dl": [("案件ID", "3"), ("顧客", "北辰電機"), ("状態", '<span class="badge active">進行中</span>'),
               ("担当", "山本"), ("予算", "¥0"), ("期間", "2027/05/01 – 2027/05/01（1日）")],
        "description": "価格改定の影響試算。",
        "members_heading": "メンバー（0名）",
        "members": [],
    },
    9: {
        "title": f"{escape('<b>x</b>')} | 案件管理",
        "h1": escape("<b>x</b>"),
        "dl": [("案件ID", "9"), ("顧客", escape("<i>c</i>")), ("状態", '<span class="badge archived">archived</span>'),
               ("担当", "佐藤"), ("予算", "¥1"), ("期間", "2027/01/01 – 2027/01/02（2日）")],
        "description": escape("<script>alert(1)</script>"),
        # 同名の重複は別人として数え、名前が担当者と一致すれば担当とする（docs/decisions.md）
        "members_heading": "メンバー（3名）",
        "members": [["1", "佐", "メンバー"], ["2", "佐藤", "担当"], ["3", "佐藤", "担当"]],
    },
}


@pytest.fixture
def client():
    app.dependency_overrides[get_projects] = lambda: copy.deepcopy(ALT)
    yield TestClient(app)
    app.dependency_overrides.clear()


def tbody_rows(html: str) -> list[list[str]]:
    body = html.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
    return [re.findall(r"<td[^>]*>(.*?)</td>", r, re.DOTALL) for r in re.findall(r"<tr>(.*?)</tr>", body, re.DOTALL)]


def one(pattern: str, html: str) -> str:
    found = re.findall(pattern, html, re.DOTALL)
    assert len(found) == 1, f"{pattern!r} matched {len(found)} times"
    return found[0]


def test_list_matches_expected_table(client):
    assert tbody_rows(client.get("/projects").text) == EXPECTED_LIST


def test_list_with_no_projects(client):
    app.dependency_overrides[get_projects] = lambda: []  # noqa: PIE807  FastAPI は依存のシグネチャを読むので list は渡せない
    res = client.get("/projects")
    assert res.status_code == 200
    assert tbody_rows(res.text) == []


@pytest.mark.parametrize("pid", sorted(EXPECTED_DETAIL))
def test_detail_matches_expected(client, pid):
    exp = EXPECTED_DETAIL[pid]
    html = client.get(f"/projects/{pid}").text
    assert one(r"<title>(.*?)</title>", html) == exp["title"]
    assert one(r"<h1>(.*?)</h1>", html) == exp["h1"]
    assert re.findall(r"<dt>(.*?)</dt><dd>(.*?)</dd>", html) == exp["dl"]
    assert one(r"</dl>\s*<p>(.*?)</p>", html) == exp["description"]
    assert one(r"<h2>(メンバー.*?)</h2>", html) == exp["members_heading"]
    members_html = html.split(exp["members_heading"], 1)[1]
    assert tbody_rows(members_html) == exp["members"]


def test_no_raw_html_from_data_reaches_the_page(client):
    for path in ("/projects", "/projects/9"):
        html = client.get(path).text
        for raw in ("<script>", "<b>x</b>", "<i>c</i>"):
            assert raw not in html


def test_leading_zeros_in_path_resolve_to_the_same_project(client):
    html = client.get("/projects/007").text
    assert ("案件ID", "7") in re.findall(r"<dt>(.*?)</dt><dd>(.*?)</dd>", html)


@pytest.mark.parametrize("path", ["/projects/0", "/projects/-1", "/projects/999", "/projects/101"])
def test_unknown_project_is_404(client, path):
    assert client.get(path).status_code == 404


def test_non_numeric_id_is_rejected(client):
    assert client.get("/projects/abc").status_code == 422


def test_new_form_options_follow_statuses(client, monkeypatch):
    # 選択肢がテンプレートの直書きではなく STATUSES から作られていることを、状態を1つ増やして確かめる
    monkeypatch.setitem(formatting.STATUSES, "archived", "アーカイブ")
    html = client.get("/projects/new").text
    assert re.findall(r'<option value="(\w+)">([^<]*)</option>', html) == list(formatting.STATUSES.items())


def test_new_form_fields(client):
    html = client.get("/projects/new").text
    for name in ["name", "client", "status", "budget", "start", "end"]:
        assert f'name="{name}"' in html


def test_real_fixtures_render_every_project():
    real = TestClient(app)
    for pid in (101, 102, 103):
        assert real.get(f"/projects/{pid}").status_code == 200


def test_stylesheet_is_the_mock_css():
    res = TestClient(app).get("/static/style.css")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/css")
    assert res.text == (ROOT / "mock" / "style.css").read_text(encoding="utf-8")
