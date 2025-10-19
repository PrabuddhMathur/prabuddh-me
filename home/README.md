# Home Application

The **home** application manages the website's homepage and landing pages. It extends the `core` application to provide a feature-rich, content-flexible homepage using Wagtail StreamFields.

## Purpose

- Provide the main homepage for the website
- Display dynamic content using StreamField blocks from the core app
- Integrate blog post feeds (recent and featured)
- Showcase author information and social links
- Offer a customizable hero section

## Structure

```
home/
├── models.py              # HomePage model
├── apps.py                # App configuration
├── tests.py               # Test cases
├── migrations/            # Database migrations
├── static/
│   └── css/
│       └── welcome_page.css  # Homepage specific styles (legacy)
└── templates/
    └── home/
        ├── home_page.html     # Homepage template
        └── blocks/            # Legacy block templates (now in core)
```

## Key Components

### 1. HomePage Model

The HomePage extends `core.models.BasePage` to inherit SEO functionality and uses StreamField blocks from core.

**Inherited from BasePage:**
- `meta_description` - SEO meta description
- `meta_keywords` - SEO keywords
- `og_title` - Open Graph title for social sharing
- `og_description` - Open Graph description
- `og_image` - Open Graph image

**Homepage-Specific Fields:**
- Hero section (title, subtitle, image, CTA)
- Author information (name, bio, image)
- Social media links (website, Twitter, LinkedIn, GitHub, email)
- StreamField body with various content blocks
- Featured posts configuration
- Recent posts configuration
- Display settings

### 2. StreamField Blocks (from core)

The homepage uses these blocks from `core.models`:
- `BaseRichTextBlock` - Rich text content
- `BaseImageBlock` - Images with captions
- `BaseHeroBlock` - Hero sections
- `BaseCallToActionBlock` - CTA buttons
- `BaseAuthorBioBlock` - Author biography cards
- `BaseRecentPostsBlock` - Recent blog posts display
- `BaseQuoteBlock` - Blockquotes with attribution
- `BaseSpacerBlock` - Vertical spacing

### 3. Template Structure

**Main Template:** `home/templates/home/home_page.html`
- Extends `core/base.html` for consistent layout
- Displays hero section
- Renders StreamField content
- Shows featured and recent blog posts
- Responsive design using TailwindCSS and DaisyUI

**Block Templates:** Located in `core/templates/core/blocks/`
- All block templates are now in the core app for reusability

## Configuration

### Admin Panels

The HomePage has three admin tabs:

1. **Content Tab**
   - Hero Section configuration
   - StreamField content editor
   - Author information
   - Social media links

2. **SEO Tab** (inherited from BasePage)
   - Meta description and keywords
   - Open Graph tags for social sharing

3. **Settings Tab**
   - Featured posts settings
   - Recent posts settings
   - Display options

### Blog Integration

The homepage automatically fetches and displays blog posts when the blog app is available. If the blog app doesn't exist, it gracefully handles the absence with empty lists.

**get_context() method:**
- Fetches recent posts (configurable count)
- Fetches featured posts (if available)
- Provides social links dictionary
- Handles ImportError gracefully

## Usage

### Creating a Homepage

1. In Wagtail admin, go to Pages
2. Add a child page to the root
3. Select "Homepage" as the page type
4. Fill in the content using StreamField blocks
5. Configure SEO settings
6. Adjust display settings
7. Publish

### Customizing Content

Use StreamField blocks to build flexible page content:

```python
# In admin, you can add:
- Hero sections for visual impact
- Rich text for written content
- Images with captions
- Call-to-action buttons
- Author bio cards
- Recent posts widgets
- Quotes for emphasis
- Spacers for layout control
```

### Template Customization

To customize the homepage template:

1. Edit `home/templates/home/home_page.html`
2. Extend `core/base.html` to maintain site consistency
3. Use DaisyUI components and Tailwind CSS classes
4. Override specific blocks as needed

## Dependencies

- **core** - Provides BasePage, StreamField blocks, and base templates
- **blog** - Optional; homepage displays blog posts when available
- **wagtail** - CMS framework
- **django-tailwind** - For styling

## Migrations

Recent migrations:
- `0005_remove_headersettings_logo_and_more.py` - Migrated to use core.BasePage, moved settings to core

## Best Practices

1. **Use Core Blocks** - Always import blocks from `core.models` rather than creating duplicates
2. **SEO Fields** - Utilize inherited SEO fields from BasePage for all pages
3. **Responsive Design** - Test all StreamField content on mobile and desktop
4. **Content Organization** - Use spacer blocks to create proper visual hierarchy
5. **Blog Integration** - Configure featured and recent posts for dynamic content

## Example Usage in Code

```python
from home.models import HomePage

# Get homepage instance
homepage = HomePage.objects.first()

# Access inherited SEO fields
homepage.meta_description  # from BasePage
homepage.og_title  # from BasePage

# Access homepage-specific fields
homepage.hero_title
homepage.author_name
homepage.body  # StreamField content

# Get social links
social_links = homepage.get_social_links_list()
```

## Related Documentation

- [Core App Documentation](../core/README.md)
- [Wagtail StreamField Documentation](https://docs.wagtail.org/en/stable/reference/streamfield/)
- [DaisyUI Components](https://daisyui.com/components/)

## Future Enhancements

- Newsletter subscription integration
- Testimonials section
- Portfolio/projects showcase
- Analytics integration
- A/B testing support

---

**Last Updated:** October 20, 2025  
**Status:** ✅ Production Ready
