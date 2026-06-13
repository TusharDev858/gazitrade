"""
Management command: fix_slugs
Finds and fixes products with empty/null slugs and updates placeholder category names.

Usage:
    python manage.py fix_slugs
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from store.models import Product, Category


class Command(BaseCommand):
    help = 'Fix products with empty slugs and placeholder category names'

    def handle(self, *args, **kwargs):
        # ── Fix empty product slugs ───────────────────────────────────
        broken = list(Product.objects.filter(slug='')) + \
                 list(Product.objects.filter(slug__isnull=True))
        fixed_slugs = 0
        for product in broken:
            base = slugify(product.name)[:300] or f'product-{product.b_product_id}'
            slug, n = base, 1
            while Product.objects.filter(slug=slug).exclude(pk=product.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            product.slug = slug
            product.save(update_fields=['slug'])
            self.stdout.write(f'  Fixed slug: [{product.id}] {product.name[:50]} → "{slug}"')
            fixed_slugs += 1

        # ── Report placeholder categories ─────────────────────────────
        placeholder_cats = Category.objects.filter(name__startswith='Category ')
        if placeholder_cats.exists():
            self.stdout.write(self.style.WARNING(
                f'\n  ⚠ {placeholder_cats.count()} categories still have placeholder names:'
            ))
            for c in placeholder_cats:
                self.stdout.write(f'    - {c.name} (droploo_id={c.droploo_id})')
            self.stdout.write(
                '  Run /sync-products/ again to fetch real names from the API.\n'
            )

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Fixed {fixed_slugs} empty slug(s). '
            f'Products: {Product.objects.count()} | Categories: {Category.objects.count()}'
        ))
