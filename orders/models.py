from django.db import models

class Order(models.Model):
    STATUS = [
        ('pending','Pending'),
        ('confirmed','Confirmed'),
        ('transferred','Transferred to Droploo'),
        ('shipped','Shipped'),
        ('delivered','Delivered'),
        ('cancelled','Cancelled'),
    ]
    PAYMENT = [
        ('cod','Cash on Delivery'),
        ('bkash','bKash'),
        ('nagad','Nagad'),
        ('rocket','Rocket'),
    ]
    DELIVERY = [
        ('inside','Inside Dhaka (৳60)'),
        ('outside','Outside Dhaka (৳120)'),
    ]

    customer          = models.ForeignKey('accounts.Customer', on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='orders')
    invoice_number    = models.CharField(max_length=30, unique=True)
    droploo_order_id  = models.CharField(max_length=50, blank=True)

    customer_name     = models.CharField(max_length=100)
    customer_phone    = models.CharField(max_length=15)
    customer_email    = models.EmailField(blank=True)
    customer_address  = models.TextField()
    area              = models.CharField(max_length=100, blank=True)

    subtotal          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_cost     = models.DecimalField(max_digits=10, decimal_places=2, default=120)
    discount          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total             = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    delivery_type     = models.CharField(max_length=10, choices=DELIVERY, default='outside')
    payment_type      = models.CharField(max_length=10, choices=PAYMENT,  default='cod')
    payment_gateway   = models.CharField(max_length=20, blank=True)
    transaction_id    = models.CharField(max_length=50, blank=True)
    special_notes     = models.TextField(blank=True)
    status            = models.CharField(max_length=15, choices=STATUS, default='pending')

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number

class OrderItem(models.Model):
    order             = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product           = models.ForeignKey('store.Product', on_delete=models.SET_NULL, null=True)
    droploo_product_id = models.CharField(max_length=20)
    product_name      = models.CharField(max_length=300)
    price             = models.DecimalField(max_digits=10, decimal_places=2)
    qty               = models.PositiveIntegerField(default=1)
    color             = models.CharField(max_length=50, blank=True)
    size              = models.CharField(max_length=50, blank=True)

    @property
    def line_total(self):
        return self.price * self.qty
