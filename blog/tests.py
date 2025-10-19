from django.test import TestCase
from django.core.exceptions import ValidationError
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTests
from home.models import HomePage
from .models import BlogPage
import datetime


# =====================================================
# Model Tests
# =====================================================


class BlogPageTests(WagtailPageTests):
    """Test cases for BlogPage model."""
    
    def setUp(self):
        """Set up test data."""
        from wagtail.models import Site, Page
        
        # Get root page and set up site
        self.root_page = Page.objects.get(id=1)
        
        # Create or get the default site
        self.site = Site.objects.filter(is_default_site=True).first()
        if not self.site:
            self.site = Site.objects.create(
                hostname='localhost',
                port=80,
                root_page=self.root_page,
                is_default_site=True,
                site_name='Test Site'
            )
        
        self.home_page = HomePage(
            title="Test Home",
            slug="test-home",
        )
        self.root_page.add_child(instance=self.home_page)
        
        # Make home page the site root for proper URL generation
        self.site.root_page = self.home_page
        self.site.save()
    
    def test_can_create_blog_page(self):
        """Test that a BlogPage can be created under HomePage."""
        self.assertCanCreateAt(HomePage, BlogPage)
    
    def test_blog_page_parent_pages(self):
        """Test BlogPage parent page types."""
        self.assertAllowedParentPageTypes(
            BlogPage,
            {HomePage}
        )
    
    def test_blog_page_cannot_have_subpages(self):
        """Test BlogPage cannot have subpages."""
        self.assertAllowedSubpageTypes(BlogPage, {})
    
    def test_blog_page_str(self):
        """Test BlogPage string representation."""
        blog_post = BlogPage(title="My First Post")
        self.assertEqual(str(blog_post), "My First Post")
    
    def test_blog_page_reading_time_calculation(self):
        """Test automatic reading time calculation."""
        blog_post = BlogPage(
            title="Test Post",
            slug="test-post",
            author="Test Author",
            date=datetime.date.today(),
            intro="This is a short intro.",  # Short intro to stay under 250 chars
        )
        self.home_page.add_child(instance=blog_post)
        
        # Reading time should be calculated
        self.assertGreater(blog_post.estimated_reading_time, 0)
    
    def test_blog_page_intro_validation(self):
        """Test intro field character limit validation."""
        blog_post = BlogPage(
            title="Test Post",
            slug="test-post",
            author="Test Author",
            date=datetime.date.today(),
            intro="x" * 300,  # Exceeds 250 character limit
        )
        
        with self.assertRaises(ValidationError):
            blog_post.clean()
    
    def test_blog_page_featured_flag(self):
        """Test featured flag functionality."""
        blog_post = BlogPage(
            title="Featured Post",
            slug="featured-post",
            author="Test Author",
            date=datetime.date.today(),
            intro="This is a featured post.",
            featured=True,
        )
        self.home_page.add_child(instance=blog_post)
        
        self.assertTrue(blog_post.featured)
    
    def test_blog_page_date_based_url(self):
        """Test that BlogPage generates date-based URLs."""
        test_date = datetime.date(2025, 10, 19)
        blog_post = BlogPage(
            title="Test Post",
            slug="test-post",
            author="Test Author",
            date=test_date,
            intro="This is a test post.",
        )
        self.home_page.add_child(instance=blog_post)
        
        url_parts = blog_post.get_url_parts()
        self.assertIsNotNone(url_parts)
        site_id, root_url, page_path = url_parts
        self.assertEqual(page_path, "2025/10/19/test-post/")


# =====================================================
# Context Tests
# =====================================================

class BlogArchiveViewTests(TestCase):
    """Test suite for blog archive views."""
    
    def setUp(self):
        """Set up test data."""
        # Get root page and set up site
        self.root_page = Page.objects.get(id=1)
        
        # Create or get the default site
        self.site = Site.objects.filter(is_default_site=True).first()
        if not self.site:
            self.site = Site.objects.create(
                hostname='localhost',
                port=80,
                root_page=self.root_page,
                is_default_site=True,
                site_name='Test Site'
            )
        
        self.home_page = HomePage(
            title="Test Home",
            slug="test-home",
        )
        self.root_page.add_child(instance=self.home_page)
        
        # Create test blog posts
        for i in range(5):
            blog_post = BlogPage(
                title=f"Post {i}",
                slug=f"post-{i}",
                author="Test Author",
                date=datetime.date(2025, 10, 19),
                intro=f"Intro for post {i}",
            )
            self.home_page.add_child(instance=blog_post)
    
    def test_year_archive_view(self):
        """Test that year archive view works."""
        response = self.client.get('/2025/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('posts', response.context)
        self.assertEqual(len(response.context['posts']), 5)
    
    def test_month_archive_view(self):
        """Test that month archive view works."""
        response = self.client.get('/2025/10/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('posts', response.context)
        self.assertEqual(len(response.context['posts']), 5)
    
    def test_day_archive_view(self):
        """Test that day archive view works."""
        response = self.client.get('/2025/10/19/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('posts', response.context)
        self.assertEqual(len(response.context['posts']), 5)


# =====================================================
# Template Tests
# =====================================================

class BlogTemplateTests(TestCase):
    """Test suite for blog templates."""
    
    def setUp(self):
        """Set up test data."""
        self.root_page = Page.objects.get(id=1)
        
        # Create or get the default site
        site = Site.objects.filter(is_default_site=True).first()
        if not site:
            site = Site.objects.create(
                hostname='localhost',
                port=80,
                root_page=self.root_page,
                is_default_site=True,
                site_name='Test Site'
            )
        
        self.home_page = HomePage(
            title="Test Home For Blog",
            slug="test-home-blog",
        )
        self.root_page.add_child(instance=self.home_page)
        
        site.root_page = self.home_page
        site.save()
        
        self.blog_post = BlogPage(
            title="Test Post",
            slug="test-post",
            author="Test Author",
            date=datetime.date.today(),
            intro="Test intro",
        )
        self.home_page.add_child(instance=self.blog_post)
    
    def test_blog_page_renders(self):
        """Test that BlogPage template renders without errors."""
        # Construct the date-based URL manually
        url = f"/{self.blog_post.date.year}/{self.blog_post.date.month:02d}/{self.blog_post.date.day:02d}/{self.blog_post.slug}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Post")
        self.assertContains(response, "Test Author")
