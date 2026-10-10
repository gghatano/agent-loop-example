"""画面表示用の整形。モック（mock/*.html）の表記が仕様。"""

from datetime import date

# 表示順もこの順（新規登録フォームの選択肢に使う）
STATUSES: dict[str, str] = {"active": "進行中", "paused": "保留", "closed": "完了"}


def yen(amount: int) -> str:
    return f"¥{amount:,}"


def status_label(status: str) -> str:
    # 未知の状態はコードのまま出す。画面を落とすより、おかしな値が見えるほうがよい
    return STATUSES.get(status, status)


def ymd(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%Y/%m/%d")


def period(start: str, end: str) -> str:
    return f"{ymd(start)} – {ymd(end)}"


def days(start: str, end: str) -> int:
    """開始日と終了日を両方含む日数。"""
    return (date.fromisoformat(end) - date.fromisoformat(start)).days + 1


def member_role(member: str, owner: str) -> str:
    return "担当" if member == owner else "メンバー"
