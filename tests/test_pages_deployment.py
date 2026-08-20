import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pages_deployment", ROOT / "scripts" / "pages_deployment.py"
)
pages_deployment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pages_deployment)


class PagesDeploymentTests(unittest.TestCase):
    def test_build_manifest_records_commit_and_artifact_hashes(self):
        with TemporaryDirectory() as temp_dir:
            public = Path(temp_dir)
            for name in pages_deployment.ARTIFACTS:
                (public / name).write_bytes(f"content:{name}".encode())

            manifest = pages_deployment.build_manifest(public, "abc123")

            stored = json.loads(
                (public / "deployment-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest, stored)
            self.assertEqual(stored["commit"], "abc123")
            self.assertEqual(set(stored["artifacts"]), set(pages_deployment.ARTIFACTS))

    def test_verify_once_checks_commit_and_all_hashes(self):
        files = {
            name: f"deployed:{name}".encode() for name in pages_deployment.ARTIFACTS
        }
        manifest = {
            "schema_version": 1,
            "commit": "abc123",
            "artifacts": {
                name: pages_deployment.sha256_bytes(content)
                for name, content in files.items()
            },
        }

        def fake_fetch(url, timeout=20):
            path = urlparse(url).path.rsplit("/", 1)[-1]
            if path == "deployment-manifest.json":
                return json.dumps(manifest).encode()
            return files[path]

        with patch.object(pages_deployment, "fetch_bytes", side_effect=fake_fetch):
            result = pages_deployment.verify_once(
                "https://example.github.io/project/", "abc123"
            )
        self.assertEqual(result["commit"], "abc123")

    def test_verify_once_rejects_stale_deployment(self):
        stale = {"schema_version": 1, "commit": "old", "artifacts": {}}
        with patch.object(
            pages_deployment, "fetch_bytes", return_value=json.dumps(stale).encode()
        ):
            with self.assertRaisesRegex(
                pages_deployment.VerificationError, "deployed commit"
            ):
                pages_deployment.verify_once(
                    "https://example.github.io/project/", "new"
                )


if __name__ == "__main__":
    unittest.main()
