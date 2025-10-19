# Architecture Documentation - Prabuddh-Me Blog

## Overview

This document describes the production-ready architecture of the Prabuddh-Me personal blog application built with Django and Wagtail CMS. The architecture follows industry best practices with a **Core-First Approach** to eliminate code duplication and ensure maintainability.

## Table of Contents

1. [Architecture Philosophy](#architecture-philosophy)
2. [Application Structure](#application-structure)
3. [Core-First Approach](#core-first-approach)
4. [Data Flow](#data-flow)
5. [Template Hierarchy](#template-hierarchy)
6. [Production Features](#production-features)
7. [Best Practices](#best-practices)
8. [Scalability](#scalability)

## Architecture Philosophy

### Core Principles

1. **DRY (Don't Repeat Yourself)**: All reusable components defined once in `core`
2. **Single Source of Truth**: Base models, blocks, and templates centralized
3. **Production-Ready**: Built-in error handling, caching, logging, and validation
4. **SEO-First**: Complete SEO optimization at every layer
5. **Performance**: Caching, database optimization, and efficient queries
6. **Maintainability**: Clear separation of concerns and well-documented code

### Design Patterns

- **Template Method Pattern**: `BasePage` defines structure, subclasses implement specifics
- **Composition over Inheritance**: StreamField blocks composed from core components
- **Repository Pattern**: Class methods for common queries
- **Singleton Pattern**: Site-wide settings accessible globally

## Application Structure

```
prabuddh-me/
├── core/               # Foundation layer (SINGLE SOURCE OF TRUTH)
│   ├── models.py      # Base models, blocks, settings
│   └── templates/     # Base templates and blocks
├── blog/              # Blog functionality
│   ├── models.py      # BlogPage (extends BasePage, uses core blocks)
│   └── templates/     # Blog-specific templates (extend core/base.html)
├── home/              # Homepage
│   ├── models.py      # HomePage (extends BasePage, uses core blocks)
│   └── templates/     # Homepage template (extends core/base.html)
├── theme/             # Tailwind CSS configuration
└── prabuddh_me/       # Project settings
    ├── settings/      # Environment-specific settings
    └── urls.py        # URL configuration
```

### Dependency Graph

```
┌─────────────────────────────────────┐
│          Django/Wagtail             │
└────────────┬────────────────────────┘
             │
             ├─────────────────────────┐
             │                         │
        ┌────▼────┐              ┌─────▼─────┐
        │  Core   │              │   Theme   │
        │  (Base) │              │(Tailwind) │
        └────┬────┘              └───────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼────┐
│  Blog  │      │  Home   │
└────────┘      └─────────┘
```

**Key Points:**
- `core` depends only on Django/Wagtail
- `blog` and `home` depend on `core`
- No circular dependencies
- Theme is independent (CSS only)

## Core-First Approach

### What Goes in Core?

**✅ Should be in Core:**
- Reusable StreamField blocks (heading, text, image, hero, etc.)
- Abstract base models (`BasePage`)
- Site-wide settings (header, footer, SEO)
- Base templates (`base.html`)
- Common template includes (header, footer, SEO meta)
- Shared utilities and helpers

**❌ Should NOT be in Core:**
- App-specific models (BlogPage, HomePage)
- App-specific templates (blog_page.html, home_page.html)
- App-specific business logic
- App-specific views

### Example: Adding a New Feature

**Scenario**: Add a video block for embedding videos

**❌ Wrong Approach:**
```python
# blog/models.py
class VideoBlock(blocks.StructBlock):  # DON'T DO THIS
    video_url = URLBlock()
    # ...

# home/models.py
class VideoBlock(blocks.StructBlock):  # DUPLICATION!
    video_url = URLBlock()
    # ...
```

**✅ Correct Approach:**
```python
# core/models.py
class BaseVideoBlock(blocks.StructBlock):  # Define once in core
    video_url = URLBlock()
    # ...

# blog/models.py
from core.models import BaseVideoBlock

body = StreamField([
    ('video', BaseVideoBlock()),  # Import and use
    # ...
])

# home/models.py
from core.models import BaseVideoBlock

body = StreamField([
    ('video', BaseVideoBlock()),  # Reuse same block
    # ...
])
```

### Benefits Realized

**Before Refactoring:**
- ❌ Duplicate block templates in `home/templates/home/blocks/`
- ❌ Inconsistent implementations across apps
- ❌ Changes required in multiple places
- ❌ Higher maintenance burden

**After Refactoring:**
- ✅ Single block templates in `core/templates/core/blocks/`
- ✅ Consistent implementation everywhere
- ✅ Changes in one place automatically propagate
- ✅ Lower maintenance burden
- ✅ Production-ready with error handling

## Data Flow

### Request/Response Cycle

```
1. User Request
   │
   ├─► Django URLConf
   │     │
   │     ├─► Wagtail Routing
   │           │
   │           ├─► Page Model (BlogPage/HomePage)
   │                 │
   │                 ├─► get_context() - Adds data
   │                 │     │
   │                 │     ├─► Query database (with caching)
   │                 │     ├─► Error handling
   │                 │     └─► Return context
   │                 │
   │                 ├─► Template Rendering
   │                       │
   │                       ├─► core/base.html (master)
   │                       │     │
   │                       │     ├─► SEO meta include
   │                       │     ├─► Header include
   │                       │     ├─► Content block
   │                       │     └─► Footer include
   │                       │
   │                       └─► app/template.html (extends base)
   │                             │
   │                             └─► StreamField blocks (from core)
   │
   └─► Response to User
```

### Database Query Flow

```
Model Method Call
   │
   ├─► Check Cache
   │     │
   │     ├─► Cache Hit
   │     │     └─► Return cached data
   │     │
   │     └─► Cache Miss
   │           │
   │           ├─► Query Database
   │           │     │
   │           │     ├─► Apply filters/ordering
   │           │     ├─► Use indexes
   │           │     └─► Return QuerySet
   │           │
   │           ├─► Store in Cache (15 min TTL)
   │           └─► Return data
```

## Template Hierarchy

### Template Structure

```
core/templates/core/
├── base.html                       # MASTER TEMPLATE
│   ├── includes/seo_meta.html     # SEO, OG, Twitter Cards
│   ├── includes/header.html       # Navigation
│   └── includes/footer.html       # Footer
│
├── blocks/                        # StreamField block templates
│   ├── heading_block.html
│   ├── rich_text_block.html
│   ├── image_block.html
│   ├── hero_block.html
│   ├── cta_block.html
│   ├── author_bio_block.html
│   ├── recent_posts_block.html
│   ├── quote_block.html
│   ├── button_block.html
│   └── spacer_block.html

blog/templates/blog/
├── blog_page.html                 # Extends core/base.html
├── blog_index_page.html           # Extends core/base.html
└── includes/
    ├── post_card.html             # Reusable component
    └── post_list_item.html        # Reusable component

home/templates/home/
└── home_page.html                 # Extends core/base.html
```

### Template Inheritance Example

```django
{# core/templates/core/base.html - MASTER #}
<!DOCTYPE html>
<html>
<head>
    {% include "core/includes/seo_meta.html" %}
    <title>{% block title %}{% endblock %}</title>
</head>
<body>
    {% include "core/includes/header.html" %}
    <main>
        {% block content %}{% endblock %}
    </main>
    {% include "core/includes/footer.html" %}
</body>
</html>

{# blog/templates/blog/blog_page.html - EXTENDS #}
{% extends "core/base.html" %}

{% block title %}{{ page.title }}{% endblock %}

{% block content %}
    <article>
        <h1>{{ page.title }}</h1>
        {{ page.body }}  {# StreamField uses core block templates #}
    </article>
{% endblock %}
```

## Production Features

### 1. Error Handling

**Pattern Used Throughout:**
```python
def get_context(self, request):
    context = super().get_context(request)
    
    try:
        # Risky database operation
        posts = BlogPage.objects.filter(...)
        context['posts'] = posts
    except BlogPage.DoesNotExist:
        logger.warning("Blog posts not found")
        context['posts'] = []
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        context['posts'] = []
    
    return context
```

**Benefits:**
- Application doesn't crash on errors
- Graceful degradation
- Errors logged for debugging
- User sees partial content instead of 500 error

### 2. Caching Strategy

**Implementation:**
```python
def get_recent_posts(cls, limit=5):
    cache_key = f'blog_recent_posts_{limit}'
    posts = cache.get(cache_key)
    
    if posts is None:
        posts = cls.objects.live().public()[:limit]
        cache.set(cache_key, posts, 900)  # 15 min TTL
    
    return posts

def save(self, *args, **kwargs):
    # Clear related caches on save
    cache.delete(f'blog_recent_posts_{self.id}')
    super().save(*args, **kwargs)
```

**Cache Strategy:**
- 15-minute TTL for most queries
- Automatic invalidation on model save
- Namespaced cache keys
- Redis backend recommended for production

### 3. Database Optimization

**Indexes Applied:**
```python
class BlogPage(BasePage):
    author = models.CharField(db_index=True)     # Frequently filtered
    date = models.DateField(db_index=True)        # Sorting/filtering
    intro = models.CharField(db_index=True)       # Search
    featured = models.BooleanField(db_index=True) # Filtering
```

**Query Optimization:**
```python
# ✅ Good: Single query with prefetch
posts = BlogPage.objects.prefetch_related('tags').live().public()

# ❌ Bad: N+1 query problem
posts = BlogPage.objects.live().public()
for post in posts:
    post.tags.all()  # Separate query for each post!
```

### 4. Validation

**Multi-Level Validation:**
```python
class BlogPage(BasePage):
    def clean(self):
        """Model-level validation"""
        super().clean()
        
        errors = {}
        
        # Business logic validation
        if self.date > timezone.now().date():
            errors['date'] = ValidationError(
                'Post date cannot be in the future.',
                code='future_date'
            )
        
        if not self.author.strip():
            errors['author'] = ValidationError(
                'Author name is required.',
                code='author_required'
            )
        
        if errors:
            raise ValidationError(errors)
```

### 5. Logging

**Structured Logging:**
```python
import logging
logger = logging.getLogger(__name__)

# Different levels for different situations
logger.debug(f"Cached {limit} recent posts")          # Development
logger.info(f"Saving BlogPage: {self.title}")          # Normal operations
logger.warning(f"Featured image has no caption")       # Potential issues
logger.error(f"Error in get_context: {e}", exc_info=True)  # Errors
```

**Production Configuration:**
```python
# settings/production.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'blog': {'handlers': ['file'], 'level': 'INFO'},
        'core': {'handlers': ['file'], 'level': 'INFO'},
        'home': {'handlers': ['file'], 'level': 'INFO'},
    },
}
```

### 6. SEO Optimization

**Complete SEO Stack:**
```html
<!-- core/includes/seo_meta.html -->
<meta name="description" content="{{ page.meta_description }}">
<meta name="keywords" content="{{ page.meta_keywords }}">

<!-- Open Graph -->
<meta property="og:title" content="{{ page.og_title }}">
<meta property="og:description" content="{{ page.og_description }}">
<meta property="og:image" content="{{ og_image.url }}">
<meta property="og:type" content="website">
<meta property="og:url" content="{{ request.build_absolute_uri }}">

<!-- Twitter Cards -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ page.og_title }}">
<meta name="twitter:description" content="{{ page.og_description }}">
<meta name="twitter:image" content="{{ og_image.url }}">

<!-- Canonical URL -->
<link rel="canonical" href="{{ request.build_absolute_uri }}">

<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={{ ga_id }}"></script>
```

## Best Practices

### Code Organization

**✅ Do:**
- Keep core app focused on reusable components
- Use meaningful class and method names
- Add docstrings to all public methods
- Use type hints where appropriate
- Follow PEP 8 style guide
- Write tests for new functionality

**❌ Don't:**
- Duplicate code across apps
- Put app-specific logic in core
- Create circular dependencies
- Ignore error handling
- Skip validation
- Forget to update documentation

### Performance Guidelines

**✅ Do:**
- Use caching for expensive queries
- Add database indexes strategically
- Use `select_related()` and `prefetch_related()`
- Optimize images before upload
- Lazy load images in templates
- Monitor query performance

**❌ Don't:**
- Query database in loops
- Load all objects when you need a count
- Forget to invalidate caches
- Store large objects in cache
- Over-index (every index has a cost)

### Security Guidelines

**✅ Do:**
- Validate all user input
- Use Django's built-in security features
- Keep dependencies updated
- Use environment variables for secrets
- Enable CSRF protection
- Use HTTPS in production

**❌ Don't:**
- Store passwords in plain text
- Trust user input without validation
- Commit secrets to version control
- Disable Django security features
- Use `safe` filter without sanitization

## Scalability

### Horizontal Scaling

The architecture supports horizontal scaling:

```
Load Balancer
      │
      ├─────────────┬─────────────┐
      │             │             │
  App Server 1  App Server 2  App Server 3
      │             │             │
      └─────────────┴─────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
   Database Server         Cache Server
   (PostgreSQL)              (Redis)
```

**Stateless Design:**
- No session data stored in application servers
- Cache and database are shared
- Static files served from CDN

### Vertical Scaling

**Database:**
- Add connection pooling (`CONN_MAX_AGE`)
- Upgrade PostgreSQL hardware
- Add read replicas for read-heavy operations

**Cache:**
- Upgrade Redis memory
- Add Redis cluster for larger datasets

**Application:**
- Increase worker processes
- Use async/await for I/O operations
- Implement task queue (Celery) for heavy operations

### Future Growth

The architecture is designed to accommodate:

- **Multi-language support**: i18n framework built into Django/Wagtail
- **Multiple authors**: Author model can be extracted to separate app
- **Advanced features**: Newsletter, comments, forums as separate apps
- **API endpoints**: Django REST Framework can be added
- **Mobile apps**: GraphQL API layer can be added

## Migration Guide

### From Old Architecture to Core-First

**Step 1: Identify Duplications**
```bash
# Find duplicate templates
find . -name "*.html" -type f | sort | uniq -d

# Find duplicate block definitions
grep -r "class.*Block" */models.py
```

**Step 2: Move to Core**
```bash
# Move base blocks to core/models.py
# Move base templates to core/templates/core/
```

**Step 3: Update Imports**
```python
# In blog/models.py and home/models.py
from core.models import (
    BaseHeadingBlock,
    BaseRichTextBlock,
    # ... all base blocks
)
```

**Step 4: Remove Duplicates**
```bash
# Remove duplicate templates
rm -rf home/templates/home/blocks/
```

**Step 5: Create Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Step 6: Test**
```bash
python manage.py test
python manage.py check
```

## Conclusion

This architecture provides:

✅ **Maintainability**: Changes in one place, DRY principle  
✅ **Performance**: Caching, database optimization  
✅ **Reliability**: Error handling, logging, validation  
✅ **Scalability**: Stateless design, horizontal scaling ready  
✅ **SEO**: Complete SEO optimization at every layer  
✅ **Security**: Django best practices, input validation  
✅ **Developer Experience**: Clear structure, good documentation  

The Core-First Approach ensures the codebase remains clean, consistent, and production-ready as the application grows.

---

**Version**: 2.0  
**Last Updated**: October 20, 2025  
**Authors**: Prabuddh Mathur
