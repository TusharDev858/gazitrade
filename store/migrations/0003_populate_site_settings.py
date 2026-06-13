from django.db import migrations

def populate_settings(apps, schema_editor):
    SiteSettings = apps.get_model('store', 'SiteSettings')
    if not SiteSettings.objects.exists():
        SiteSettings.objects.create(
            site_name      = 'Gazitrade',
            site_logo_text = 'GT',
            tagline        = 'Your Trusted BD Shop',
            whatsapp       = '8801719607407',
            phone          = '+8801719607407',
            email          = 'gazitrade2026@gmail.com',
            address        = 'Dhaka, Mirpur-1',
            owner_name     = 'Gazi Eman Mahmud',
            about_text     = (
                'Welcome to Gazitrade — your trusted online dropshipping store in Bangladesh.\n\n'
                'We offer a wide range of genuine products across fashion, electronics, home & lifestyle, '
                'and much more — all delivered fast to your door anywhere in Bangladesh.\n\n'
                'Our mission is simple: give every customer the best shopping experience with zero hassle. '
                'No advance payment ever. Pay only when your order arrives.'
            ),
            primary_color  = '#1a3c6e',
            accent_color   = '#e85d26',
        )

def reverse_populate(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('store', '0002_contactmessage_offerbanner_sitesettings_about_text_and_more'),
    ]
    operations = [
        migrations.RunPython(populate_settings, reverse_populate),
    ]
