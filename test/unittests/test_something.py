# write your first unittest!
import unittest


class TestSomething(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.var = "hello"

    def test_something(self):
        self.assertEqual("hello", self.var)

