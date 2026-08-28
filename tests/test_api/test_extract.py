from io import BytesIO
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from trade_service_agents.api.app import app
from trade_service_agents.extraction.vision import get_client

client = TestClient(app)


def _fake_png_bytes() -> bytes:
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_extract_proforma_returns_parsed_json():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(
        text='{"supplier": {"name": "Acme Ltd"}}'
    )

    app.dependency_overrides[get_client] = lambda: mock_client
    try:
        response = client.post(
            "/extract_proforma",
            files={"file": ("invoice.png", _fake_png_bytes(), "image/png")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"supplier": {"name": "Acme Ltd"}}


def test_extract_rejects_empty_file():
    app.dependency_overrides[get_client] = lambda: MagicMock()
    try:
        response = client.post(
            "/extract",
            files={"file": ("invoice.png", b"", "image/png")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
