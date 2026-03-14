from __future__ import annotations

import os
import unittest
from unittest import mock

import main as shelf_main


class MainCliTest(unittest.TestCase):
    def test_normalize_argv_defaults_to_serve(self) -> None:
        self.assertEqual(shelf_main._normalize_argv([]), ["serve"])
        self.assertEqual(shelf_main._normalize_argv(["--reload"]), ["serve", "--reload"])
        self.assertEqual(shelf_main._normalize_argv(["legacy-reference-shelf"]), ["legacy-reference-shelf"])

    @mock.patch("main.run_reference_pipeline")
    def test_reference_shelf_command_runs_legacy_pipeline(self, run_reference_pipeline: mock.Mock) -> None:
        result = shelf_main.main(["legacy-reference-shelf"])

        self.assertEqual(result, 0)
        run_reference_pipeline.assert_called_once_with()

    @mock.patch("main.uvicorn.run")
    @mock.patch("main.materialize_registered_project")
    def test_serve_reload_materializes_and_watches_project_inputs(
        self,
        materialize_registered_project: mock.Mock,
        uvicorn_run: mock.Mock,
    ) -> None:
        result = shelf_main.main(
            [
                "serve",
                "--product-spec-file",
                "projects/knowledge_base_basic/product_spec.toml",
                "--reload",
                "--port",
                "8011",
            ]
        )

        self.assertEqual(result, 0)
        materialize_registered_project.assert_called_once()
        uvicorn_run.assert_called_once()
        args, kwargs = uvicorn_run.call_args
        self.assertEqual(args[0], "project_runtime.app_factory:app")
        self.assertTrue(kwargs["reload"])
        self.assertEqual(kwargs["port"], 8011)
        self.assertEqual(kwargs["reload_dirs"], [str(path) for path in shelf_main.RELOAD_DIRS])
        self.assertEqual(kwargs["reload_includes"], shelf_main.RELOAD_INCLUDES)

    @mock.patch("main.uvicorn.run")
    @mock.patch("main.build_project_app")
    def test_serve_without_reload_builds_runtime_app(
        self,
        build_project_app: mock.Mock,
        uvicorn_run: mock.Mock,
    ) -> None:
        runtime_app = object()
        build_project_app.return_value = runtime_app

        with mock.patch.dict(os.environ, {}, clear=True):
            result = shelf_main.main(
                [
                    "serve",
                    "--product-spec-file",
                    "projects/knowledge_base_basic/product_spec.toml",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "9000",
                ]
            )
            self.assertEqual(
                os.environ.get(shelf_main.PRODUCT_SPEC_FILE_ENV),
                str((shelf_main.REPO_ROOT / "projects/knowledge_base_basic/product_spec.toml").resolve()),
            )

        self.assertEqual(result, 0)
        build_project_app.assert_called_once()
        uvicorn_run.assert_called_once_with(runtime_app, host="0.0.0.0", port=9000)


if __name__ == "__main__":
    unittest.main()
