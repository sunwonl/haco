import unittest
from backend.calculator import add, subtract, multiply, divide

class TestCalculator(unittest.TestCase):

    def test_add_positive_numbers(self):
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(100, 200), 300)

    def test_add_negative_numbers(self):
        self.assertEqual(add(-1, -2), -3)
        self.assertEqual(add(-10, -5), -15)

    def test_add_mixed_numbers(self):
        self.assertEqual(add(-1, 2), 1)
        self.assertEqual(add(5, -10), -5)

    def test_add_zero(self):
        self.assertEqual(add(0, 0), 0)
        self.assertEqual(add(5, 0), 5)
        self.assertEqual(add(0, -5), -5)

    def test_add_float_numbers(self):
        self.assertAlmostEqual(add(1.5, 2.5), 4.0)
        self.assertAlmostEqual(add(-1.5, 2.0), 0.5)
        self.assertAlmostEqual(add(0.1, 0.2), 0.3)

    def test_subtract_positive_numbers(self):
        self.assertEqual(subtract(5, 3), 2)
        self.assertEqual(subtract(10, 20), -10)

    def test_subtract_negative_numbers(self):
        self.assertEqual(subtract(-5, -3), -2)
        self.assertEqual(subtract(-3, -5), 2)

    def test_subtract_mixed_numbers(self):
        self.assertEqual(subtract(5, -3), 8)
        self.assertEqual(subtract(-5, 3), -8)

    def test_subtract_zero(self):
        self.assertEqual(subtract(0, 0), 0)
        self.assertEqual(subtract(5, 0), 5)
        self.assertEqual(subtract(0, 5), -5)

    def test_subtract_float_numbers(self):
        self.assertAlmostEqual(subtract(5.5, 2.5), 3.0)
        self.assertAlmostEqual(subtract(2.0, 1.5), 0.5)

    def test_multiply_positive_numbers(self):
        self.assertEqual(multiply(2, 3), 6)
        self.assertEqual(multiply(10, 10), 100)

    def test_multiply_negative_numbers(self):
        self.assertEqual(multiply(-2, -3), 6)
        self.assertEqual(multiply(-5, -10), 50)

    def test_multiply_mixed_numbers(self):
        self.assertEqual(multiply(-2, 3), -6)
        self.assertEqual(multiply(5, -4), -20)

    def test_multiply_by_zero(self):
        self.assertEqual(multiply(0, 5), 0)
        self.assertEqual(multiply(5, 0), 0)
        self.assertEqual(multiply(-5, 0), 0)

    def test_multiply_float_numbers(self):
        self.assertAlmostEqual(multiply(2.5, 2), 5.0)
        self.assertAlmostEqual(multiply(0.5, 0.5), 0.25)

    def test_divide_positive_numbers(self):
        self.assertEqual(divide(6, 3), 2)
        self.assertAlmostEqual(divide(10, 4), 2.5)

    def test_divide_negative_numbers(self):
        self.assertEqual(divide(-6, -3), 2)
        self.assertAlmostEqual(divide(-10, -4), 2.5)

    def test_divide_mixed_numbers(self):
        self.assertEqual(divide(6, -3), -2)
        self.assertAlmostEqual(divide(-10, 4), -2.5)

    def test_divide_by_one(self):
        self.assertEqual(divide(5, 1), 5)
        self.assertEqual(divide(-5, 1), -5)

    def test_divide_zero_by_number(self):
        self.assertEqual(divide(0, 5), 0)
        self.assertEqual(divide(0, -5), 0)

    def test_divide_float_numbers(self):
        self.assertAlmostEqual(divide(7.0, 2.0), 3.5)
        self.assertAlmostEqual(divide(1.0, 3.0), 1/3)

    def test_divide_by_zero(self):
        with self.assertRaises(ValueError) as cm:
            divide(5, 0)
        self.assertEqual(str(cm.exception), "Cannot divide by zero")

        with self.assertRaises(ValueError) as cm:
            divide(0, 0)
        self.assertEqual(str(cm.exception), "Cannot divide by zero")

if __name__ == '__main__':
    unittest.main()
