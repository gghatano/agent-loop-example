"""実ブラウザでの画面遷移。fixtures/projects.json の実データで動かす。"""

import re

from playwright.sync_api import expect


def test_list_to_detail_and_back(page, base_url):
    page.goto(f"{base_url}/projects")
    rows = page.locator("tbody tr")
    expect(rows).to_have_count(3)

    page.get_by_role("link", name="需要予測PoC").click()
    expect(page).to_have_url(f"{base_url}/projects/102")
    expect(page.get_by_role("heading", level=1)).to_have_text("需要予測PoC")
    expect(page.locator("dd .badge")).to_have_text("保留")
    expect(page.get_by_role("heading", name="メンバー（2名）")).to_be_visible()
    expect(page.locator(".card table tbody tr").nth(0)).to_contain_text("鈴木担当")

    page.get_by_role("link", name="一覧へ戻る").click()
    expect(page).to_have_url(f"{base_url}/projects")


def test_every_list_link_opens_its_detail(page, base_url):
    page.goto(f"{base_url}/projects")
    links = page.locator("tbody a")
    count = links.count()
    names = [links.nth(i).inner_text() for i in range(count)]
    for name in names:
        page.goto(f"{base_url}/projects")
        page.get_by_role("link", name=name, exact=True).click()
        expect(page.get_by_role("heading", level=1)).to_have_text(name)


def test_header_navigation(page, base_url):
    page.goto(f"{base_url}/projects/101")
    page.locator("header nav").get_by_role("link", name="新規登録").click()
    expect(page).to_have_url(f"{base_url}/projects/new")
    page.locator("header nav").get_by_role("link", name="案件一覧").click()
    expect(page).to_have_url(f"{base_url}/projects")
    page.get_by_role("link", name="＋ 新規登録").click()
    expect(page).to_have_url(f"{base_url}/projects/new")


def test_new_form_blocks_empty_required_fields(page, base_url):
    page.goto(f"{base_url}/projects/new")
    page.get_by_role("button", name="登録").click()
    # 必須の案件名が空なので、ブラウザが送信を止める（ページは移動しない）
    expect(page).to_have_url(f"{base_url}/projects/new")
    assert page.locator("#name").evaluate("el => el.validity.valueMissing") is True
    assert page.locator("#client").evaluate("el => el.required") is True


def test_new_form_controls(page, base_url):
    page.goto(f"{base_url}/projects/new")
    expect(page.get_by_label("状態")).to_have_value("active")
    page.get_by_label("状態").select_option(label="保留")
    expect(page.get_by_label("状態")).to_have_value("paused")
    expect(page.get_by_label("開始日")).to_have_attribute("type", "date")
    expect(page.get_by_label("予算（円）")).to_have_attribute("inputmode", "numeric")
    page.get_by_role("link", name="キャンセル").click()
    expect(page).to_have_url(f"{base_url}/projects")


def test_unknown_project_returns_404(page, base_url):
    res = page.goto(f"{base_url}/projects/999")
    assert res.status == 404
    # 404 のリソース読み込みはブラウザが console error として出すので、このテストでは除外する
    page.console_errors[:] = [e for e in page.console_errors if not re.search(r"404", e)]
