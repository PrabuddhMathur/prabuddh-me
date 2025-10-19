# Blog View Modes Guide

## Available View Modes

### 1. Grid - 2 Columns (Default)
- **URL Parameter:** `?view=grid-2`
- **Session Key:** `blog_view_mode='grid-2'`
- **Layout:** 2 columns on desktop, 1 on mobile
- **Posts per page:** 12
- **CSS Classes:** `grid grid-cols-1 md:grid-cols-2 gap-6`
- **Best for:** Balanced view with good image visibility

### 2. Grid - 3 Columns
- **URL Parameter:** `?view=grid-3`
- **Session Key:** `blog_view_mode='grid-3'`
- **Layout:** 3 columns on large screens, 2 on tablet, 1 on mobile
- **Posts per page:** 12
- **CSS Classes:** `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`
- **Best for:** Maximum posts visible, compact layout

### 3. Masonry Grid
- **URL Parameter:** `?view=masonry`
- **Session Key:** `blog_view_mode='masonry'`
- **Layout:** CSS columns (3 on desktop, 2 on tablet, 1 on mobile)
- **Posts per page:** 12
- **CSS Classes:** `columns-1 md:columns-2 lg:columns-3 gap-6`
- **Special:** Uses `break-inside-avoid` for each card
- **Best for:** Pinterest-style varied height layout

### 4. List View
- **URL Parameter:** `?view=list`
- **Session Key:** `blog_view_mode='list'`
- **Layout:** Single column, horizontal cards
- **Posts per page:** 10
- **CSS Classes:** `space-y-6`
- **Best for:** Detailed view with more text visible

## Implementation Details

### Session Storage
```python
# Get current view mode
view_mode = request.session.get('blog_view_mode', 'grid-2')

# Update view mode
if 'view' in request.GET:
    view_mode = request.GET.get('view')
    request.session['blog_view_mode'] = view_mode
```

### Toggle Buttons
```html
<div class="join">
    <a href="?view=grid-2" class="btn btn-sm join-item {% if view_mode == 'grid-2' %}btn-primary{% endif %}">
        <!-- 2 Column Icon -->
    </a>
    <!-- ... more buttons ... -->
</div>
```

### Template Conditionals
```django
{% if view_mode == 'grid-2' %}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {% for post in posts %}
            {% include "blog/includes/post_card.html" %}
        {% endfor %}
    </div>
{% elif view_mode == 'grid-3' %}
    <!-- 3 column layout -->
{% elif view_mode == 'masonry' %}
    <!-- Masonry layout -->
{% else %}
    <!-- List view -->
{% endif %}
```

## Icon Usage

Each view mode has a unique icon:

1. **2 Column:** 2x2 grid icon (`M4 6a2 2 0 012-2h2...`)
2. **3 Column:** 3x3 grid icon (`M4 5a1 1 0 011-1h4...`)
3. **Masonry:** Varied height blocks (`M4 5a1 1 0 011-1h4...`)
4. **List:** Horizontal lines (`M4 6h16M4 12h16...`)

## Pagination Handling

Preserve view mode in pagination:
```django
{% if posts.has_next %}
    <a href="?page={{ posts.next_page_number }}{% if view_mode != 'grid-2' %}&view={{ view_mode }}{% endif %}">
        Next »
    </a>
{% endif %}
```

## Responsive Breakpoints

- **Mobile (default):** All views show 1 column
- **Tablet (md: 768px+):** 2 columns for grid-2, grid-3, masonry
- **Desktop (lg: 1024px+):** Full 3 columns for grid-3 and masonry

## Component Reuse

All view modes use the same components:
- `blog/includes/post_card.html` - For grid and masonry
- `blog/includes/post_list_item.html` - For list view

This ensures consistency in:
- Post metadata display
- Author/tag links
- Image rendering
- Featured badge
- Read more buttons

## Performance Notes

1. **Masonry CSS vs JS:** Using pure CSS `columns` instead of JavaScript for better performance
2. **Session storage:** Minimal server-side storage, no database overhead
3. **Pagination:** Adjusts posts per page based on view density
4. **Lazy loading:** Can be added to images in future for better performance

## Browser Support

- **Grid layouts:** All modern browsers (IE11+ with autoprefixer)
- **CSS Columns (Masonry):** All modern browsers
- **Session storage:** Universal server-side support

## Accessibility

- Icons have `title` attributes for tooltips
- Active state clearly visible with `btn-primary` class
- Keyboard navigable (native button behavior)
- Screen reader friendly (semantic HTML)
