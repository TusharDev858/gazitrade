from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model           = OrderItem
    extra           = 0
    readonly_fields = ['droploo_product_id', 'product_name', 'price', 'qty', 'color', 'size']
    fields          = ['product_name', 'droploo_product_id', 'price', 'qty', 'size', 'color']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = [
        'invoice_number', 'customer_name', 'customer_phone',
        'colored_status', 'payment_type', 'total', 'created_at',
    ]
    list_filter     = ['status', 'payment_type', 'delivery_type', 'created_at']
    search_fields   = ['invoice_number', 'customer_name', 'customer_phone', 'droploo_order_id']
    readonly_fields = ['invoice_number', 'droploo_order_id', 'created_at', 'updated_at']
    ordering        = ['-created_at']
    inlines         = [OrderItemInline]

    fieldsets = (
        ('Order Info',  {'fields': ('invoice_number', 'droploo_order_id', 'status', 'customer')}),
        ('Customer',    {'fields': ('customer_name', 'customer_phone', 'customer_email', 'customer_address', 'area')}),
        ('Pricing',     {'fields': ('subtotal', 'delivery_cost', 'discount', 'advance', 'total')}),
        ('Delivery',    {'fields': ('delivery_type',)}),
        ('Payment',     {'fields': ('payment_type', 'payment_gateway', 'transaction_id')}),
        ('Notes',       {'fields': ('special_notes',)}),
        ('Timestamps',  {'fields': ('created_at', 'updated_at')}),
    )

    def colored_status(self, obj):
        COLORS = {
            'pending':     '#f59e0b',
            'confirmed':   '#3b82f6',
            'transferred': '#8b5cf6',
            'shipped':     '#0ea5e9',
            'delivered':   '#22c55e',
            'cancelled':   '#ef4444',
        }
        color = COLORS.get(obj.status, '#6b7280')
        return format_html(
            '<b style="color:{}">{}</b>', color, obj.get_status_display()
        )
    colored_status.short_description = 'Status'
    colored_status.admin_order_field = 'status'
