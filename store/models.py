from django.db import models

class SiteSettings(models.Model):
    site_name      = models.CharField(max_length=100, default='Gazitrade')
    site_logo      = models.ImageField(upload_to='site/', blank=True, null=True)
    site_logo_text = models.CharField(max_length=5, default='HS')
    tagline        = models.CharField(max_length=200, default='Your Trusted BD Shop')
    whatsapp       = models.CharField(max_length=20, blank=True)
    phone          = models.CharField(max_length=20, blank=True)
    email          = models.EmailField(blank=True)
    address        = models.TextField(blank=True)
    facebook       = models.URLField(blank=True)
    instagram      = models.URLField(blank=True)
    youtube        = models.URLField(blank=True)
    owner_name     = models.CharField(max_length=100, blank=True, default='Gazi Eman Mahmud')
    about_text     = models.TextField(blank=True, default='Welcome to Gazitrade — your trusted online dropshipping store. We offer genuine products across fashion, electronics, home & lifestyle, and more, delivered fast anywhere in Bangladesh. No advance payment. Cash on delivery always.')
    primary_color  = models.CharField(max_length=20, default='#1a3c6e')
    accent_color   = models.CharField(max_length=20, default='#e85d26')

    class Meta:
        verbose_name = verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

class Banner(models.Model):
    title       = models.CharField(max_length=200)
    subtitle    = models.CharField(max_length=300, blank=True)
    image       = models.ImageField(upload_to='banners/', blank=True, null=True)
    btn_text    = models.CharField(max_length=50, default='Shop Now')
    btn_link    = models.CharField(max_length=200, default='/products/')
    bg_color    = models.CharField(max_length=50, default='linear-gradient(135deg,#1a3c6e,#2563eb)')
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class Category(models.Model):
    name       = models.CharField(max_length=100)
    slug       = models.SlugField(unique=True)
    image      = models.ImageField(upload_to='categories/', blank=True, null=True)
    droploo_id = models.IntegerField(blank=True, null=True)
    order      = models.PositiveIntegerField(default=0)
    is_active  = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order','name']

    def __str__(self):
        return self.name

class Product(models.Model):
    BADGE_CHOICES = [('','None'),('HOT','HOT'),('DISCOUNT','DISCOUNT'),('NEW','NEW')]

    b_product_id   = models.IntegerField(unique=True)
    name           = models.CharField(max_length=300)
    slug           = models.SlugField(unique=True, max_length=350)
    category       = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='products')
    price          = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description    = models.TextField(blank=True)
    is_variable    = models.BooleanField(default=False)
    stock          = models.IntegerField(default=0)
    badge          = models.CharField(max_length=10, choices=BADGE_CHOICES, blank=True, default='')
    is_featured    = models.BooleanField(default=False)
    priority       = models.PositiveIntegerField(default=0)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority','-created_at']

    def __str__(self):
        return self.name

    @property
    def sale_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def main_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url  = models.URLField(max_length=500)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size    = models.CharField(max_length=50, blank=True)
    color   = models.CharField(max_length=50, blank=True)
    price   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock   = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} | {self.size} {self.color}".strip()

class Wishlist(models.Model):
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='wishlist')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer','product')

class OfferBanner(models.Model):
    """Editable offer/promo slider between Best Sellers and New Arrivals."""
    title       = models.CharField(max_length=200)
    subtitle    = models.CharField(max_length=300, blank=True)
    badge_text  = models.CharField(max_length=50, blank=True, help_text="e.g. SPECIAL OFFER, FLASH SALE")
    image       = models.ImageField(upload_to='offers/', blank=True, null=True)
    btn_text    = models.CharField(max_length=50, default='Shop Now')
    btn_link    = models.CharField(max_length=200, default='/products/')
    bg_color    = models.CharField(max_length=100, default='linear-gradient(135deg,#f97316,#ef4444)')
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    """Customer contact form submissions."""
    name       = models.CharField(max_length=100)
    email      = models.EmailField(blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    subject    = models.CharField(max_length=200, blank=True)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.subject or self.message[:40]}"
