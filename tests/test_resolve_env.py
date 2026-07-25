import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import resolve_env
from resolve_api import ResolveAPI


class ResolveEnvironmentTests(unittest.TestCase):
    def setUp(self):
        resolve_env._safe_to_import = None

    def tearDown(self):
        resolve_env._safe_to_import = None

    def test_probe_receives_selected_module_path(self):
        with tempfile.TemporaryDirectory() as module_path:
            pathlib.Path(module_path, "DaVinciResolveScript.py").write_text(
                "def scriptapp(name):\n"
                "    return object()\n",
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"PYTHONPATH": ""}):
                self.assertTrue(resolve_env.scripting_safe_to_import(module_path))

    def test_custom_module_path_is_added_to_sys_path(self):
        with tempfile.TemporaryDirectory() as module_path:
            with mock.patch.dict(
                os.environ, {"RESOLVE_SCRIPT_PATH": module_path}, clear=False
            ):
                with mock.patch.object(sys, "path", list(sys.path)):
                    api = ResolveAPI.__new__(ResolveAPI)
                    self.assertEqual(api._find_scripting_module(), module_path)
                    self.assertIn(module_path, sys.path)


if __name__ == "__main__":
    unittest.main()
