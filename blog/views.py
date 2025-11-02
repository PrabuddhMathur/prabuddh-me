"""
Views for the blog application.
"""
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from taggit.models import Tag
from .models import BlogPage


def blog_listing(request):
    """
    Main blog listing page showing all posts with grid view options.
    """
    # Get view preference from session (default to 'grid-2')
    view_mode = request.session.get('blog_view_mode', 'grid-2')
    
    # Update view mode if requested
    if 'view' in request.GET:
        view_mode = request.GET.get('view')
        request.session['blog_view_mode'] = view_mode
    
    # Get all published blog posts
    # Performance: Use select_related('owner') to avoid N+1 queries when accessing post authors
    posts = BlogPage.objects.live().public().select_related('owner').order_by('-date')
    
    # Paginate results
    posts_per_page = 12 if 'grid' in view_mode else 10
    paginator = Paginator(posts, posts_per_page)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    
    # SEO metadata
    seo_meta = {
        'title': 'Blog - All Posts',
        'description': 'Browse all blog posts',
    }
    
    return render(request, 'blog/blog_listing.html', {
        'seo_meta': seo_meta,
        'posts': posts_page,
        'paginator': paginator,
        'view_mode': view_mode,
    })


def blog_author_archive(request, author_slug):
    """
    Redirect to blog listing since there's only one author.
    Kept for backwards compatibility with old URLs.
    """
    from django.shortcuts import redirect
    return redirect('blog_listing')


def blog_tag_archive(request, tag_slug):
    """
    View function for displaying all posts with a specific tag.
    """
    # Get the tag
    tag = get_object_or_404(Tag, slug=tag_slug)
    
    # Get all published blog posts with this tag
    # Performance: Use select_related('owner') to avoid N+1 queries when accessing post authors
    posts = BlogPage.objects.live().public().filter(
        tags__slug=tag_slug
    ).select_related('owner').order_by('-date')
    
    # Paginate results
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    
    # SEO metadata
    seo_meta = {
        'title': f'Posts tagged "{tag.name}"',
        'description': f'All blog posts tagged with {tag.name}',
    }
    
    return render(request, 'blog/blog_archive.html', {
        'seo_meta': seo_meta,
        'posts': posts_page,
        'paginator': paginator,
        'archive_type': 'tag',
        'tag': tag,
    })


def blog_post_detail(request, year, month, day, slug):
    """
    View function for displaying an individual blog post by date and slug.
    """
    # Get the blog post
    post = get_object_or_404(
        BlogPage.objects.live().public(),
        date__year=year,
        date__month=month,
        date__day=day,
        slug=slug
    )
    
    # Use Wagtail's serve method to render the page
    return post.serve(request)


def blog_year_archive(request, year):
    """
    View function for displaying blog posts from a specific year.
    """
    # Get all published blog posts for the year
    # Performance: Use select_related('owner') to avoid N+1 queries when accessing post authors
    posts = BlogPage.objects.live().public().filter(
        date__year=year
    ).select_related('owner').order_by('-date')
    
    # Paginate results
    paginator = Paginator(posts, 10)  # 10 posts per page
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    
    # SEO metadata
    seo_meta = {
        'title': f'Blog Archive - {year}',
        'description': f'Blog posts from {year}',
    }
    
    return render(request, 'blog/blog_archive.html', {
        'seo_meta': seo_meta,
        'posts': posts_page,
        'paginator': paginator,
        'year': year,
        'archive_type': 'year',
    })


def blog_month_archive(request, year, month):
    """
    View function for displaying blog posts from a specific month.
    """
    from datetime import date
    
    # Get all published blog posts for the month
    # Performance: Use select_related('owner') to avoid N+1 queries when accessing post authors
    posts = BlogPage.objects.live().public().filter(
        date__year=year,
        date__month=month
    ).select_related('owner').order_by('-date')
    
    # Paginate results
    paginator = Paginator(posts, 10)  # 10 posts per page
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    
    # Create month name
    month_date = date(year, month, 1)
    month_name = month_date.strftime('%B')
    
    # SEO metadata
    seo_meta = {
        'title': f'Blog Archive - {month_name} {year}',
        'description': f'Blog posts from {month_name} {year}',
    }
    
    return render(request, 'blog/blog_archive.html', {
        'seo_meta': seo_meta,
        'posts': posts_page,
        'paginator': paginator,
        'year': year,
        'month': month,
        'month_name': month_name,
        'archive_type': 'month',
    })


def blog_day_archive(request, year, month, day):
    """
    View function for displaying blog posts from a specific day.
    """
    from datetime import date
    
    # Get all published blog posts for the day
    # Performance: Use select_related('owner') to avoid N+1 queries when accessing post authors
    posts = BlogPage.objects.live().public().filter(
        date__year=year,
        date__month=month,
        date__day=day
    ).select_related('owner').order_by('-date')
    
    # Paginate results
    paginator = Paginator(posts, 10)  # 10 posts per page
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    
    # Create date string
    archive_date = date(year, month, day)
    date_string = archive_date.strftime('%B %d, %Y')
    month_name = archive_date.strftime('%B')
    
    # SEO metadata
    seo_meta = {
        'title': f'Blog Archive - {date_string}',
        'description': f'Blog posts from {date_string}',
    }
    
    return render(request, 'blog/blog_archive.html', {
        'seo_meta': seo_meta,
        'posts': posts_page,
        'paginator': paginator,
        'year': year,
        'month': month,
        'month_name': month_name,
        'day': day,
        'archive_type': 'day',
    })
