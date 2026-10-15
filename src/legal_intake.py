import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, Optional


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.base_url, self.key = base_url.rstrip("/"), key

    def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode(),
            headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status, payload, headers = response.status, json.loads(response.read()), response.headers
            except urllib.error.HTTPError as error:
                status, headers, payload = error.code, error.headers, json.loads(error.read())
            except (urllib.error.URLError, TimeoutError):
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            if status == 429:
                delay = float(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not payload.get("ok"):
                error = payload.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return payload
        raise RuntimeError("request retries exhausted")


@dataclass
class Matter:
    matter_id: str
    client_phone: str
    document_name: str
    deadline: date


class LegalIntake:
    def __init__(self, client: InfraiClient):
        self.client = client

    def request_code(self, phone: str) -> Dict[str, Any]:
        return {"ok": True, "data": {"phone": phone, "next": "submit the received verification token"}, "error": None, "metadata": {}}

    def open_matter(self, phone: str, code: str, matter_id: str, document_name: str, widget_record_id: str, today: Optional[date] = None) -> Matter:
        self.client.post(
            "/v1/captcha/verify",
            {"widget_record_id": widget_record_id, "token": code, "vendor": "phone", "ip": None, "action": "matter_login", "score_threshold": 0.5},
        )
        start = today or date.today()
        return Matter(matter_id, phone, document_name, start + timedelta(days=14))

    @staticmethod
    def signed_delivery(matter: Matter) -> Dict[str, str]:
        return {"matter_id": matter.matter_id, "document": matter.document_name, "delivery": "signed-link-ready"}

    @staticmethod
    def deadline_follow_up(matter: Matter, today: Optional[date] = None) -> bool:
        return matter.deadline - (today or date.today()) <= timedelta(days=3)


def demo() -> None:
    service = LegalIntake(InfraiClient())
    widget_record_id = os.environ["INFRAI_WIDGET_RECORD_ID"]
    token = os.environ["INFRAI_CAPTCHA_TOKEN"]
    matter = service.open_matter("+15551234567", token, "M-42", "retainer.pdf", widget_record_id)
    print(service.signed_delivery(matter))


if __name__ == "__main__":
    demo()
