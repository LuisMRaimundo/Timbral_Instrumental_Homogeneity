from __future__ import annotations

import os
import unittest

from homogeneity_analyser.utils.output_paths import export_directory, new_export_path


class TestOutputPaths(unittest.TestCase):
    def test_new_export_path_creates_file(self):
        p = new_export_path("pytest_", ".txt")
        self.assertTrue(os.path.isabs(p))
        self.assertTrue(p.endswith(".txt"))
        with open(p, "w", encoding="utf-8") as f:
            f.write("x")
        self.assertTrue(os.path.isfile(p))
        os.remove(p)

    def test_export_directory_exists(self):
        d = export_directory()
        self.assertTrue(d.is_dir())


if __name__ == "__main__":
    unittest.main()
