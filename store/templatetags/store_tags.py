from django import template
from decimal import Decimal, ROUND_HALF_UP

register = template.Library()


@register.filter
def multiply(value, arg):
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except Exception:
        return 0


@register.filter
def currency(value):
    try:
        return f"৳{Decimal(str(value)):,.2f}"
    except Exception:
        return value


@register.filter
def cart_subtotal(cart):
    """Sum all items in the session cart dict."""
    try:
        return sum(Decimal(str(i['price'])) * i['qty'] for i in cart.values())
    except Exception:
        return 0


@register.filter
def split(value, delimiter=','):
    """Split a string into a list — e.g. {{ 'a,b,c'|split:',' }}"""
    try:
        return value.split(delimiter)
    except Exception:
        return []


@register.filter
def savings_percent(discount_price, original_price):
    """
    Returns how much percent is saved.
    Usage: {{ product.discount_price|savings_percent:product.price }}
    e.g. discount=800, original=1000 → 20
    """
    try:
        d = Decimal(str(discount_price))
        o = Decimal(str(original_price))
        if o == 0:
            return 0
        saved = ((o - d) / o * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return int(saved)
    except Exception:
        return 0
