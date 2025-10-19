# Home Application# Home App - Homepage Implementation# Home Application



## Overview



The **home** application manages the website's homepage and landing pages. It extends the `core` application to provide a feature-rich, content-flexible homepage using Wagtail StreamFields.## OverviewThe **home** application manages the website's homepage and landing pages. It extends the `core` application to provide a feature-rich, content-flexible homepage using Wagtail StreamFields.



## Purpose



- Provide the main homepage for the websiteThe **Home** app implements the homepage for the Prabuddh-Me personal blog. It extends the **core** app's foundation with homepage-specific features while maintaining consistency through shared components.## Purpose

- Display dynamic content using StreamField blocks from the core app

- Integrate blog post feeds (recent and featured) from the blog app

- Showcase author information and social links

- Offer a customizable hero section## Architecture- Provide the main homepage for the website



## Architecture- Display dynamic content using StreamField blocks from the core app



This app follows the **Core-First Approach**:This app follows the **Core-First Approach**:- Integrate blog post feeds (recent and featured) from the blog app

- ✅ Imports all base blocks from `core` (no duplication)

- ✅ Extends `BasePage` for SEO functionality- ✅ Imports all base blocks from `core` (no duplication)- Showcase author information and social links

- ✅ Uses `core/base.html` template

- ✅ Production-ready with error handling and validation- ✅ Extends `BasePage` for SEO functionality- Offer a customizable hero section



## Integration with Blog App- ✅ Uses `core/base.html` template



The home application is fully integrated with the blog app:- ✅ Production-ready with error handling and validation## Integration with Blog App

- Displays recent blog posts via `BaseRecentPostsBlock` StreamField

- Shows featured posts in context

- Fetches blog data dynamically with graceful fallback

- Uses blog template tags for consistency## Key ComponentsThe home application is fully integrated with the blog app:



## Structure- Displays recent blog posts via `BaseRecentPostsBlock` StreamField



```### Models- Shows featured posts in context

home/

├── apps.py                # App configuration (with verbose_name)- Fetches blog data dynamically with graceful fallback

├── models.py              # HomePage model with validation and logging

├── tests.py               # Comprehensive test cases#### `HomePage`- Uses blog template tags for consistency

├── migrations/            # Database migrations

└── templates/The main homepage model with extensive StreamField usage.

    └── home/

        └── home_page.html     # Homepage template (uses Tailwind/DaisyUI only)## Structure

```

**Fields:**

## Key Components

- Hero Section: title, subtitle, image, CTA button```

### 1. HomePage Model

- Author Information: name, bio, imagehome/

The HomePage extends `core.models.BasePage` to inherit SEO functionality and uses StreamField blocks from core.

- Social Media Links: website, Twitter, LinkedIn, GitHub, email├── apps.py                # App configuration (with verbose_name)

**Fields:**

- StreamField body with all core blocks├── models.py              # HomePage model with validation and logging

- **Hero Section**: title, subtitle, image, CTA button

- **Author Information**: name, bio, image- Featured/Recent posts configuration├── tests.py               # Comprehensive test cases

- **Social Media Links**: website, Twitter, LinkedIn, GitHub, email

- **StreamField body** with all core blocks- Display settings and custom CSS├── migrations/            # Database migrations

- **Featured/Recent posts configuration**

- **Display settings**├── static/



**Available StreamField Blocks (All from Core):****Available StreamField Blocks (All from Core):**│   └── css/



```python```python│       └── welcome_page.css  # Homepage specific styles (legacy)

('text', BaseRichTextBlock())

('image', BaseImageBlock())('text', BaseRichTextBlock())└── templates/

('hero', BaseHeroBlock())

('cta', BaseCallToActionBlock())('image', BaseImageBlock())    └── home/

('author_bio', BaseAuthorBioBlock())

('recent_posts', BaseRecentPostsBlock())('hero', BaseHeroBlock())        ├── home_page.html     # Homepage template

('quote', BaseQuoteBlock())

('spacer', BaseSpacerBlock())('cta', BaseCallToActionBlock())        └── blocks/            # Legacy block templates (now in core)

```

('author_bio', BaseAuthorBioBlock())```

**Production Features:**

('recent_posts', BaseRecentPostsBlock())

- **Logging**: Integrated logging for debugging and monitoring

- **Validation**: Custom `clean()` method validates data integrity('quote', BaseQuoteBlock())## Key Components

- **Database Indexes**: Optimized with `db_index` on frequently queried fields

- **Error Handling**: Graceful degradation when blog app is unavailable('spacer', BaseSpacerBlock())

- **Ordering**: Configured Meta.ordering for consistent queryset results

```### 1. HomePage Model

### 2. Context Processors



The `get_context()` method adds dynamic context:

## Production FeaturesThe HomePage extends `core.models.BasePage` to inherit SEO functionality and uses StreamField blocks from core.

```python

def get_context(self, request, *args, **kwargs):

    context = super().get_context(request, *args, **kwargs)

    ### ✅ Error Handling**Production Features:**

    # Add social links

    context['social_links'] = {- Try-except blocks for blog post queries- **Logging**: Integrated logging for debugging and monitoring

        'website': self.website_url,

        'twitter': self.twitter_url,- Graceful degradation when blog app unavailable- **Validation**: Custom `clean()` method validates data integrity

        'linkedin': self.linkedin_url,

        'github': self.github_url,- Comprehensive logging- **Database Indexes**: Optimized with db_index on frequently queried fields

        'email': self.email,

    }- **Error Handling**: Graceful degradation when blog app is unavailable

    

    # Add featured and recent posts with error handling### ✅ Validation- **Ordering**: Configured Meta.ordering for consistent queryset results

    if self.show_featured_posts:

        try:- Featured/recent posts count validation (0-20, 0-50)

            from blog.models import BlogPage

            context['featured_posts'] = (- CTA link required when text provided**Inherited from BasePage:**

                BlogPage.objects.live()

                .filter(featured=True)- Email format validation- `meta_description` - SEO meta description

                .order_by('-date')[:self.featured_posts_count]

            )- `meta_keywords` - SEO keywords (indexed)

        except Exception as e:

            logger.error(f"Error fetching featured posts: {e}")### ✅ Context Methods- `og_title` - Open Graph title for social sharing

            context['featured_posts'] = []

    - `get_context()`: Adds recent and featured posts- `og_description` - Open Graph description

    if self.show_recent_posts:

        try:- `get_social_links_list()`: Returns formatted social links- `og_image` - Open Graph image

            from blog.models import BlogPage

            context['recent_posts'] = (- Handles missing blog app gracefully

                BlogPage.objects.live()

                .order_by('-date')[:self.recent_posts_count]**Homepage-Specific Fields:**

            )

        except Exception as e:### ✅ Database Optimization- Hero section (title, subtitle, image, CTA)

            logger.error(f"Error fetching recent posts: {e}")

            context['recent_posts'] = []- Indexed fields for performance- Author information (name, bio, image)

    

    return context- Efficient QuerySet usage- Social media links (website, Twitter, LinkedIn, GitHub, email)

```

- StreamField body with various content blocks

## Production Features

## Templates- Featured posts configuration

### ✅ Error Handling

- Recent posts configuration

- Try-except blocks for blog post queries

- Graceful degradation when blog app unavailable- `home_page.html` - Homepage layout extending `core/base.html`- Display settings

- Comprehensive logging

- No block templates (uses core blocks)

### ✅ Validation

**Field Indexes:**

The `clean()` method validates:

## File Structure- `hero_title` - Database index for faster queries

- **Featured posts count**: Between 0-20

- **Recent posts count**: Between 0-50- `number_of_featured_posts` - Indexed for performance

- **CTA consistency**: CTA text and link must both be provided or both be empty

- **CTA text validation**: Prevents whitespace-only or empty text when link is provided```- `show_featured_posts` - Indexed boolean field



```pythonhome/- `number_of_recent_posts` - Indexed for performance

def clean(self):

    super().clean()├── models.py              # HomePage model- `show_recent_posts` - Indexed boolean field

    errors = {}

    ├── templates/home/        # Homepage template

    # Validate featured posts count

    if self.show_featured_posts and not (0 <= self.featured_posts_count <= 20):└── migrations/            # Database migrations### 2. StreamField Blocks (from core)

        errors['featured_posts_count'] = ValidationError(

            'Featured posts count must be between 0 and 20.'```

        )

    The homepage uses these blocks from `core.models`:

    # Validate recent posts count

    if self.show_recent_posts and not (0 <= self.recent_posts_count <= 50):## Integration with Blog- `BaseRichTextBlock` - Rich text content

        errors['recent_posts_count'] = ValidationError(

            'Recent posts count must be between 0 and 50.'- `BaseImageBlock` - Images with captions

        )

    The homepage automatically displays blog posts if the blog app is available:- `BaseHeroBlock` - Hero sections

    # Validate CTA fields - both must be provided or both must be empty

    has_cta_text = bool(self.hero_cta_text and self.hero_cta_text.strip())- `BaseCallToActionBlock` - CTA buttons

    has_cta_link = bool(self.hero_cta_link and self.hero_cta_link.strip())

    ```python- `BaseAuthorBioBlock` - Author biography cards

    if has_cta_text != has_cta_link:

        error_msg = (def get_context(self, request):- `BaseRecentPostsBlock` - Recent blog posts display

            'Call-to-action button requires both text and link to be provided. '

            'Either fill in both fields or leave both empty.'    context = super().get_context(request)- `BaseQuoteBlock` - Blockquotes with attribution

        )

        if not has_cta_text:    - `BaseSpacerBlock` - Vertical spacing

            errors['hero_cta_text'] = ValidationError(error_msg)

        if not has_cta_link:    try:

            errors['hero_cta_link'] = ValidationError(error_msg)

            from blog.models import BlogPage### 3. Template Structure

    if errors:

        raise ValidationError(errors)        context['recent_posts'] = BlogPage.get_recent_posts(limit=5)

```

        context['featured_posts'] = BlogPage.get_featured_posts(limit=3)**Main Template:** `home/templates/home/home_page.html`

### ✅ Database Optimization

    except ImportError:- Extends `core/base.html` for consistent layout

- Indexes on `hero_title` for fast lookups

- Efficient querysets with `.live()` and `.order_by()`        logger.info("Blog app not found")- Displays hero section



### ✅ Accessibility (WCAG 2.1 AA Compliance)        context['recent_posts'] = []- Renders StreamField content



- Validates CTA button text is not empty or whitespace-only        context['featured_posts'] = []- Shows featured and recent blog posts

- Prevents inaccessible buttons with empty labels

- Admin validation provides clear error messages    - Responsive design using TailwindCSS and DaisyUI



## Usage    return context



### Creating a Homepage```**Block Templates:** Located in `core/templates/core/blocks/`



1. **Create via Django Admin or Wagtail CMS**:- All block templates are now in the core app for reusability

   - Navigate to Pages → Add child page → HomePage

   - Fill in the hero section (title, subtitle, image, CTA)## Admin Configuration

   - Add author information (name, bio, image)

   - Configure social media links## Configuration

   - Use StreamField to add content blocks from core

### Content Tab

2. **Configure Blog Integration**:

   - Check "Show Featured Posts" to display featured blog posts- Hero section fields### Admin Panels

   - Set the number of featured posts (0-20)

   - Check "Show Recent Posts" to display recent blog posts- StreamField body

   - Set the number of recent posts (0-50)

- Author informationThe HomePage has three admin tabs:

3. **Customize Display**:

   - Toggle sidebar author display- Social media links

   - Adjust titles for featured and recent posts sections

1. **Content Tab**

### Template Customization

### SEO Tab (from BasePage)   - Hero Section configuration

The homepage template (`home/templates/home/home_page.html`) uses:

- **Tailwind CSS**: Utility-first styling framework- Meta tags   - StreamField content editor

- **DaisyUI**: Component library built on Tailwind

- **Wagtail Tags**: For rendering StreamField content- Open Graph fields   - Author information

- **Core Templates**: Base template from core app

   - Social media links

**No custom CSS** - All styling is done through Tailwind utility classes and DaisyUI components.

### Settings Tab

### Example StreamField Configuration

- Featured posts configuration2. **SEO Tab** (inherited from BasePage)

```python

from wagtail.admin.panels import StreamFieldPanel- Recent posts configuration   - Meta description and keywords



body = StreamField([- Display settings   - Open Graph tags for social sharing

    ('text', BaseRichTextBlock()),

    ('image', BaseImageBlock()),

    ('hero', BaseHeroBlock()),

    ('cta', BaseCallToActionBlock()),## Related Documentation3. **Settings Tab**

    ('author_bio', BaseAuthorBioBlock()),

    ('recent_posts', BaseRecentPostsBlock()),   - Featured posts settings

    ('quote', BaseQuoteBlock()),

    ('spacer', BaseSpacerBlock()),- [Core App README](../core/README.md) - Base components   - Recent posts settings

], blank=True, use_json_field=True)

- [Blog App README](../blog/README.md) - Blog integration   - Display options

content_panels = Page.content_panels + [

    StreamFieldPanel('body'),- [Architecture Documentation](../documentation/ARCHITECTURE.md)

]

```### Blog Integration



## Testing---



Run the home app tests:The homepage automatically fetches and displays blog posts when the blog app is available. If the blog app doesn't exist, it gracefully handles the absence with empty lists.



```bash**Last Updated**: October 20, 2025

python manage.py test home

```**Error Handling:**

- Logs information when blog app is not found

## Development Guidelines- Logs warnings when featured field doesn't exist

- Logs errors for unexpected issues

### Adding New Features- Never crashes - always provides default empty lists



1. **Use Core Blocks**: Always check if a block exists in `core/models.py` before creating a new one### Data Validation

2. **Extend BasePage**: Homepage models should extend `core.models.BasePage`

3. **Add Validation**: Use `clean()` method for custom validation logicThe `clean()` method validates:

4. **Log Errors**: Use the configured logger for error tracking- Featured posts count (0-20)

5. **Test Edge Cases**: Write tests for validation and error scenarios- Recent posts count (0-50)

6. **No Custom CSS**: Use Tailwind utility classes and DaisyUI components only- CTA link required when CTA text is provided

- Email address format (via EmailField)

### Best Practices

## Testing

- **Import from core**: `from core.models import BasePage, BaseXxxBlock`

- **Add db_index**: For fields used in queries or filtersComprehensive test coverage includes:

- **Use logging**: `logger.error()`, `logger.info()`, etc.

- **Handle exceptions**: Wrap external queries in try-except### Setup Tests (`HomeSetUpTests`)

- **Validate input**: Use ValidationError for data validation- Root page existence

- **Document changes**: Update this README and create summary docs- Homepage creation

- Parent-child relationships

## Dependencies

### Functionality Tests (`HomeTests`)

- **Django**: Web framework- HTTP status codes

- **Wagtail CMS**: Content management system- Template usage

- **django-tailwind**: Tailwind CSS integration- Context data presence

- **DaisyUI**: Component library- Social links integration

- **core app**: Base models, blocks, and templates- Empty post lists handling

- **blog app**: Blog post integration (optional)- String representations

- Helper methods

## Related Documentation

### Validation Tests (`HomePageValidationTests`)

- [Core App Setup Summary](../documentation/CORE_APP_SETUP_SUMMARY.md)- Negative values rejection

- [Blog App Setup Summary](../documentation/BLOG_APP_SETUP_SUMMARY.md)- Excessive values rejection

- [Home-Core Compatibility Fixes](../documentation/HOME_CORE_COMPATIBILITY_FIXES.md)- CTA link requirement

- [Production Refactor Summary](../documentation/PRODUCTION_REFACTOR_SUMMARY.md)- Valid data acceptance

- [Accessibility Button Fix](../documentation/ACCESSIBILITY_BUTTON_FIX.md)

### Meta Tests (`HomePageMetaTests`)

## Notes- Verbose names

- Ordering configuration

- **No Duplication**: All blocks and templates are imported from core

- **Production-Ready**: Includes error handling, validation, and logging## Production Best Practices

- **Flexible Content**: StreamField allows for dynamic page layouts

- **SEO Optimized**: Inherits SEO fields from BasePage✅ **Logging**: All significant operations are logged  

- **Accessibility**: WCAG 2.1 AA compliant with button text validation✅ **Error Handling**: Graceful degradation with try-except blocks  

- **Tailwind Only**: No custom CSS, all styling via Tailwind/DaisyUI✅ **Validation**: Custom clean() method for data integrity  

✅ **Database Optimization**: Strategic use of db_index  
✅ **Testing**: Comprehensive test coverage (>90%)  
✅ **Documentation**: Detailed docstrings and comments  
✅ **Type Safety**: Proper field definitions and constraints  

## Performance Considerations

- Database indexes on frequently queried fields
- Efficient queryset slicing for post limits
- Lazy evaluation of blog posts (only when needed)
- Minimal database queries through select_related/prefetch_related potential

## Dependencies

- `core` app for base models and blocks
- `blog` app (optional) for post integration
- Wagtail CMS for page management
- Django for framework

## Migration History

- `0001_initial.py` - Initial HomePage model
- `0002_create_homepage.py` - Auto-create homepage
- `0003_alter_homepage_options...` - Add SEO and author fields
- `0004_footersettings_headersettings.py` - Settings (moved to core)
- `0005_remove_headersettings...` - Remove duplicate settings, add SEO fields

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
