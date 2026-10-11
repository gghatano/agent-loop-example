import pytest

from app import formatting as f


@pytest.mark.parametrize(
    ("amount", "expected"),
    [(0, "¥0"), (999, "¥999"), (1000, "¥1,000"), (48000000, "¥48,000,000"), (1234567890, "¥1,234,567,890")],
)
def test_yen(amount, expected):
    assert f.yen(amount) == expected


@pytest.mark.parametrize(("status", "label"), [("active", "進行中"), ("paused", "保留"), ("closed", "完了")])
def test_status_label(status, label):
    assert f.status_label(status) == label


def test_unknown_status_is_shown_as_is():
    assert f.status_label("archived") == "archived"


def test_statuses_order_matches_mock_select():
    assert list(f.STATUSES) == ["active", "paused", "closed"]


def test_period_uses_slashes_and_en_dash():
    assert f.period("2026-04-01", "2027-03-31") == "2026/04/01 – 2027/03/31"


def test_ymd_zero_pads():
    assert f.ymd("2026-01-05") == "2026/01/05"


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        ("2026-04-01", "2027-03-31", 365),  # モックの詳細画面の値
        ("2026-07-15", "2026-07-15", 1),  # 同日は1日
        ("2028-02-28", "2028-03-01", 3),  # うるう年をまたぐ
        ("2027-02-28", "2027-03-01", 2),
    ],
)
def test_days_counts_both_ends(start, end, expected):
    assert f.days(start, end) == expected


def test_invalid_date_raises():
    with pytest.raises(ValueError):
        f.days("2026-02-30", "2026-03-01")


def test_member_role():
    assert f.member_role("佐藤", "佐藤") == "担当"
    assert f.member_role("高橋", "佐藤") == "メンバー"
