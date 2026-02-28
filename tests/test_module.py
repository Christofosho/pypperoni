import unittest

from app.module import (
    ModuleBase,
)


class TestModuleBase(unittest.TestCase):

    def setUp(self):
        self.module_name = "test_module"
        self.module_code = "print('Hello, World!')"
        self.module_base = ModuleBase(name=self.module_name, code=self.module_code)

    def test_module_base_init(self):
        self.assertEqual(self.module_base.name, self.module_name)

    def test_set_as_main(self):
        self.module_base.set_as_main()
        self.assertTrue(self.module_base._is_main)

    def test_is_external(self):
        self.assertFalse(self.module_base.is_external())

    def test_is_package(self):
        self.assertFalse(self.module_base.is_package())

    def test_get_id_is_main(self):
        expected_id = 0
        self.module_base.set_as_main()
        self.assertEqual(self.module_base.get_id(), expected_id)

    def test_get_id_negative_one(self):
        expected_id = 3742630538
        self.assertEqual(self.module_base.get_id(), expected_id)

    def test_get_id_default(self):
        expected_id = 1
        self.module_base._id = 1
        self.assertEqual(self.module_base.get_id(), expected_id)

    def test_get_parent(self):
        self.assertIsNone(self.module_base.get_parent(None))


if __name__ == "__main__":
    unittest.main()
