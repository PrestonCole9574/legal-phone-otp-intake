from datetime import date

from src.legal_intake import LegalIntake, Matter


class FakeClient:
    def __init__(self):
        self.calls = []

    def post(self, path, body):
        self.calls.append((path, body))
        return {"ok": True, "data": {}, "error": None, "metadata": {}}


def test_verified_phone_opens_matter_and_triggers_follow_up():
    client = FakeClient()
    service = LegalIntake(client)
    matter = service.open_matter("+15550001111", "123456", "M-42", "retainer.pdf", "widget-42", date(2026, 9, 1))
    assert client.calls == [
        (
            "/v1/captcha/verify",
            {"widget_record_id": "widget-42", "token": "123456", "vendor": "phone", "ip": None, "action": "matter_login", "score_threshold": 0.5},
        )
    ]
    assert service.signed_delivery(matter)["delivery"] == "signed-link-ready"
    assert service.deadline_follow_up(matter, date(2026, 9, 12)) is True
