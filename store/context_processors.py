from .models import SiteSettings


def cart_count(request):
    cart  = request.session.get('cart', {})
    count = sum(item['qty'] for item in cart.values())
    return {'cart_count': count}


def site_settings(request):
    obj = SiteSettings.objects.first()
    return {'site_settings': obj}


def wishlist_ids(request):
    """
    Provides a set of product IDs in the current user's wishlist.
    Used by the product_card partial to show the active heart
    without triggering N+1 queries.
    """
    if request.user.is_authenticated:
        from .models import Wishlist
        ids = set(
            Wishlist.objects.filter(customer=request.user)
            .values_list('product_id', flat=True)
        )
    else:
        ids = set()
    return {'wishlist_ids': ids}
