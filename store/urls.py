from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.home,            name='home'),
    path('products/',           views.product_list,    name='product_list'),
    path('product/<slug:slug>/',views.product_detail,  name='product_detail'),
    path('categories/',         views.categories_view, name='categories'),
    path('search/',             views.search_view,     name='search'),
    path('track/',              views.track_order,     name='track_order'),
    # cart
    path('cart/',               views.cart_view,       name='cart'),
    path('cart/add/',           views.add_to_cart,     name='add_to_cart'),
    path('cart/update/',        views.update_cart,     name='update_cart'),
    path('cart/remove/',        views.remove_from_cart,name='remove_from_cart'),
    # wishlist
    path('wishlist/',           views.wishlist_view,   name='wishlist'),
    path('wishlist/toggle/',    views.toggle_wishlist, name='toggle_wishlist'),
    # admin util
    path('clear-resync/',         views.clear_and_resync, name='clear_resync'),
    path('fix-categories/',       views.fix_categories,  name='fix_categories'),
    path('sync-products/',      views.sync_products,   name='sync_products'),
    path('api-test/',           views.api_test,        name='api_test'),
    path('api-test-cats/',      views.api_test_cats,   name='api_test_cats'),
    path('about/',              views.about_view,      name='about'),
    path('contact/',            views.contact_view,    name='contact'),
]
