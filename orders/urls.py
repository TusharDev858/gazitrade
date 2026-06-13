from django.urls import path
from . import views

urlpatterns = [
    path('checkout/',                    views.checkout_view,  name='checkout'),
    path('success/<str:invoice>/',       views.order_success,  name='order_success'),
    path('detail/<str:invoice>/',        views.order_detail,   name='order_detail'),
]
