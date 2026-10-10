from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_pages_respond():
    for path in ["/projects", "/projects/101", "/projects/new"]:
        assert client.get(path).status_code == 200


def test_unknown_project_is_404():
    assert client.get("/projects/999").status_code == 404
