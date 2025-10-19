# Core Application

The **core** application serves as the base/foundation layer for the Django/Wagtail project. It contains reusable components, base models, settings, and templates that can be used across other applications.

## Purpose

- Provide reusable StreamField blocks for consistent content creation
- Store global site settings accessible throughout the project
- Define base abstract models for common functionality (SEO, etc.)
- Offer base templates (header, footer, SEO meta tags) for consistent UI
- Centralize common utilities and helpers

## Structure

```
core/
├── models.py              # Base models, blocks, and site settings
├── apps.py                # App configuration
├── admin.py               # Admin customizations
├── views.py               # Base views (error pages, utilities)
├── tests.py               # Test cases
├── migrations/            # Database migrations
└── templates/
    └── core/
        ├── base.html      # Base layout template
        ├── blocks/        # StreamField block templates
        │   ├── heading_block.html
        │   ├── rich_text_block.html
        │   ├── image_block.html
        │   ├── button_block.html
        │   ├── spacer_block.html
        │   ├── hero_block.html
        │   ├── cta_block.html
        │   ├── author_bio_block.html
        │   ├── recent_posts_block.html
        │   └── quote_block.html
        └── includes/      # Reusable template components
            ├── header.html
            ├── footer.html
            └── seo_meta.html
```

## Key Components

### 1. Base StreamField Blocks

Reusable content blocks that can be imported into other apps:

**Basic Content Blocks:**
- **BaseHeadingBlock**: Configurable heading with level (h1-h6) and alignment
- **BaseRichTextBlock**: Rich text content with alignment options
- **BaseImageBlock**: Image with caption, alt text, and alignment
- **BaseButtonBlock**: CTA button with DaisyUI styling options
- **BaseSpacerBlock**: Vertical spacing utility

**Advanced Content Blocks:**
- **BaseHeroBlock**: Hero sections with background images, overlays, and CTAs
- **BaseCallToActionBlock**: Engagement-focused CTA sections with various styles
- **BaseAuthorBioBlock**: Author information cards with social media links
- **BaseRecentPostsBlock**: Dynamic blog post displays (list/grid/card layouts)
- **BaseQuoteBlock**: Styled blockquotes with attribution and style variations

**Usage Example:**
```python
from core.models import (
    BaseHeadingBlock,
    BaseRichTextBlock,
    BaseHeroBlock,
    BaseCallToActionBlock,
)

content = StreamField([
    ('heading', BaseHeadingBlock()),
    ('text', BaseRichTextBlock()),
    ('hero', BaseHeroBlock()),
    ('cta', BaseCallToActionBlock()),
], use_json_field=True)
```

### 2. Site Settings

**SiteSettings** - Global configuration:
- Site information (name, tagline, description)
- Contact information (email, phone)
- Social media links (Twitter, LinkedIn, GitHub, Facebook, Instagram)
- SEO settings (meta description, Google Analytics)
- Footer settings (text, copyright)

**HeaderSettings** - Navigation configuration:
- Logo and branding
- Navigation links (up to 5 configurable links)
- Search and theme toggle features
- Header positioning (sticky/static)

**FooterSettings** - Footer configuration:
- Copyright text with auto year
- Footer links (up to 4 configurable links)
- Social media links
- Footer description/additional info

Access in templates:
```django
{% load wagtailsettings_tags %}
{% get_settings %}
{{ settings.core.SiteSettings.site_name }}
{{ settings.core.HeaderSettings.site_title }}
{{ settings.core.FooterSettings.copyright_text }}
```

### 3. Base Abstract Models

**BasePage**: Abstract model with common SEO fields:
- Meta description and keywords
- Open Graph tags (title, description, image)
- Social media sharing optimization

**Usage Example:**
```python
from core.models import BasePage

class MyPage(BasePage):
    # Your custom fields
    pass
```

### 4. Base Templates

- **base.html**: Main layout with header, footer, and content blocks
- **includes/header.html**: Navigation header with responsive menu
- **includes/footer.html**: Footer with social links
- **includes/seo_meta.html**: Complete SEO meta tags

## Configuration

### 1. Enable the App

Add to `INSTALLED_APPS` in settings:
```python
INSTALLED_APPS = [
    'core',
    # ... other apps
]
```

### 2. Run Migrations

```bash
python manage.py makemigrations core
python manage.py migrate core
```

### 3. Configure Site Settings

1. Access Wagtail admin: `/admin/`
2. Navigate to Settings → Site Settings
3. Fill in your site information, social links, and SEO settings

## Design Principles

- **No custom CSS**: All styling uses Tailwind utility classes
- **No JavaScript**: UI achieved purely with Tailwind and DaisyUI
- **DaisyUI components**: Leverages DaisyUI component library
- **Wagtail best practices**: Follows Wagtail documentation standards
- **Reusability**: Components designed for use across multiple apps
- **SEO-first**: Built-in SEO optimization in all components

## Testing

Run tests:
```bash
python manage.py test core
```

## Dependencies

- Django
- Wagtail
- django-tailwind
- DaisyUI (via tailwind plugins)
- @tailwindcss/typography

## Future Enhancements

- Additional reusable blocks (video, embed, callout, etc.)
- More abstract models for common patterns
- Utility functions for common operations
- Enhanced SEO features (structured data, etc.)
