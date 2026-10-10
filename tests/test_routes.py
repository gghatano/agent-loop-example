"""HTTP レベルの結合テスト。

案件データを fixtures とは別のデータに差し替えて描画する。
テンプレートに fixtures の値を直書きしていれば、ここで落ちる。
"""

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_projects

ALT = [
    {"id": 7, "name": "物流最適化", "client": "西海運輸", "status": "closed", "owner": "中村", "budget": 1500,
     "start": "2028-02-28", "end": "2028-03-01", "description": "配送ルートの最適化。", "members": ["小林", "中村"]},
    {"id": 3, "name": "価格改定シミュレーター", "client": "北辰電機", "status": "active", "owner": "山本",
     "budget": 0, "start": "2027-01-01", "end": "2027-12-31", "description": "価格改定の影響試算。", "members": []},
]
FIXTURE_VALUES = ["基幹システム刷新", "北洋物産株式会社", "佐藤", "¥48,000,000", "101"]


@pytest.fixture
def client():
    app.dependency_overrides[get_projects] = lambda: ALT
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def real_client():
    return TestClient(app)


def rows(html: str) -> list[str]:
    body = html.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
    return re.findall(r"<tr>(.*?)</tr>", body, re.DOTALL)


def text(fragment: str) -> str:
    return re.sub(r"<[^>]+>", "|", fragment)


def test_list_renders_given_data_in_order(client):
    html = client.get("/projects").text
    r = rows(html)
    assert len(r) == 2
    assert "物流最適化" in r[0] and "価格改定シミュレーター" in r[1]
    assert 'href="/projects/7"' in r[0]
    assert "¥1,500" in r[0] and "¥0" in r[1]
    assert 'class="badge closed">完了' in r[0] and 'class="badge active">進行中' in r[1]
    assert "2028/02/28 – 2028/03/01" in r[0]


def test_list_has_no_hardcoded_fixture_values(client):
    html = client.get("/projects").text
    for value in FIXTURE_VALUES:
        assert value not in html


def test_list_with_no_projects(client):
    app.dependency_overrides[get_projects] = lambda: []  # noqa: PIE807  FastAPI は依存のシグネチャを読むので list は渡せない
    res = client.get("/projects")
    assert res.status_code == 200
    assert rows(res.text) == []


def test_detail_renders_given_project(client):
    html = client.get("/projects/7").text
    assert "<h1>物流最適化</h1>" in html
    assert "西海運輸" in html and "¥1,500" in html
    assert "2028/02/28 – 2028/03/01（3日）" in html
    assert "メンバー（2名）" in html
    member_rows = [text(r) for r in rows(html.split("メンバー（", 1)[1])]
    assert member_rows == ["|1||小林||メンバー|", "|2||中村||担当|"]
    for value in FIXTURE_VALUES:
        assert value not in html


def test_detail_with_no_members(client):
    html = client.get("/projects/3").text
    assert "メンバー（0名）" in html


@pytest.mark.parametrize("path", ["/projects/999", "/projects/101"])
def test_unknown_project_is_404(client, path):
    assert client.get(path).status_code == 404


def test_non_numeric_id_is_rejected(client):
    assert client.get("/projects/abc").status_code == 422


def test_new_form_lists_statuses_in_order(client):
    html = client.get("/projects/new").text
    assert re.findall(r'<option value="(\w+)">', html) == ["active", "paused", "closed"]
    for name in ["name", "client", "status", "budget", "start", "end"]:
        assert f'name="{name}"' in html


def test_real_fixtures_render_every_project(real_client):
    for pid in (101, 102, 103):
        assert real_client.get(f"/projects/{pid}").status_code == 200


def test_stylesheet_is_the_mock_css(real_client):
    from app.main import ROOT

    res = real_client.get("/static/style.css")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/css")
    assert res.text == (ROOT / "mock" / "style.css").read_text(encoding="utf-8")
