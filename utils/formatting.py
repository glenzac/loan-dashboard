"""
Formatting utilities for displaying numbers in Indian format (Lakhs and Crores)
"""

def format_indian_currency(number, show_decimals=True):
    """
    Format a number in Indian numbering system with commas.

    Examples:
        7291935 -> ₹72,91,935.00
        25527200 -> ₹2,55,27,200.00
        1234567890 -> ₹1,23,45,67,890.00

    Args:
        number: The number to format (int or float)
        show_decimals: Whether to show decimal places (default: True)

    Returns:
        Formatted string with Indian number formatting
    """
    if number is None:
        return "₹0"

    # Convert to float for consistency
    number = float(number)

    # Handle negative numbers
    is_negative = number < 0
    number = abs(number)

    # Split into integer and decimal parts
    if show_decimals:
        integer_part = int(number)
        decimal_part = number - integer_part
        decimal_str = f".{int(decimal_part * 100):02d}"
    else:
        integer_part = int(round(number))
        decimal_str = ""

    # Convert integer part to string
    num_str = str(integer_part)

    # Apply Indian formatting
    if len(num_str) <= 3:
        # Numbers up to 999
        formatted = num_str
    else:
        # Last 3 digits
        formatted = num_str[-3:]
        remaining = num_str[:-3]

        # Add commas every 2 digits for the remaining part
        while remaining:
            if len(remaining) <= 2:
                formatted = remaining + ',' + formatted
                remaining = ''
            else:
                formatted = remaining[-2:] + ',' + formatted
                remaining = remaining[:-2]

    # Add decimal part
    formatted += decimal_str

    # Add negative sign if needed
    if is_negative:
        formatted = '-' + formatted

    # Add currency symbol
    formatted = '₹' + formatted

    return formatted


def format_indian_number_short(number):
    """
    Format large numbers in Lakhs/Crores notation for compact display.

    Examples:
        150000 -> ₹1.5L
        7291935 -> ₹72.9L
        25527200 -> ₹2.55Cr
        125000000 -> ₹12.5Cr

    Args:
        number: The number to format

    Returns:
        Formatted string with L (Lakhs) or Cr (Crores) suffix
    """
    if number is None:
        return "₹0"

    number = float(number)
    is_negative = number < 0
    number = abs(number)

    if number >= 10000000:  # 1 Crore or more
        value = number / 10000000
        suffix = "Cr"
    elif number >= 100000:  # 1 Lakh or more
        value = number / 100000
        suffix = "L"
    elif number >= 1000:  # 1 Thousand or more
        value = number / 1000
        suffix = "K"
    else:
        return format_indian_currency(number, show_decimals=False)

    # Format with appropriate decimal places
    if value >= 100:
        formatted = f"{value:.1f}"
    elif value >= 10:
        formatted = f"{value:.1f}"
    else:
        formatted = f"{value:.2f}"

    # Remove unnecessary trailing zeros
    formatted = formatted.rstrip('0').rstrip('.')

    result = f"₹{formatted}{suffix}"

    if is_negative:
        result = '-' + result

    return result
