from typing import Union

def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Adds two numbers and returns the sum."""
    return a + b

def subtract(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Subtracts the second number from the first and returns the difference."""
    return a - b

def multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Multiplies two numbers and returns the product."""
    return a * b

def divide(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Divides the first number by the second and returns the quotient.
    Raises ValueError if the divisor (b) is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == '__main__':
    # Example usage for direct execution and basic demonstration
    print(f"3 + 5 = {add(3, 5)}")
    print(f"10 - 4 = {subtract(10, 4)}")
    print(f"6 * 7 = {multiply(6, 7)}")
    print(f"10 / 2 = {divide(10, 2)}")
    print(f"7.5 + 2.5 = {add(7.5, 2.5)}")
    print(f"-5 * 3 = {multiply(-5, 3)}")
    try:
        print(f"5 / 0 = {divide(5, 0)}")
    except ValueError as e:
        print(f"Error: {e}")
