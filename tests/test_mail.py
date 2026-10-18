from pathlib import Path
from unittest.mock import MagicMock, patch

from job_agent.mail import ResendConfig, load_recipient, send_digest_email


def test_load_recipient_plain(tmp_path: Path):
    path = tmp_path / ".email"
    path.write_text("person@example.com\n", encoding="utf-8")
    assert load_recipient(path) == "person@example.com"


def test_load_recipient_keyed(tmp_path: Path):
    path = tmp_path / ".email"
    path.write_text("to: other@example.com\n", encoding="utf-8")
    assert load_recipient(path) == "other@example.com"


def test_load_recipient_missing(tmp_path: Path):
    assert load_recipient(tmp_path / ".email") is None


def test_send_digest_uses_resend():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "msg_123"}
    with patch("job_agent.mail.httpx.post", return_value=mock_resp) as post:
        send_digest_email(
            rows=[],
            recipient="person@example.com",
            resend=ResendConfig(api_key="re_test", from_addr="Job <onboarding@resend.dev>"),
        )
    assert post.called
    kwargs = post.call_args.kwargs
    assert kwargs["headers"]["Authorization"] == "Bearer re_test"
    assert kwargs["json"]["to"] == ["person@example.com"]
