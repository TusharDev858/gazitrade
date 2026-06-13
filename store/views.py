import json
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils.text import slugify

from .models import Product, Category, Banner, OfferBanner, Wishlist, ProductImage, ProductVariant, SiteSettings
from .droploo_api import get_all_products, get_product_detail, get_categories, _get


# ── helpers ──────────────────────────────────────────────────────────

def _unique_slug(name, qs):
    base = slugify(name)[:300]
    slug, n = base, 1
    while qs.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def _unique_cat_slug(name):
    base = slugify(name)[:90]
    if not base:
        base = 'category'
    slug, n = base, 1
    while Category.objects.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


# ── public pages ─────────────────────────────────────────────────────

def home(request):
    banners      = Banner.objects.filter(is_active=True)
    categories   = Category.objects.filter(is_active=True)
    best_sellers = Product.objects.filter(is_active=True, is_featured=True).order_by('-priority')[:12]
    if not best_sellers.exists():
        best_sellers = Product.objects.filter(is_active=True).order_by('-priority')[:12]
    new_arrivals  = Product.objects.filter(is_active=True).order_by('-created_at')[:12]
    offer_banners = OfferBanner.objects.filter(is_active=True)
    all_products  = Product.objects.filter(is_active=True).order_by('-created_at')[:40]
    return render(request, 'store/home.html', {
        'banners':       banners,
        'offer_banners': offer_banners,
        'categories':    categories,
        'best_sellers':  best_sellers,
        'new_arrivals':  new_arrivals,
        'all_products':  all_products,
    })


def product_list(request):
    category_slug     = request.GET.get('category', '')
    sort              = request.GET.get('sort', '')
    query             = request.GET.get('q', '')
    selected_category = None

    products = Product.objects.filter(is_active=True)

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=selected_category)

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if   sort == 'price_asc':  products = products.order_by('price')
    elif sort == 'price_desc': products = products.order_by('-price')
    elif sort == 'newest':     products = products.order_by('-created_at')
    else:                      products = products.order_by('-priority', '-created_at')

    return render(request, 'store/product_list.html', {
        'products':          products,
        'categories':        Category.objects.filter(is_active=True),
        'selected_category': selected_category,
        'query':             query,
        'sort':              sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:6]
    in_wishlist = (
        request.user.is_authenticated
        and Wishlist.objects.filter(customer=request.user, product=product).exists()
    )
    return render(request, 'store/product_detail.html', {
        'product':     product,
        'related':     related,
        'in_wishlist': in_wishlist,
    })


def categories_view(request):
    cats = Category.objects.filter(is_active=True).prefetch_related('products')
    return render(request, 'store/categories.html', {'categories': cats})


def search_view(request):
    query    = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        products = products.none()
    return render(request, 'store/search.html', {'products': products, 'query': query})


def track_order(request):
    order = None
    PROGRESS_STEPS = [
        ('Pending',    'pending'),
        ('Confirmed',  'confirmed'),
        ('Dispatched', 'transferred'),
        ('Shipped',    'shipped'),
        ('Delivered',  'delivered'),
    ]
    if request.method == 'POST':
        from orders.models import Order
        invoice = request.POST.get('invoice', '').strip().upper()
        try:
            order = Order.objects.prefetch_related('items').get(invoice_number=invoice)
        except Order.DoesNotExist:
            messages.error(request, f'No order found with invoice "{invoice}". Please check and try again.')
    return render(request, 'store/track_order.html', {
        'order':          order,
        'progress_steps': PROGRESS_STEPS,
    })


# ── cart ──────────────────────────────────────────────────────────────

def cart_view(request):
    cart  = request.session.get('cart', {})
    items = []
    total = Decimal('0')
    for key, item in cart.items():
        sub = Decimal(str(item['price'])) * int(item['qty'])
        total += sub
        items.append({**item, 'key': key, 'subtotal': sub})
    return render(request, 'store/cart.html', {'cart_items': items, 'total': total})


def add_to_cart(request):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    try:
        data    = json.loads(request.body)
        pid     = str(data.get('product_id'))
        qty     = max(1, int(data.get('qty', 1)))
        size    = data.get('size', '')
        color   = data.get('color', '')
        product = get_object_or_404(Product, pk=pid, is_active=True)
        cart    = request.session.get('cart', {})
        key     = f"{pid}_{size}_{color}"
        if key in cart:
            cart[key]['qty'] += qty
        else:
            img_url = product.main_image.image_url if product.main_image else ''
            cart[key] = {
                'product_id': pid,
                'name':       product.name,
                'price':      str(product.sale_price),
                'qty':        qty,
                'size':       size,
                'color':      color,
                'image':      img_url,
                'droploo_id': product.b_product_id,
            }
        request.session['cart'] = cart
        count = sum(i['qty'] for i in cart.values())
        return JsonResponse({'success': True, 'cart_count': count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def update_cart(request):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    data = json.loads(request.body)
    key  = data.get('key')
    qty  = int(data.get('qty', 1))
    cart = request.session.get('cart', {})
    if key in cart:
        if qty > 0:
            cart[key]['qty'] = qty
        else:
            del cart[key]
    request.session['cart'] = cart
    return JsonResponse({'success': True})


def remove_from_cart(request):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    data  = json.loads(request.body)
    key   = data.get('key')
    cart  = request.session.get('cart', {})
    cart.pop(key, None)
    request.session['cart'] = cart
    count = sum(i['qty'] for i in cart.values())
    return JsonResponse({'success': True, 'cart_count': count})


# ── wishlist ──────────────────────────────────────────────────────────

@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(
        customer=request.user
    ).select_related('product').prefetch_related('product__images')
    return render(request, 'store/wishlist.html', {'wishlist_items': items})


@login_required
def toggle_wishlist(request):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    data    = json.loads(request.body)
    product = get_object_or_404(Product, pk=data.get('product_id'))
    obj, created = Wishlist.objects.get_or_create(customer=request.user, product=product)
    if not created:
        obj.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})


# ── admin: sync products + categories from Droploo ───────────────────

@login_required
def sync_products(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)

    # ── Step 0: Pre-fetch categories to build name lookup map ────────
    cat_lookup = {}  # {droploo_id: {"name": ..., "slug": ...}}
    cat_data, cat_err = _get("/categories")
    if not cat_err and cat_data:
        raw_cats = cat_data.get('categories', cat_data) if isinstance(cat_data, dict) else cat_data
        if isinstance(raw_cats, list):
            for c in raw_cats:
                cid   = c.get('id') or c.get('cat_id')
                cname = (c.get('name') or c.get('category_name') or c.get('title') or '').strip()
                if cid and cname:
                    cat_lookup[int(cid)] = cname

    # ── Step 1: Fetch all products ────────────────────────────────────
    data, err = _get("/products")
    if err:
        return JsonResponse({
            'error': f'Droploo API error: {err}',
            'tip':   'Ask the Droploo developer to whitelist your server IP.',
        }, status=502)

    products_list = data.get('products', [])
    image_base    = data.get('imagePath', 'https://backend.droploo.com/product/images/')
    gallery_base  = 'https://backend.droploo.com/galleryImage/'

    added = skipped = price_zero = variants_added = 0

    for p in products_list:
        pid = p.get('id')
        if not pid:
            continue

        # Skip duplicates
        if Product.objects.filter(b_product_id=pid).exists():
            skipped += 1
            continue

        # ── Name ──────────────────────────────────────────────────────
        name = (p.get('name') or p.get('product_name') or
                p.get('title') or p.get('product_title') or
                f"Product {pid}")
        name = str(name).strip() or f"Product {pid}"

        # ── Slug ──────────────────────────────────────────────────────
        slug = _unique_slug(name, Product.objects)
        if not slug:
            slug = f"product-{pid}"

        # ── Price — Droploo uses regular_price ────────────────────────
        raw_price = (
            p.get('regular_price') or
            p.get('sell_price') or
            p.get('selling_price') or
            p.get('price') or
            p.get('sale_price') or
            p.get('amount') or
            0
        )
        try:
            price = Decimal(str(raw_price)).quantize(Decimal('0.01'))
        except Exception:
            price = Decimal('0.00')

        if price == 0:
            price_zero += 1

        # ── Discount price ────────────────────────────────────────────
        raw_disc = p.get('discount_price')
        discount_price = None
        if raw_disc:
            try:
                discount_price = Decimal(str(raw_disc)).quantize(Decimal('0.01'))
            except Exception:
                discount_price = None

        # ── is_variable ───────────────────────────────────────────────
        is_variable = bool(p.get('is_variable', 0))

        # ── Create product ────────────────────────────────────────────
        product = Product.objects.create(
            b_product_id   = pid,
            name           = name,
            slug           = slug,
            price          = price,
            discount_price = discount_price,
            is_variable    = is_variable,
            stock          = int(p.get('qty') or p.get('stock') or p.get('quantity') or 0),
            description    = (p.get('long_description') or p.get('short_description') or
                              p.get('description') or p.get('details') or ''),
        )

        # ── Category — use pre-fetched lookup map first, then nested object ──
        cat_obj  = p.get('category') or {}
        cat_id   = cat_obj.get('id') or p.get('cat_id') or p.get('category_id')

        if cat_id:
            try:
                cat_id_int = int(cat_id)
            except (ValueError, TypeError):
                cat_id_int = None

            if cat_id_int:
                # Priority: pre-fetched /categories API > nested object name > slug fallback
                real_name = (
                    cat_lookup.get(cat_id_int) or
                    (cat_obj.get('name') or '').strip() or
                    (cat_obj.get('slug') or '').replace('-', ' ').title() or
                    f'Category {cat_id_int}'
                )

                base_slug  = slugify(real_name)[:90] or f'category-{cat_id_int}'
                final_slug, n = base_slug, 1
                while Category.objects.filter(slug=final_slug).exclude(droploo_id=cat_id_int).exists():
                    final_slug = f"{base_slug}-{n}"
                    n += 1

                cat, created = Category.objects.get_or_create(
                    droploo_id=cat_id_int,
                    defaults={'name': real_name, 'slug': final_slug, 'is_active': True}
                )
                # Always update name if we now have a better one
                if not created and (cat.name.startswith('Category ') or cat.name != real_name):
                    if real_name and not real_name.startswith('Category '):
                        cat.name = real_name
                        cat.save(update_fields=['name'])

                product.category = cat
                product.save(update_fields=['category'])

        # ── Main product image ────────────────────────────────────────
        img_name = (
            p.get('image') or p.get('thumbnail') or p.get('img') or
            p.get('photo') or p.get('featured_image') or
            p.get('product_image') or p.get('cover_image')
        )
        # Also check imageUrl directly
        img_url_direct = p.get('imageUrl') or p.get('image_url') or ''

        if img_url_direct and img_url_direct.startswith('http'):
            ProductImage.objects.create(
                product=product, image_url=img_url_direct, is_primary=True, order=0
            )
        elif img_name:
            img_url = img_name if img_name.startswith('http') else f"{image_base}{img_name}"
            ProductImage.objects.create(
                product=product, image_url=img_url, is_primary=True, order=0
            )

        # ── Variants from product_images array ────────────────────────
        # Droploo stores variants inside product_images with size, color, price per variant
        # Each entry: {"id":3317, "price":590, "color":null, "size":"Age 1/2",
        #              "gallery_image":"...", "imageUrl":"..."}
        product_images_list = p.get('product_images', [])

        # Track sizes/colors already seen to avoid duplicate variant records
        seen_variants = set()

        for idx, pi in enumerate(product_images_list):
            pi_size  = (pi.get('size')  or '').strip()
            pi_color = (pi.get('color') or '').strip()
            pi_price = pi.get('price') or pi.get('sell_price') or None

            # Gallery image URL for this variant
            pi_img_url = pi.get('imageUrl') or pi.get('image_url') or ''
            if not pi_img_url:
                gi = pi.get('gallery_image', '')
                if gi:
                    pi_img_url = gi if gi.startswith('http') else f"{gallery_base}{gi}"

            # Save variant gallery image (skip if already added as primary)
            if pi_img_url and idx > 0:
                ProductImage.objects.get_or_create(
                    product=product, image_url=pi_img_url,
                    defaults={'is_primary': False, 'order': idx}
                )
            elif pi_img_url and idx == 0 and not (img_url_direct or img_name):
                # No main image was set — use first product_image as primary
                ProductImage.objects.create(
                    product=product, image_url=pi_img_url, is_primary=True, order=0
                )

            # Create variant record if size or color exists
            if pi_size or pi_color:
                vkey = (pi_size, pi_color)
                if vkey not in seen_variants:
                    seen_variants.add(vkey)
                    v_price = None
                    if pi_price:
                        try:
                            v_price = Decimal(str(pi_price)).quantize(Decimal('0.01'))
                        except Exception:
                            v_price = None
                    ProductVariant.objects.create(
                        product=product,
                        size=pi_size,
                        color=pi_color,
                        price=v_price,
                        stock=100,  # Droploo doesn't provide per-variant stock; default to 100
                    )
                    variants_added += 1

        # ── Fallback: standalone colors/sizes arrays (if product_images empty) ──
        if not product_images_list:
            for c in p.get('colors', []):
                cname = c.get('name') or c.get('color') or str(c)
                if cname:
                    ProductVariant.objects.get_or_create(
                        product=product, size='', color=cname,
                        defaults={'stock': 100}
                    )
                    variants_added += 1
            for s in p.get('sizes', []):
                sname = s.get('name') or s.get('size') or str(s)
                if sname:
                    ProductVariant.objects.get_or_create(
                        product=product, size=sname, color='',
                        defaults={'stock': 100}
                    )
                    variants_added += 1

        added += 1

    categories_count = Category.objects.count()
    return JsonResponse({
        'success':          True,
        'added':            added,
        'skipped':          skipped,
        'total':            len(products_list),
        'variants_added':   variants_added,
        'categories':       categories_count,
        'price_zero_count': price_zero,
        'image_base':       image_base,
        'note': (f'{price_zero} products have price=0 — check /api-test/ for real field names'
                 if price_zero else 'All prices OK'),
    })


# ── debug: raw API test ───────────────────────────────────────────────

@login_required
def api_test(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)

    import requests as req
    from django.conf import settings as s

    url  = f"{s.DROPLOO_BASE_URL}/products"
    hdrs = {
        "App-Key":      s.DROPLOO_APP_KEY,
        "App-Secret":   s.DROPLOO_APP_SECRET,
        "Username":     s.DROPLOO_USERNAME,
        "Accept":       "application/json",
        "Content-Type": "application/json",
        "User-Agent":   "Mozilla/5.0 (compatible; Gazitrade/1.0)",
    }
    result = {}
    try:
        r = req.get(url, headers=hdrs, timeout=15)
        result = {
            'url':           url,
            'status_code':   r.status_code,
            'headers_sent':  {k: v for k, v in hdrs.items() if k != 'App-Secret'},
            'response_text': r.text[:2000],
        }
        if r.status_code == 200:
            d = r.json()
            prods = d.get('products', [])
            result['product_count']      = len(prods)
            result['image_path']         = d.get('imagePath', '')
            result['top_level_keys']     = list(d.keys())
            if prods:
                result['sample_products'] = prods[:3]
                result['all_field_names'] = sorted(set(
                    k for p in prods[:20] for k in p.keys()
                ))
    except Exception as e:
        result = {'error': str(e), 'url': url}

    return JsonResponse(result, json_dumps_params={'indent': 2})


@login_required
def api_test_cats(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)

    import requests as req
    from django.conf import settings as s

    hdrs = {
        "App-Key":      s.DROPLOO_APP_KEY,
        "App-Secret":   s.DROPLOO_APP_SECRET,
        "Username":     s.DROPLOO_USERNAME,
        "Accept":       "application/json",
        "Content-Type": "application/json",
        "User-Agent":   "Mozilla/5.0 (compatible; Gazitrade/1.0)",
    }
    result = {}

    try:
        r = req.get(f"{s.DROPLOO_BASE_URL}/categories", headers=hdrs, timeout=15)
        result['categories_status'] = r.status_code
        if r.status_code == 200:
            d = r.json()
            result['categories_keys']   = list(d.keys())
            result['categories_sample'] = d.get('categories', d)[:5] if isinstance(d.get('categories', d), list) else d
        else:
            result['categories_error'] = r.text[:300]
    except Exception as e:
        result['categories_exception'] = str(e)

    from store.models import Product
    p = Product.objects.first()
    if p:
        try:
            r2 = req.get(f"{s.DROPLOO_BASE_URL}/product/{p.b_product_id}", headers=hdrs, timeout=15)
            result['product_detail_status'] = r2.status_code
            if r2.status_code == 200:
                result['product_detail'] = r2.json()
            else:
                result['product_detail_error'] = r2.text[:300]
        except Exception as e:
            result['product_detail_exception'] = str(e)

    return JsonResponse(result, json_dumps_params={'indent': 2})


# ── About page ────────────────────────────────────────────────────────

def about_view(request):
    return render(request, 'store/about.html')


# ── Contact page ──────────────────────────────────────────────────────

def contact_view(request):
    from .models import ContactMessage
    submitted = False
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        msg     = request.POST.get('message', '').strip()
        if name and msg:
            ContactMessage.objects.create(
                name=name, email=email, phone=phone,
                subject=subject, message=msg
            )
            submitted = True
        else:
            messages.error(request, 'Please enter your name and message.')
    return render(request, 'store/contact.html', {'submitted': submitted})


# ── admin: fix category names ─────────────────────────────────────────
@login_required
def fix_categories(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)

    from django.utils.text import slugify as dj_slugify
    updated = created = 0
    cat_list = []

    # Strategy 1: try /categories endpoint
    data, err = _get('/categories')
    if not err and data:
        raw = data.get('categories', data) if isinstance(data, dict) else data
        if isinstance(raw, list):
            cat_list = raw

    # Strategy 2: if /categories failed or returned nothing,
    # fetch category data from individual product detail endpoints
    if not cat_list:
        products_with_placeholder = Product.objects.filter(
            category__name__startswith='Category '
        ).select_related('category').distinct()[:30]

        seen_pids = set()
        for prod in products_with_placeholder:
            if prod.b_product_id and prod.b_product_id not in seen_pids:
                seen_pids.add(prod.b_product_id)
                pdata, perr = _get(f'/product/{prod.b_product_id}')
                if not perr and pdata:
                    p = pdata.get('product', pdata)
                    cat_obj = p.get('category') or {}
                    cid   = cat_obj.get('id') or p.get('cat_id')
                    cname = (cat_obj.get('name') or '').strip()
                    if cid and cname:
                        cat_list.append({'id': cid, 'name': cname})

    if not cat_list:
        return JsonResponse({
            'success': False,
            'error': 'Could not fetch category names from API. Make sure your server IP is whitelisted by Droploo.',
            'tip': 'Delete all products and re-sync — the sync will read category names from the products API response.',
        })

    # Apply names from cat_list
    for c in cat_list:
        cid   = c.get('id') or c.get('cat_id')
        cname = (c.get('name') or c.get('category_name') or c.get('title') or '').strip()
        if not cid or not cname:
            continue
        try:
            cat_id_int = int(cid)
        except (ValueError, TypeError):
            continue
        try:
            cat = Category.objects.get(droploo_id=cat_id_int)
            changed = False
            if cat.name != cname:
                cat.name = cname
                changed = True
            new_slug = dj_slugify(cname)[:90] or f'category-{cid}'
            if cat.slug != new_slug and not Category.objects.filter(slug=new_slug).exclude(pk=cat.pk).exists():
                cat.slug = new_slug
                changed = True
            if changed:
                cat.save()
                updated += 1
        except Category.DoesNotExist:
            slug = dj_slugify(cname)[:90] or f'category-{cid}'
            n, base = 1, slug
            while Category.objects.filter(slug=slug).exists():
                slug = f'{base}-{n}'; n += 1
            Category.objects.create(droploo_id=cat_id_int, name=cname, slug=slug, is_active=True)
            created += 1

    return JsonResponse({
        'success':          True,
        'updated':          updated,
        'created':          created,
        'total_categories': Category.objects.count(),
        'all_category_names': list(Category.objects.values_list('name', flat=True)),
    })


# ── admin: clear products & re-sync fresh from Droploo ───────────────
@login_required  
def clear_and_resync(request):
    """Delete all products/categories and re-sync fresh. This fixes category names."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)
    
    # Delete existing data
    from orders.models import Order
    Product.objects.all().delete()
    Category.objects.all().delete()
    
    # Now re-sync (category names will be correct this time)
    return sync_products(request)
