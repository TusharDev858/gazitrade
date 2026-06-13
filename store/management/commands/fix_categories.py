"""
Management command to fix category names from Droploo API.
Run: python manage.py fix_categories
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from store.models import Category
from store.droploo_api import _get


class Command(BaseCommand):
    help = 'Fix category names from Droploo /api/categories endpoint'

    def handle(self, *args, **options):
        data, err = _get('/categories')
        if err:
            self.stdout.write(self.style.ERROR(f'API error: {err}'))
            return

        # Handle both {categories:[...]} and direct list
        cat_list = data.get('categories', data) if isinstance(data, dict) else data
        if not isinstance(cat_list, list):
            self.stdout.write(self.style.ERROR('Unexpected API response format'))
            return

        updated = 0
        for c in cat_list:
            cid   = c.get('id') or c.get('cat_id')
            cname = (c.get('name') or c.get('category_name') or c.get('title') or '').strip()
            cimg  = c.get('imageUrl') or c.get('image_url') or ''

            if not cid or not cname:
                continue

            try:
                cat = Category.objects.get(droploo_id=int(cid))
                changed = False
                if cat.name != cname:
                    cat.name = cname
                    changed = True
                # Fix slug if it's still the placeholder form
                expected_slug = slugify(cname)[:90]
                if cat.slug.startswith('category-') or cat.slug != expected_slug:
                    # Only update slug if no conflict
                    if not Category.objects.filter(slug=expected_slug).exclude(pk=cat.pk).exists():
                        cat.slug = expected_slug
                        changed = True
                if changed:
                    cat.save()
                    updated += 1
                    self.stdout.write(f'  Updated: {cid} → {cname}')
            except Category.DoesNotExist:
                # Create if doesn't exist
                slug = slugify(cname)[:90] or f'category-{cid}'
                n = 1
                base = slug
                while Category.objects.filter(slug=slug).exists():
                    slug = f'{base}-{n}'; n += 1
                Category.objects.create(
                    droploo_id=int(cid), name=cname, slug=slug, is_active=True
                )
                updated += 1
                self.stdout.write(f'  Created: {cid} → {cname}')

        self.stdout.write(self.style.SUCCESS(f'Done. {updated} categories updated/created.'))
