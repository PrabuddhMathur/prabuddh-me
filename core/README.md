# Core App - Production-Ready Foundation

## Overview

The **Core** app is the foundational layer of the Prabuddh-Me personal blog application. It provides production-ready reusable components, base models, templates, and settings that are shared across all other applications (`blog`, `home`, etc.). This follows the **DRY (Don't Repeat Yourself)** principle and industry best practices for Django/Wagtail development.

## Architecture Philosophy

**Core-First Approach**: All base functionality, reusable blocks, and shared templates are defined in the `core` app first. Other applications (`blog`, `home`) import and extend from core rather than duplicating code.

### Key Benefits

- **Single Source of Truth**: All base components are defined once in `core`
- **Consistency**: All pages use the same blocks and styling
- **Maintainability**: Changes to blocks or templates only need to be made in one place
- **Scalability**: Easy to add new apps that leverage existing core functionality
- **Production-Ready**: Follows Django/Wagtail best practices with proper error handling, caching, validation, and logging

## Core Components

### 1. Base Models

#### `BasePage` (Abstract Model)
The foundational page model that all other pages inherit from. Provides:
- SEO fields (`meta_description`, `meta_keywords`)
- Open Graph fields for social media (`og_title`, `og_description`, `og_image`)
- Common SEO panels for Wagtail admin
- Database indexes for performance

**Usage in other apps:**
```python
from core.models import BasePage

class BlogPage(BasePage):
    # Your page-specific fields here
    # SEO fields inherited automatically
    pass
```

#### `StaticPage` (Page Model)
A flexible, reusable page model for static content pages like About, Contact, Terms, Privacy, etc. Provides:
- Intro field for page introduction
- StreamField with all available blocks for maximum flexibility
- Optional "last updated" date display
- Full SEO support from `BasePage`
- Search indexing
- Tabbed admin interface

**Usage:**
1. Create pages in Wagtail admin: Pages → Add Child Page → Static Page
2. Set the page title and slug (e.g., "About" with slug "about")
3. Add content using StreamField blocks
4. Publish and access at `/about/`, `/contact/`, etc.

**Example use cases:**
- `/about` - About page with author bio
- `/contact` - Contact information with form or email
- `/terms` - Terms of Service
- `/privacy` - Privacy Policy
- Any other static content page

### 2. Reusable StreamField Blocks

All blocks are production-ready with comprehensive configuration options:

#### Content Blocks
- **`BaseHeadingBlock`**: Configurable headings (H1-H6) with alignment
- **`BaseRichTextBlock`**: Rich text with formatting and alignment options
- **`BaseImageBlock`**: Images with caption, alt text, and alignment
- **`BaseQuoteBlock`**: Blockquotes with author attribution and styling
- **`BaseButtonBlock`**: Styled buttons with DaisyUI themes

#### Layout Blocks
- **`BaseSpacerBlock`**: Vertical spacing control
- **`BaseHeroBlock`**: Hero sections with background images, CTAs
- **`BaseCallToActionBlock`**: Prominent CTAs with styling options

#### Dynamic Blocks
- **`BaseAuthorBioBlock`**: Author biography with photo and social links
- **`BaseRecentPostsBlock`**: Display recent blog posts with layout options

**Usage in other apps:**
```python
from core.models import (
    BaseHeadingBlock,
    BaseRichTextBlock,
    BaseImageBlock,
    BaseHeroBlock,
    BaseCallToActionBlock,
    BaseAuthorBioBlock,
    BaseRecentPostsBlock,
    BaseQuoteBlock,
    BaseButtonBlock,
    BaseSpacerBlock,
)

body = StreamField([
    ('heading', BaseHeadingBlock()),
    ('text', BaseRichTextBlock()),
    ('image', BaseImageBlock()),
    ('hero', BaseHeroBlock()),
    ('cta', BaseCallToActionBlock()),
    ('author_bio', BaseAuthorBioBlock()),
    ('recent_posts', BaseRecentPostsBlock()),
    ('quote', BaseQuoteBlock()),
    ('button', BaseButtonBlock()),
    ('spacer', BaseSpacerBlock()),
], use_json_field=True, blank=True)
```

### 3. Site Settings

#### `SiteSettings`
Global site configuration accessible throughout the application:
- Site name and tagline
- Contact information (email, phone)
- Social media links (Twitter, LinkedIn, GitHub, Facebook, Instagram)
- SEO defaults (meta description, Google Analytics ID)
- Footer text and copyright

#### `HeaderSettings`
Centralized header/navigation configuration:
- Logo and branding
- Navigation links (up to 5 configurable)
- Search and theme toggle options
- Sticky/static positioning
- Helper method: `get_navigation_links()`

#### `FooterSettings`
Centralized footer configuration:
- Copyright text with auto-year
- Footer links (up to 4 configurable)
- Social media links
- Additional footer description
- Helper methods: `get_footer_links()`, `get_social_links()`

**Usage in templates:**
```django
{% load wagtailsettings_tags %}
{% get_settings %}

{{ settings.core.SiteSettings.site_name }}
{{ settings.core.HeaderSettings.site_title }}
{{ settings.core.FooterSettings.copyright_text }}

{# Get navigation links #}
{% for link in settings.core.HeaderSettings.get_navigation_links %}
    <a href="{{ link.url }}">{{ link.text }}</a>
{% endfor %}
```

### 4. Base Templates

#### `core/templates/core/base.html`
The master template that all other templates extend:
- HTML5 structure with semantic markup
- SEO meta tags (via `includes/seo_meta.html`)
- Open Graph and Twitter Card support
- Responsive design with Tailwind CSS
- Header and footer includes
- Google Analytics integration
- Wagtail admin toolbar

**Features:**
- Production-grade SEO optimization
- Accessibility best practices (ARIA labels, semantic HTML)
- Mobile-first responsive design
- Performance optimized (async scripts, lazy loading)

#### Template Structure
```
core/templates/
├── 404.html                      # Custom 404 error page
├── 500.html                      # Custom 500 error page
└── core/
    ├── base.html                 # Master template
    ├── blocks/                   # Block templates
    │   ├── author_bio_block.html
    │   ├── button_block.html
    │   ├── cta_block.html
    │   ├── heading_block.html
    │   ├── hero_block.html
    │   ├── image_block.html
    │   ├── quote_block.html
    │   ├── recent_posts_block.html
    │   ├── rich_text_block.html
    │   └── spacer_block.html
    └── includes/                 # Reusable partials
        ├── footer.html
        ├── header.html
        └── seo_meta.html
```
```
core/templates/
├── core/
│   ├── base.html                 # Master template
│   ├── blocks/                   # Block templates
│   │   ├── author_bio_block.html
│   │   ├── button_block.html
│   │   ├── cta_block.html
│   │   ├── heading_block.html
│   │   ├── hero_block.html
│   │   ├── image_block.html
│   │   ├── quote_block.html
│   │   ├── recent_posts_block.html
│   │   ├── rich_text_block.html
│   │   └── spacer_block.html
│   └── includes/                 # Reusable partials
│       ├── footer.html
│       ├── header.html
│       └── seo_meta.html
```

**Creating a template that extends base:**
```django
{# your_app/templates/your_app/your_page.html #}
{% extends "core/base.html" %}
{% load wagtailcore_tags %}

{% block title %}{{ page.title }}{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1>{{ page.title }}</h1>
    {{ page.body }}
</div>
{% endblock %}
```

## Production-Grade Features

### ✅ Error Handling
- Try-except blocks around database queries
- Graceful degradation when optional features fail
- Comprehensive logging for debugging
- Proper exception handling in model methods

### ✅ Caching
- Query result caching for performance (15-minute TTL)
- Cache invalidation on model save
- Cache keys with namespacing
- Configurable cache backends

### ✅ Validation
- Field-level validation with Django validators
- Model-level validation in `clean()` methods
- Helpful error messages for content editors
- Date validation (no future dates)
- Required field checks

### ✅ Database Optimization
- Strategic `db_index=True` on frequently queried fields
- `select_related()` and `prefetch_related()` where appropriate
- Efficient QuerySet usage
- No N+1 query problems

### ✅ Logging
- Structured logging throughout the application
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Production-ready log configuration
- Error tracking with full stack traces

### ✅ SEO Optimization
- Complete meta tag support
- Open Graph for social sharing
- Twitter Card integration
- Canonical URLs
- Google Analytics support
- Structured data ready

### ✅ Security
- No inline JavaScript
- CSP-friendly implementation
- Secure settings references
- CSRF protection

## Usage Examples

### Creating a New Page Type

```python
# your_app/models.py
from django.db import models
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel

from core.models import (
    BasePage,
    BaseHeadingBlock,
    BaseRichTextBlock,
    BaseImageBlock,
    BaseHeroBlock,
)

class YourPage(BasePage):
    """
    Your custom page type.
    Inherits SEO functionality from BasePage.
    """
    
    intro = models.TextField(
        blank=True,
        help_text="Introduction text"
    )
    
    body = StreamField([
        ('heading', BaseHeadingBlock()),
        ('text', BaseRichTextBlock()),
        ('image', BaseImageBlock()),
        ('hero', BaseHeroBlock()),
    ], use_json_field=True, blank=True)
    
    content_panels = BasePage.content_panels + [
        FieldPanel('intro'),
        FieldPanel('body'),
    ]
    
    # Inherit SEO panels from BasePage
    promote_panels = BasePage.promote_panels + BasePage.seo_panels
    
    class Meta:
        verbose_name = "Your Page"
        verbose_name_plural = "Your Pages"
```

## Best Practices

### When Adding New Features

1. **Check if it belongs in Core**: If the feature will be used by multiple apps, add it to `core`
2. **Use Base Classes**: Always extend `BasePage` for new page types
3. **Reuse Blocks**: Use existing StreamField blocks before creating new ones
4. **Follow Patterns**: Match the structure and style of existing core components
5. **Document**: Update this README when adding new core functionality
6. **Test**: Add tests for new functionality

### Code Quality Standards

- **Type Hints**: Use Python type hints where appropriate
- **Docstrings**: Document all classes and non-trivial methods
- **Logging**: Add appropriate log statements
- **Error Handling**: Wrap risky operations in try-except
- **Validation**: Add `clean()` methods for complex validation
- **Performance**: Consider caching for expensive operations

### Performance Considerations

- Use caching for expensive queries (already implemented)
- Add database indexes for frequently filtered fields
- Optimize images before upload
- Use lazy loading for images
- Minimize database queries in templates
- Use `select_related()` and `prefetch_related()`

### SEO Best Practices

- Always provide meta descriptions
- Use descriptive page titles
- Include Open Graph images (1200x630px)
- Set up Google Analytics in SiteSettings
- Use semantic HTML structure
- Add alt text to all images

## Development Workflow

1. **Make changes to core models/blocks**
2. **Create migrations**: `python manage.py makemigrations core`
3. **Review migrations**: Check the generated migration file
4. **Run migrations**: `python manage.py migrate`
5. **Update this README** with any new functionality
6. **Test across all apps** that use core functionality
7. **Run tests**: `python manage.py test core`

## File Structure

```
core/
├── __init__.py
├── admin.py                  # Wagtail admin customizations
├── apps.py                   # App configuration
├── models.py                 # Base models, blocks, and settings (970 lines)
├── README.md                 # This documentation
├── tests.py                  # Unit tests
├── views.py                  # Views (if needed)
├── migrations/               # Database migrations
│   ├── __init__.py
│   ├── 0001_initial.py
│   ├── 0002_footersettings_headersettings.py
│   └── 0003_alter_sitesettings_site_name.py
├── templates/
│   ├── 404.html              # Custom 404 error page
│   ├── 500.html              # Custom 500 error page
│   └── core/
│       ├── base.html         # Master template
│       ├── blocks/           # All StreamField block templates
│       └── includes/         # Header, footer, SEO meta
└── __pycache__/
```

## Testing

```bash
# Run core app tests
python manage.py test core

# Run with coverage
coverage run --source='core' manage.py test core
coverage report

# Check for issues
python manage.py check

# Validate templates
python manage.py validate_templates
```

## Dependencies

- **Django**: Web framework
- **Wagtail**: CMS framework
- **django-tailwind**: CSS framework integration
- **DaisyUI**: Component library
- **Pillow**: Image processing

## Integration with Other Apps

### Blog App
- Imports all base blocks from core
- Extends `BasePage` for `BlogPage`
- Uses core templates (`core/base.html`)
- No duplicate blocks or templates

### Home App
- Imports all base blocks from core
- Extends `BasePage` for `HomePage`
- Uses core templates (`core/base.html`)
- No duplicate blocks or templates

## Related Documentation

- [Architecture Documentation](../documentation/ARCHITECTURE.md)
- [Blog App README](../blog/README.md)
- [Home App README](../home/README.md)
- [Wagtail Documentation](https://docs.wagtail.org/)
- [Django Documentation](https://docs.djangoproject.com/)

## Changelog

### Latest Changes (October 20, 2025)
- ✅ Moved 404 and 500 error pages to core app templates
- ✅ Removed unused `prabuddh_me/templates` directory
- ✅ Updated Django settings to remove custom TEMPLATES DIRS configuration
- ✅ Updated search template to extend from `core/base.html` with Tailwind styling
- ✅ Enhanced SEO meta template to support both Wagtail pages and seo_meta dictionaries
- ✅ Fixed SEO meta template to work with blog archive views without MockPage
- ✅ Fixed SEO meta template to remove `page.intro` reference causing errors on HomePage
- ✅ Improved meta description fallback chain to use only universal fields
- ✅ Removed all duplicate templates from home app
- ✅ Centralized all reusable blocks in core
- ✅ Added production-grade error handling and caching to blog
- ✅ Enhanced validation with comprehensive `clean()` methods
- ✅ Improved logging throughout with structured log messages
- ✅ Added type hints for better code documentation
- ✅ Implemented cache management with TTL and invalidation
- ✅ Added class methods for common queries (`get_recent_posts`, etc.)
- ✅ Database optimization with strategic indexes
- ✅ Complete SEO meta template with OG and Twitter Cards
- ✅ Implemented Reddit-style spoiler text feature for Draftail editor

## Wagtail Custom Features

### Spoiler Text (Draftail Inline Style)

A Reddit-style spoiler text feature integrated into the Wagtail Draftail editor.

**Features:**
- Blurred text in editor and frontend
- Click-to-reveal functionality
- Keyboard accessible (Tab + Enter/Space)
- Revealed state persists until page refresh
- Dark mode support
- ARIA attributes for screen readers

**Usage in Wagtail Admin:**
1. Select text in the Draftail editor
2. Click the 👁 (eye) icon in the toolbar
3. Text becomes blurred as a spoiler
4. On the published page, click the spoiler to reveal

**Technical Implementation:**
- **File:** [`core/wagtail_hooks.py`](core/wagtail_hooks.py:1) - Registers the Draftail feature
- **CSS:** [`core/static/core/css/spoiler.css`](core/static/core/css/spoiler.css:1) - Styling for blur effect
- **JavaScript:** [`core/static/core/js/spoiler.js`](core/static/core/js/spoiler.js:1) - Click-to-reveal functionality
- **Template:** [`core/templates/core/blocks/rich_text_block.html`](core/templates/core/blocks/rich_text_block.html:1) - Loads assets
- **Database Format:** `<span class="spoiler" data-spoiler="true">content</span>`

**Accessibility:**
- Keyboard navigation supported (Tab to focus, Enter/Space to reveal)
- ARIA labels for screen readers
- Focus indicators for keyboard users
- Progressive enhancement (works without JavaScript, just no reveal interaction)

### Citation Feature

Wikipedia-style inline citations with automatic references section generation.

#### Overview

The citation feature allows content editors to add numbered citations to blog posts that link to a references section automatically generated at the bottom of the page. Citations appear as superscript numbers (e.g., [1], [2]) and scroll to their corresponding reference when clicked.

#### Usage in Wagtail Admin

1. Click the 📖 (book) button in the Draftail editor toolbar
2. Enter citation number (auto-suggested based on existing citations)
3. Enter citation text/description (required)
4. Optionally enter a URL (can be cancelled/skipped)
5. Citation appears as blue superscript number in editor

#### Frontend Behavior

**Citation Display:**
- Citations appear as blue superscript links: [1]
- Clicking scrolls smoothly to the reference section
- References section auto-generates at page bottom
- Each reference has a ↑ back arrow to return to citation
- Yellow highlight animation on scroll target

**Keyboard Accessibility:**
- Tab to focus citations and back arrows
- Enter or Space to activate
- Screen reader support via ARIA labels

#### Technical Implementation

**Backend (Python):**
- [`core/wagtail_hooks.py`](wagtail_hooks.py) (lines 76-167):
  - `CitationEntityElementHandler`: Custom handler for HTML-to-ContentState conversion
  - `citation_entity_decorator`: ContentState-to-HTML conversion
  - `register_citation_feature`: Wagtail hook registration
  - Entity type: `'CITATION'`
  - Storage format: `<a class="citation" data-ref="{number}" data-text="{text}" data-url="{url}" href="#ref-{number}"><sup>[{number}]</sup></a>`

**Editor Plugin (JavaScript):**
- [`core/static/core/js/citation_plugin.js`](static/core/js/citation_plugin.js):
  - `CitationSource`: React component for creating citations via prompts
  - `Citation`: Decorator component for displaying citations in editor
  - Auto-increment citation numbers
  - Immutable entity type

**Frontend Behavior (JavaScript):**
- [`core/static/core/js/citation.js`](static/core/js/citation.js):
  - Click-to-scroll for citations
  - Back-to-citation navigation
  - Highlight animations
  - Keyboard support
  - MutationObserver for dynamic content

**Styling (CSS):**
- [`core/static/core/css/citation.css`](static/core/css/citation.css):
  - Wikipedia-style blue citations (#0066cc)
  - Superscript positioning
  - References list styling
  - Yellow highlight animation
  - Dark mode support

**Template Integration:**
- [`core/templates/core/blocks/rich_text_block.html`](templates/core/blocks/rich_text_block.html):
  - Loads citation.css and citation.js
- [`blog/templates/blog/blog_page.html`](../../blog/templates/blog/blog_page.html):
  - Auto-extracts citations using template tag
  - Displays references section if citations exist

**Citation Extraction:**
- [`core/templatetags/citation_tags.py`](templatetags/citation_tags.py):
  - `extract_citations` template tag
  - Parses StreamField HTML for citation elements
  - Returns sorted list of unique citations
  - Uses BeautifulSoup4 for reliable parsing

#### Data Structure

**Entity Data (in editor):**
```javascript
{
  number: '1',        // Citation number
  text: 'Description', // Citation text/description  
  url: 'https://...'   // Optional URL
}
```

**HTML Storage:**
```html
<a class="citation" 
   data-ref="1" 
   data-text="Source description"
   data-url="https://example.com"
   href="#ref-1">
  <sup>[1]</sup>
</a>
```

**References Section:**
```html
<section id="references" class="references-section">
  <h2>References</h2>
  <ol class="references-list">
    <li id="ref-1">
      <a href="#cite-1" class="back-to-citation">↑</a>
      Source description
      <a href="https://example.com">Link</a>
    </li>
  </ol>
</section>
```

#### Dependencies

- **beautifulsoup4** (>=4.12.0): HTML parsing for citation extraction
- Added to requirements.txt

#### Features Enabled In

The citation feature is enabled in:
- `BaseRichTextBlock` in [`core/models.py`](models.py) (line 56)
- Available in all blog post rich text fields

#### Important Notes

1. **Bidirectional Conversion**: The custom `CitationEntityElementHandler` ensures citations retain their data when loading from database
2. **Auto-numbering**: JavaScript plugin suggests next citation number based on existing citations
3. **No Separate Model**: Citations are stored inline in rich text HTML
4. **Template Tag**: `{% load citation_tags %}` and `{% extract_citations page.body as citations %}` in templates
5. **File Paths**: EntityFeature loads `citation_plugin.js` automatically in Wagtail admin; frontend loads `citation.js` separately

#### Testing

To test the citation feature:
1. Create/edit a blog post in Wagtail admin
2. Add citations using the 📖 button
3. Save and publish the page
4. View on frontend and test:
   - Citation links scroll to references
   - Back arrows return to citations
   - Keyboard navigation works
   - Dark mode displays correctly

## Future Enhancements

- [ ] Add more StreamField blocks (video, gallery, accordion, tabs)
- [ ] Implement multi-language support (i18n)
- [ ] Add A/B testing capabilities
- [ ] Enhanced analytics integration (GA4)
- [ ] Performance monitoring dashboard
- [ ] Rate limiting for API endpoints
- [ ] Advanced caching strategies (Redis)
- [ ] Image optimization pipeline
- [ ] CDN integration for static files

## Troubleshooting

### Common Issues

**Issue**: Templates not found  
**Solution**: Ensure `core` is in `INSTALLED_APPS` and templates are in `core/templates/core/`

**Issue**: Settings not loading in templates  
**Solution**: Add `{% load wagtailsettings_tags %}` and `{% get_settings %}` at the top

**Issue**: VariableDoesNotExist error for `page.intro`  
**Solution**: The `intro` field only exists on `BlogPage` and `BlogIndexPage`, not on all page types. The SEO meta template now uses a universal fallback chain that works for all page types.

**Issue**: Blocks not rendering  
**Solution**: Check block template paths match the `template` attribute in block Meta class

**Issue**: Migrations not applying  
**Solution**: Run `python manage.py migrate core` and check for conflicts

## Support

For questions or issues:
1. Check this README
2. Review the [Architecture Documentation](../documentation/ARCHITECTURE.md)
3. Check Wagtail documentation: https://docs.wagtail.org/
4. Review commit history for context

---

**Maintainer**: Prabuddh Mathur  
**Last Updated**: October 20, 2025  
**Version**: 2.0 (Production-Ready Refactor)
