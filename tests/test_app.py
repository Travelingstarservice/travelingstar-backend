import unittest
from pathlib import Path

from app import create_app


class AppIntegrationTests(unittest.TestCase):
    def test_root_serves_frontend_when_build_exists(self):
        frontend_dir = Path(__file__).resolve().parents[2] / "traveling-star-frontend" / "dist"
        frontend_dir.mkdir(parents=True, exist_ok=True)
        (frontend_dir / "index.html").write_text("<h1>Frontend build loaded</h1>", encoding="utf-8")

        app = create_app()
        client = app.test_client()

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Frontend build loaded", response.get_data(as_text=True))
        self.assertEqual(response.mimetype, "text/html")


if __name__ == "__main__":
    unittest.main()
