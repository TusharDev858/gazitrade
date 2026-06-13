from django.contrib import admin
from .models import SiteSettings, Banner, Category, Product, ProductImage, ProductVariant, Wishlist


class ProductImageInline(admin.TabularInline):
    model  = ProductImage
    extra  = 1
    fields = ['image_url','is_primary','order']


class ProductVariantInline(admin.TabularInline):
    model  = ProductVariant
    extra  = 1
    fields = ['size','color','price','stock']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Branding',     {'fields': ('site_name','site_logo','site_logo_text','tagline')}),
        ('Contact',      {'fields': ('phone','whatsapp','email','address')}),
        ('Social Links', {'fields': ('facebook','instagram','youtube')}),
        ('Theme',        {'fields': ('primary_color','accent_color')}),
        ('About',        {'fields': ('owner_name','about_text')}),
    )
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display  = ['title','order','is_active']
    list_editable = ['order','is_active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display   = ['name','slug','order','is_active']
    list_editable  = ['order','is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display   = ['name','category','price','discount_price','stock',
                      'badge','is_featured','priority','is_active']
    list_editable  = ['price','discount_price','stock','badge','is_featured','priority','is_active']
    list_filter    = ['category','badge','is_featured','is_active']
    search_fields  = ['name','b_product_id']
    prepopulated_fields = {'slug': ('name',)}
    inlines        = [ProductImageInline, ProductVariantInline]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['customer','product','added_at']
    list_filter  = ['added_at']

from .models import OfferBanner, ContactMessage

@admin.register(OfferBanner)
class OfferBannerAdmin(admin.ModelAdmin):
    list_display  = ['title', 'badge_text', 'order', 'is_active']
    list_editable = ['order', 'is_active']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ['name', 'phone', 'email', 'subject', 'is_read', 'created_at']
    list_editable = ['is_read']
    list_filter   = ['is_read', 'created_at']
    readonly_fields = ['name','email','phone','subject','message','created_at']
