# Gazitrade — Dropshipping Website

## Owner Info
- **Site Name:** Gazitrade
- **Owner:** Gazi Eman Mahmud
- **Phone:** +8801719607407
- **Email:** gazitrade2026@gmail.com
- **Location:** Dhaka, Mirpur-1

## Setup Instructions

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Apply migrations
```bash
python manage.py migrate
```
This will auto-create the SiteSettings with your info (phone, email, address, etc.)

### 3. Create superuser (admin)
```bash
python manage.py createsuperuser
```

### 4. Run the server
```bash
python manage.py runserver
```

### 5. Sync products from Droploo
- Log in as admin/staff
- Visit: `http://yoursite.com/sync/`
- This will pull all products, categories, and **size/color variants** from Droploo

## What was fixed in this version

### ✅ Branding
- All pages updated to "Gazitrade"
- Owner name: Gazi Eman Mahmud
- Phone, email, location pre-filled

### ✅ Product Variants (Size & Color)
- Droploo stores variants inside `product_images` array
- Each entry has `size`, `color`, and `price` fields
- The sync now correctly reads `product_images` and creates `ProductVariant` records
- Product detail page shows size buttons and color buttons correctly

### ✅ Category Names
- Droploo returns category as a nested object: `"category": {"id": 58, "name": "Kid's Fashion"}`
- The sync now reads `product["category"]["name"]` directly — no more "Category 58" placeholders

### ✅ Contact & Footer
- Phone, email, address, WhatsApp, social links all pull from SiteSettings
- Pre-populated via migration

## API Credentials (Test)
- App-Key: UZUOQBD6ZV6DHPQ9
- App-Secret: 51itkHeCEfLqbLo3c73grLfOCl2wvrjy
- Username: test_testcom

When your client gets their own API, just update the .env file.

## Version 2 Changes

### ✅ Contact Form Fixed
- Removed JS button-disabling that was blocking form submission
- Added explicit `action` attribute on form
- Messages now save to database correctly — view in Admin → Store → Contact Messages

### ✅ Header Updates
- Phone number removed from top bar
- "About" and "Contact" removed from header nav (still in footer)
- Logo now uses the uploaded shopping bag/cart icon image
- Brand name uses elegant serif font matching footer style

### ✅ Hero Banner — Full Background Image
- Each banner slide now uses the uploaded image as full background
- Text/button overlay stays on top with a subtle dark gradient for readability
- If no image uploaded, falls back to CSS gradient color
- Superuser sets via Admin → Store → Banners

### ✅ Categories — Sliding Carousel
- Categories now display as a modern horizontal sliding carousel
- Auto-slides every 2.8 seconds
- Arrow buttons for manual navigation
- Bigger cards with image support

### ✅ Offer Banner — Background Image Support
- The promo banner between Best Sellers and New Arrivals now supports background image
- Superuser uploads image via Admin → Store → Offer Banners

### ✅ Category Names Fixed
- After syncing products, visit /fix-categories/ (as staff) to pull real names from Droploo
- Or run: python manage.py fix_categories

## Quick Fix Steps After Deploy
1. `python manage.py migrate`
2. Log in as superuser
3. Visit `/sync-products/` to pull products
4. Visit `/fix-categories/` to fix category names
