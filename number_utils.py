# SPDX-License-Identifier: GPL-3.0-or-later
"""Finite numeric input; supports decimal comma or decimal point."""
import math
import re

def parse_number(value):
    if value is None or isinstance(value, bool):
        raise ValueError("A numeric value is required.")
    if isinstance(value, (float, int)):
        number = float(value)
    else:
        text = str(value).strip()
        if ',' in text and '.' in text:
            decimal = ',' if text.rfind(',') > text.rfind('.') else '.'
            thousands = '.' if decimal == ',' else ','
            integer, fraction = text.rsplit(decimal, 1)
            if not re.fullmatch(r'[+-]?\d{1,3}(?:' + re.escape(thousands) + r'\d{3})+', integer) or not fraction.isdigit():
                raise ValueError("Ambiguous numeric separators: %s" % value)
            text = integer.replace(thousands, '') + '.' + fraction
        elif text.count(',') > 1 or text.count('.') > 1:
            separator = ',' if ',' in text else '.'
            if not re.fullmatch(r'[+-]?\d{1,3}(?:' + re.escape(separator) + r'\d{3})+', text):
                raise ValueError("Invalid thousands grouping: %s" % value)
            text = text.replace(separator, '')
        else:
            text = text.replace(',', '.')
        number = float(text)
    if not math.isfinite(number):
        raise ValueError("Coordinates and values must be finite.")
    return number
