from __future__ import annotations

import os
import unittest
from unittest import mock

import main as shelf_main


class MainCliTest(unittest.TestCase):
    def _default_project_file(self) -> str:
        default_project_file = shelf_main.DEFAULT_PROJECT_FILE
        if default_project_file is None:
            self.skipTest("no projects/*/project.toml found")
        return str(default_project_file.relative_to(shelf_main.REPO_ROOT))

    def test_normalize_argv_defaults_to_serve(self) -> None:
        self.assertEqual(shelf_main._normalize_argv([]), ["serve"])
        self.assertEqual(shelf_main._normalize_argv(["--reload"]), ["serve", "--reload"])

    @mock.patch("main.uvicorn.run")
    @mock.patch("main.materialize_project_runtime")
    def test_serve_reload_materializes_project(self, materialize_project: mock.Mock, uvicorn_run: mock.Mock) -> None:
        result = shelf_main.main(
            [
                "serve",
                "--project-file",
                self._default_project_file(),
                "--reload",
            ]
        )

        self.assertEqual(result, 0)
        materialize_project.assert_called_once()
        uvicorn_run.assert_called_once()

    @mock.patch("main.uvicorn.run")
    @mock.patch("main.build_project_app")
    def test_serve_without_reload_builds_runtime_app(self, build_project_app: mock.Mock, uvicorn_run: mock.Mock) -> None:
        build_project_app.return_value = object()

        with mock.patch.dict(os.environ, {}, clear=True):
            result = shelf_main.main(
                [
                    "serve",
                    "--project-file",
                    self._default_project_file(),
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "9000",
                ]
            )

        self.assertEqual(result, 0)
        build_project_app.assert_called_once()
        uvicorn_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
