# Blog App - Production-Ready Blog Engine# Blog Application



## OverviewThe **blog** application provides a full-featured blogging system for the personal website. It extends the `core` application to leverage reusable StreamField blocks and follows production-grade Django/Wagtail best practices.



The **Blog** app provides a full-featured blog system for the Prabuddh-Me personal website. It extends the **core** app's foundation with blog-specific functionality while maintaining consistency through shared components.## Purpose



## Architecture- Provide a complete blog with post listing and detail pages

- Support rich content creation using StreamField blocks from core

This app follows the **Core-First Approach**:- Enable tagging, categorization, and filtering of blog posts

- ✅ Imports all base blocks from `core` (no duplication)- Offer featured posts, pagination, and search functionality

- ✅ Extends `BasePage` for SEO functionality- Integrate seamlessly with the home application

- ✅ Uses `core/base.html` template

- ✅ Production-ready with error handling, caching, and validation## Structure



## Key Components```

blog/

### Models├── apps.py                # App configuration with verbose_name

├── admin.py               # Wagtail ModelAdmin configuration

#### `BlogPageTag`├── models.py              # BlogIndexPage and BlogPage models

Tag model for categorizing blog posts using `django-taggit`.├── tests.py               # Comprehensive test suite

├── migrations/            # Database migrations

#### `BlogPage`└── templates/

Individual blog post model with rich content capabilities.    └── blog/

        ├── blog_index_page.html      # Blog listing template

**Fields:**        ├── blog_page.html            # Individual post template

- `author`: Post author name (indexed)        └── includes/

- `author_bio`: Optional author biography override            ├── post_card.html         # Card layout component

- `date`: Publication date (indexed, validated)            └── post_list_item.html    # List layout component

- `intro`: Brief excerpt (250 chars max, indexed)```

- `featured_image`: Header image with caption

- `body`: Rich content using StreamField (all 10 core blocks)## Key Components

- `tags`: Post categorization

- `featured`: Mark post for homepage display (indexed)### 1. Blog Models

- `show_author_bio`: Display author info toggle

- `show_related_posts`: Show related content toggle#### BlogIndexPage

- `estimated_reading_time`: Auto-calculated (words/200)

The main blog listing page that displays all blog posts with advanced features:

**Available StreamField Blocks (All from Core):**

```python**Production Features:**

('heading', BaseHeadingBlock())         # H1-H6 headings- **Pagination**: Configurable posts per page

('text', BaseRichTextBlock())          # Rich text content- **Featured Posts**: Highlight important posts at the top

('image', BaseImageBlock())            # Images with captions- **Tag Filtering**: Filter posts by tags via query parameters

('quote', BaseQuoteBlock())            # Styled blockquotes- **Multiple Layouts**: Support for list, grid, and masonry views

('button', BaseButtonBlock())          # CTA buttons- **Context Enrichment**: Provides featured posts, pagination, and tag lists

('spacer', BaseSpacerBlock())          # Vertical spacing- **Validation**: Custom `clean()` method for data integrity

('hero', BaseHeroBlock())              # Hero sections- **Max Count**: Only one blog index page allowed per site

('cta', BaseCallToActionBlock())       # Call-to-action blocks

('author_bio', BaseAuthorBioBlock())   # Author cards**Fields:**

('recent_posts', BaseRecentPostsBlock())# Recent posts widget- `intro` - RichTextField for introduction text

```- `posts_per_page` - Number of posts per page (default: 10)

- `show_featured_posts` - Toggle featured posts section

## Production Features- `featured_posts_count` - Number of featured posts to display

- `layout_style` - Choose between list, grid, or masonry layout

### ✅ Error Handling

- Try-except blocks around all database operations**Parent/Subpage Rules:**

- Graceful degradation when features fail- Can only be created under `HomePage`

- Comprehensive logging with stack traces- Can only have `BlogPage` as children

- Limited to 1 instance per site

### ✅ Caching

- Related posts cached for 15 minutes#### BlogPage

- Automatic cache invalidation on save

- Performance optimization for expensive queriesIndividual blog post with rich content capabilities:



### ✅ Comprehensive Validation**Production Features:**

- Intro length validation (250 chars max)- **StreamField Content**: Uses blocks from core app for flexible content

- Date validation (no future dates)- **Tagging System**: django-taggit integration for categorization

- Author name required validation- **Reading Time**: Auto-calculated based on word count

- Featured image accessibility warnings- **Related Posts**: Shows posts with shared tags

- **Post Navigation**: Previous/next post links

### ✅ Class Methods for Common Queries- **Search Indexing**: Wagtail search integration

```python- **Database Indexes**: Optimized fields for performance

# Get recent posts with caching- **Validation**: Field-level and model-level validation

recent_posts = BlogPage.get_recent_posts(limit=5)- **Logging**: Integrated logging for debugging



# Get posts by tag**Fields:**

tagged_posts = BlogPage.get_posts_by_tag('django', limit=10)- `author` - Post author name (indexed)

- `author_bio` - Optional author biography override

# Get featured posts  - `date` - Publication date (indexed)

featured = BlogPage.get_featured_posts(limit=3)- `intro` - Brief excerpt (250 chars max, indexed)

```- `featured_image` - Featured image with caption

- `body` - StreamField with content blocks

### ✅ Automatic Reading Time- `tags` - Tag system for categorization

Calculates based on 200 words/minute standard.- `featured` - Boolean flag for featured posts (indexed)

- `show_author_bio` - Toggle author bio display

### ✅ Database Optimization- `show_related_posts` - Toggle related posts display

- Indexed fields: `author`, `date`, `intro`, `featured`- `estimated_reading_time` - Auto-calculated reading time

- Efficient QuerySet usage

- Search indexing with Wagtail**StreamField Blocks (from core):**

- `BaseHeadingBlock` - Configurable headings (h1-h6)

### ✅ SEO Optimization- `BaseRichTextBlock` - Rich text with alignment

- Date-based URLs: `/YYYY/MM/DD/slug/`- `BaseImageBlock` - Images with captions

- Full search indexing- `BaseQuoteBlock` - Blockquotes with attribution

- Rich snippets support- `BaseButtonBlock` - CTA buttons

- Inherited SEO fields from `BasePage`- `BaseSpacerBlock` - Vertical spacing

- `BaseCallToActionBlock` - Engagement sections

## Templates

**Parent/Subpage Rules:**

All extend `core/base.html`:- Can only be created under `BlogIndexPage`

- Cannot have child pages

- `blog_page.html` - Individual post display

- `blog_index_page.html` - Post listing/archive### 2. Tag System

- `blog_listing.html` - Alternative listing view

- `blog_archive.html` - Date-based archive**BlogPageTag Model:**

- `includes/post_card.html` - Reusable post card- Uses django-taggit for flexible tagging

- `includes/post_list_item.html` - Compact list item- Enables filtering and categorization

- Allows discovering related content

## File Structure

### 3. Template Structure

```

blog/#### Main Templates

├── models.py              # BlogPage and BlogPageTag

├── templates/blog/        # All blog templates**blog_index_page.html:**

├── templatetags/          # Custom template tags- Extends `core/base.html`

└── migrations/            # Database migrations- Displays featured posts section

```- Shows all posts in selected layout (list/grid/masonry)

- Includes sidebar with tag filter

## Related Documentation- Pagination controls

- Responsive design with Tailwind CSS

- [Core App README](../core/README.md) - Base components

- [Architecture Documentation](../documentation/ARCHITECTURE.md)**blog_page.html:**

- [Wagtail Documentation](https://docs.wagtail.org/)- Extends `core/base.html`

- Breadcrumb navigation

---- Post header with metadata (author, date, reading time)

- Featured image display

**Last Updated**: October 20, 2025- Post introduction

- StreamField content rendering
- Author bio section
- Post navigation (prev/next)
- Sidebar with share buttons and related posts
- Responsive layout

#### Include Templates

**includes/post_card.html:**
- Reusable post card component
- Used in grid and masonry layouts
- Shows featured badge, image, title, excerpt, meta, and tags
- Hover effects and transitions

**includes/post_list_item.html:**
- Reusable list item component
- Used in list layout
- Horizontal layout with thumbnail and content
- Tag links for filtering

## Templates Documentation

All blog templates extend [`core/base.html`](../core/templates/core/base.html:1) for consistency.

### Main Templates

#### blog_page.html
**Location**: [`blog/templates/blog/blog_page.html`](blog/templates/blog/blog_page.html:1)

Individual blog post display with full content.

**Features:**
- Breadcrumb navigation
- Post header with featured image
- Post metadata (author, date, reading time)
- Full StreamField content rendering
- Author bio section (optional)
- Post navigation (previous/next)
- Related posts sidebar
- Social sharing buttons
- Responsive layout

#### blog_index_page.html
**Location**: [`blog/templates/blog/blog_index_page.html`](blog/templates/blog/blog_index_page.html:1)

Main blog listing page with featured posts and filtering.

**Features:**
- Featured posts section at top
- Multiple layout options (list/grid/masonry)
- Tag filtering via sidebar
- Pagination controls
- Responsive grid layouts
- Loading skeletons for better UX

#### blog_listing.html
**Location**: [`blog/templates/blog/blog_listing.html`](blog/templates/blog/blog_listing.html:1)

Alternative blog listing with view mode switching.

**Features:**
- View mode toggle (list/grid/masonry)
- Persistent view preference
- Same filtering capabilities as index
- Optimized for different content densities

#### blog_archive.html
**Location**: [`blog/templates/blog/blog_archive.html`](blog/templates/blog/blog_archive.html:1)

Date-based archive view for posts.

**Features:**
- Date-filtered post display
- Archive navigation
- SEO-optimized meta tags

### Include Templates

#### post_card.html
**Location**: [`blog/templates/blog/includes/post_card.html`](blog/templates/blog/includes/post_card.html:1)

Reusable post card component for grid/masonry layouts.

**Enhanced Features (Frontend Revamp):**
- ✅ Enforced aspect-video ratio for images (16:9)
- ✅ Smooth hover effects with shadow transitions
- ✅ Featured badge with prominent styling
- ✅ Image zoom effect on hover (scale-105)
- ✅ Card lift animation (hover:-translate-y-1)
- ✅ Improved visual hierarchy with better spacing
- ✅ Enhanced typography with line clamping
- ✅ Accessibility improvements (ARIA labels)
- ✅ Touch-friendly design for mobile

**DaisyUI Components:**
- `card` with shadow-md and hover:shadow-xl
- `badge badge-primary` for featured posts
- Responsive image with aspect-video

**Usage:**
```django
{% include "blog/includes/post_card.html" with post=post %}
```

#### post_list_item.html
**Location**: [`blog/templates/blog/includes/post_list_item.html`](blog/templates/blog/includes/post_list_item.html:1)

Compact horizontal layout for list views.

**Enhanced Features (Frontend Revamp):**
- ✅ Responsive layout (stacks on mobile, horizontal on desktop)
- ✅ Better content truncation with line-clamp
- ✅ Improved metadata display
- ✅ Enhanced hover states with smooth transitions
- ✅ Tag links with hover effects
- ✅ Optimized mobile experience
- ✅ Better visual separation between items
- ✅ Accessibility enhancements

**DaisyUI Components:**
- `card card-side` for horizontal layout
- Responsive breakpoints (md:flex-row)
- Badge tags with hover effects

**Usage:**
```django
{% include "blog/includes/post_list_item.html" with post=post %}
```

### Loading Skeleton Components (NEW - Frontend Revamp)

Added loading skeletons for better perceived performance during content loading.

#### post_card_skeleton.html
**Location**: [`blog/templates/blog/includes/post_card_skeleton.html`](blog/templates/blog/includes/post_card_skeleton.html:1)

Loading skeleton matching post_card.html structure.

**Features:**
- Matches card aspect ratios perfectly
- Skeleton image placeholder with aspect-video
- Title, meta, and content skeleton lines
- Tag placeholder skeletons
- ARIA busy state for accessibility
- Smooth pulsing animations
- Matches exact spacing of real cards

**DaisyUI Components:**
- `skeleton` utility class
- `card` structure matching post_card
- `aspect-video` for image skeleton

**Usage:**
```django
{% include "blog/includes/post_card_skeleton.html" %}
```

**Use Case:**
Display while posts are loading or during dynamic content updates to improve perceived performance.

#### post_list_item_skeleton.html
**Location**: [`blog/templates/blog/includes/post_list_item_skeleton.html`](blog/templates/blog/includes/post_list_item_skeleton.html:1)

Loading skeleton matching post_list_item.html structure.

**Features:**
- Responsive skeleton (stacks on mobile, horizontal on desktop)
- Matches list item proportions exactly
- Image skeleton with proper sizing
- Content skeleton with varying line widths
- ARIA busy states for screen readers
- Smooth loading animations
- Mobile-optimized skeleton display

**DaisyUI Components:**
- `skeleton` utility class
- `card card-side` responsive layout
- Breakpoint-aware sizing (md:w-64, md:h-48)

**Usage:**
```django
{% include "blog/includes/post_list_item_skeleton.html" %}
```

**Use Case:**
Display in list view while content is loading to maintain layout stability and provide visual feedback.

### Template File Structure

```
blog/templates/blog/
├── blog_archive.html           # Date-based archive
├── blog_index_page.html        # Main blog listing
├── blog_listing.html           # Alternative listing
├── blog_page.html              # Individual post
├── blocks/                     # StreamField block templates
└── includes/                   # Reusable components
    ├── post_card.html          # Enhanced card component
    ├── post_card_skeleton.html # NEW: Card loading skeleton
    ├── post_list_item.html     # Enhanced list item
    ├── post_list_item_skeleton.html # NEW: List item loading skeleton
    ├── post_meta.html          # Post metadata
    └── post_tags.html          # Tag display
```


## Configuration

### Admin Interface

The blog uses Wagtail's ModelAdmin to provide a dedicated admin interface:

**Features:**
- List view with columns: title, author, date, featured status
- Filtering by: featured, live status, date, author
- Search by: title, intro, author
- Ordered by date (newest first)

### Search Integration

Blog posts are fully indexed for Wagtail's search functionality:

**Indexed Fields:**
- `intro` - Post excerpt
- `body` - Full content
- `author` - Author name
- `date` - Publication date (filter)
- `featured` - Featured status (filter)

### SEO Integration

BlogPage extends `BasePage` from core, inheriting:
- `meta_description` - SEO meta description
- `meta_keywords` - SEO keywords
- `og_title` - Open Graph title
- `og_description` - Open Graph description
- `og_image` - Social sharing image

## Usage

### Creating a Blog

1. **Create BlogIndexPage:**
   - Go to Wagtail Admin → Pages
   - Under HomePage, add child page
   - Select "Blog Index Page"
   - Configure display settings
   - Publish

2. **Create Blog Posts:**
   - Under the Blog Index Page, add child page
   - Select "Blog Post"
   - Fill in required fields (title, author, date, intro)
   - Add featured image (optional)
   - Use StreamField to build content
   - Add tags for categorization
   - Configure display options
   - Publish

### Featured Posts

To feature a post:
1. Edit the blog post
2. Go to Settings tab
3. Check "Featured" checkbox
4. Save and publish

Featured posts appear:
- At the top of the blog index (if enabled)
- With a special "Featured" badge

### Tag Filtering

Tags automatically create filters:
- Click a tag on any post
- URL updates with `?tag=tagname`
- Blog index shows only posts with that tag
- Sidebar highlights current tag

### Layout Options

BlogIndexPage supports three layouts:
1. **List View**: Horizontal cards with thumbnails
2. **Grid View**: Card grid (2 columns on desktop)
3. **Masonry Grid**: Pinterest-style layout

Change via admin: Edit BlogIndexPage → Layout Style

## Integration with Home App

The blog integrates with the home application through:

1. **BaseRecentPostsBlock**: Home page can display recent blog posts
2. **Shared Base**: Both extend `core.models.BasePage`
3. **Consistent Styling**: Both use Tailwind CSS and DaisyUI
4. **Navigation**: Header includes link to blog

### Displaying Recent Posts on Homepage

Use `BaseRecentPostsBlock` in HomePage StreamField:
- Automatically fetches latest blog posts
- Configurable count and display options
- Multiple layout styles available

## Testing

The blog includes comprehensive tests:

**Model Tests:**
- Page creation and hierarchy validation
- Field validation (intro length, reading time)
- Parent/child page rules
- Max count restrictions
- String representations

**Context Tests:**
- Pagination functionality
- Featured posts display
- Tag filtering
- Related posts logic

**Template Tests:**
- Template rendering
- Content display
- Error handling

Run tests:
```bash
python manage.py test blog
```

## Performance Optimizations

**Database Indexes:**
- `author` - Indexed for filtering
- `date` - Indexed for sorting
- `intro` - Indexed for search
- `featured` - Indexed for filtering
- Boolean display fields indexed

**Query Optimization:**
- `.live().public()` filters for published content
- `.select_related()` for foreign keys (where applicable)
- Pagination prevents loading all posts at once

## Logging

The blog uses Python's logging module:

**Logged Events:**
- BlogPage save operations with reading time
- BlogIndexPage context generation with post counts

Access logs in development console or configure handlers for production.

## Best Practices

### Content Creation

1. **Intro Field**: Keep under 250 characters (enforced)
2. **Featured Image**: Use high-quality images (1200x600+ recommended)
3. **Tags**: Use consistent, lowercase tags
4. **SEO**: Fill meta_description and meta_keywords
5. **Reading Time**: Auto-calculated, but verify accuracy

### Organization

1. **One Blog Index**: Maintain single BlogIndexPage
2. **Consistent Authoring**: Use standard author name
3. **Regular Publishing**: Set realistic publication dates
4. **Tag Strategy**: Develop tag taxonomy (5-10 main tags)

### Performance

1. **Image Optimization**: Compress images before upload
2. **StreamField**: Don't overuse blocks in single post
3. **Pagination**: Keep posts_per_page reasonable (10-20)
4. **Featured Posts**: Limit featured_posts_count (2-4)

## Future Enhancements

Potential additions:
- Comment system integration
- Social media sharing with counters
- Newsletter signup
- RSS feed generation
- Archive views (by month/year)
- Author pages (multiple authors)
- Series/collections of posts
- Estimated reading time visualization

## Dependencies

- **Django**: Web framework
- **Wagtail**: CMS functionality
- **django-taggit**: Tagging system
- **modelcluster**: Wagtail model clustering
- **Pillow**: Image handling
- **TailwindCSS**: Styling (via django-tailwind)
- **DaisyUI**: Component library

## Related Documentation

- [Core App README](../core/README.md) - Base blocks and models
- [Home App README](../home/README.md) - Homepage integration
- [Wagtail Documentation](https://docs.wagtail.org/) - CMS features
- [Django Taggit](https://django-taggit.readthedocs.io/) - Tagging system

## Troubleshooting

### Common Issues

**Blog Index Not Appearing:**
- Ensure BlogIndexPage is published
- Check it's child of HomePage
- Verify URL routing in Wagtail

**Posts Not Showing:**
- Confirm posts are published (not draft)
- Check posts are children of BlogIndexPage
- Verify date is not in future

**Tags Not Working:**
- Ensure django-taggit is installed
- Run migrations: `python manage.py migrate`
- Check tag names are consistent

**Images Not Loading:**
- Verify MEDIA_URL and MEDIA_ROOT in settings
- Check image files exist in media directory
- Ensure image renditions are generated

## Changelog
### Frontend Revamp (November 3, 2025)
- ✅ Enhanced post_card.html with hover effects and animations
- ✅ Enhanced post_list_item.html with responsive improvements
- ✅ Created post_card_skeleton.html for loading states
- ✅ Created post_list_item_skeleton.html for loading states
- ✅ Improved image aspect ratios (enforced 16:9)
- ✅ Added smooth transitions and hover effects
- ✅ Enhanced mobile responsiveness and touch targets
- ✅ Improved visual hierarchy and spacing
- ✅ Added accessibility improvements (ARIA labels)
- ✅ Optimized for perceived performance with skeletons


### Version 1.1.0 (October 2025)
- ✅ Removed MockPage hack from all archive views
- ✅ Simplified views to use `seo_meta` dictionary instead of fake page objects
- ✅ Updated templates to support both Wagtail pages and archive views
- ✅ Improved SEO meta template to handle multiple context types
- ✅ Fixed VariableDoesNotExist errors on blog listing and archive pages

### Version 1.0.0 (Initial Release)
- BlogIndexPage with pagination and filtering
- BlogPage with StreamField content
- Tag system integration
- Featured posts functionality
- Reading time calculation
- Related posts display
- Responsive templates with Tailwind CSS
- Comprehensive test coverage
- Production-grade validation and logging
