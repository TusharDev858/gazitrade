import random
import string
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Order, OrderItem
from store.droploo_api import transfer_order


def _make_invoice():
    return 'GT' + ''.join(random.choices(string.digits, k=8))


def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    subtotal = sum(
        Decimal(str(item['price'])) * int(item['qty'])
        for item in cart.values()
    )
    customer = request.user if request.user.is_authenticated else None

    if request.method == 'POST':
        delivery_type = request.POST.get('delivery_type', 'outside')
        delivery_cost = Decimal('60') if delivery_type == 'inside' else Decimal('120')
        discount      = Decimal(request.POST.get('discount', '0') or '0')
        # Always COD — other methods are coming soon
        payment_type  = 'cod'
        total         = subtotal + delivery_cost - discount

        order = Order.objects.create(
            customer         = customer,
            invoice_number   = _make_invoice(),
            customer_name    = request.POST.get('name', '').strip(),
            customer_phone   = request.POST.get('phone', '').strip(),
            customer_email   = request.POST.get('email', '').strip(),
            customer_address = request.POST.get('address', '').strip(),
            area             = request.POST.get('area', '').strip(),
            subtotal         = subtotal,
            delivery_cost    = delivery_cost,
            discount         = discount,
            delivery_type    = delivery_type,
            payment_type     = payment_type,
            payment_gateway  = '',
            transaction_id   = '',
            special_notes    = request.POST.get('notes', '').strip(),
            total            = total,
        )

        for key, item in cart.items():
            OrderItem.objects.create(
                order               = order,
                droploo_product_id  = str(item['droploo_id']),
                product_name        = item['name'],
                price               = Decimal(str(item['price'])),
                qty                 = int(item['qty']),
                color               = item.get('color', ''),
                size                = item.get('size', ''),
            )

        result = transfer_order(order)
        if result.get('order_id'):
            order.droploo_order_id = result['order_id']
            order.status           = 'transferred'
            order.save(update_fields=['droploo_order_id', 'status'])

        request.session['cart'] = {}
        return redirect('order_success', invoice=order.invoice_number)

    return render(request, 'orders/checkout.html', {
        'cart':     cart,
        'subtotal': subtotal,
        'customer': customer,
    })


def order_success(request, invoice):
    order = get_object_or_404(Order, invoice_number=invoice)
    return render(request, 'orders/order_success.html', {'order': order})


def order_detail(request, invoice):
    order = get_object_or_404(Order, invoice_number=invoice)
    if not request.user.is_authenticated:
        return redirect(f'/accounts/login/?next=/orders/detail/{invoice}/')
    if not request.user.is_staff and order.customer != request.user:
        from django.http import Http404
        raise Http404
    return render(request, 'orders/order_detail.html', {'order': order})
