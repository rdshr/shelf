from __future__ import annotations

import unittest

from framework_ir import load_framework_registry
from framework_packages import load_builtin_package_registry


class FrameworkPackageRegistryTest(unittest.TestCase):
    def test_every_framework_module_has_one_registered_package(self) -> None:
        framework_registry = load_framework_registry()
        package_registry = load_builtin_package_registry()

        package_registry.validate_against_framework(framework_registry)
        self.assertEqual(len(framework_registry.modules), len(package_registry.iter_registrations()))
        self.assertEqual(
            {module.module_id for module in framework_registry.modules},
            {registration.module_id for registration in package_registry.iter_registrations()},
        )


if __name__ == "__main__":
    unittest.main()
