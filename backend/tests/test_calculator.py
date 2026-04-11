import unittest
from backend.calculator import add, subtract, multiply, divide

class TestCalculator(unittest.TestCase):

    def test_add_integers(self):
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(-1, -1), -2)
        self.assertEqual(add(0, 0), 0)

    def test_add_floats(self):
        self.assertEqual(add(1.5, 2.5), 4.0)
        self.assertEqual(add(-1.5, 2.5), 1.0)
        self.assertEqual(add(0.0, 0.0), 0.0)
        self.assertAlmostEqual(add(0.1, 0.2), 0.3)

    def test_subtract_integers(self):
        self.assertEqual(subtract(5, 3), 2)
        self.assertEqual(subtract(3, 5), -2)
        self.assertEqual(subtract(-1, 1), -2)
        self.assertEqual(subtract(1, -1), 2)
        self.assertEqual(subtract(0, 0), 0)

    def test_subtract_floats(self):
        self.assertEqual(subtract(5.5, 2.5), 3.0)
        self.assertEqual(subtract(2.5, 5.5), -3.0)
        self.assertEqual(subtract(0.0, 0.0), 0.0)
        self.assertAlmostEqual(subtract(0.3, 0.1), 0.2)

    def test_multiply_integers(self):
        self.assertEqual(multiply(2, 3), 6)
        self.assertEqual(multiply(-2, 3), -6)
        self.assertEqual(multiply(-2, -3), 6)
        self.assertEqual(multiply(0, 5), 0)
        self.assertEqual(multiply(5, 0), 0)

    def test_multiply_floats(self):
        self.assertEqual(multiply(2.5, 2), 5.0)
        self.assertAlmostEqual(multiply(0.5, 0.5), 0.25)
        self.assertEqual(multiply(-2.5, 2.0), -5.0)

    def test_divide_integers(self):
        self.assertEqual(divide(6, 3), 2)
        self.assertEqual(divide(6, -3), -2)
        self.assertEqual(divide(-6, -3), 2)
        self.assertEqual(divide(0, 5), 0)

    def test_divide_floats(self):
        self.assertEqual(divide(5, 2), 2.5)
        self.assertEqual(divide(10.0, 4.0), 2.5)
        self.assertEqual(divide(-7.5, 2.5), -3.0)
        self.assertAlmostEqual(divide(1.0, 3.0), 0.3333333333333333)

    def test_divide_by_zero(self):
        with self.assertRaisesRegex(ValueError, "Cannot divide by zero"):
            divide(5, 0)
        with self.assertRaisesRegex(ValueError, "Cannot divide by zero"):
            divide(0, 0)

if __name__ == '__main__':
    unittest.main()