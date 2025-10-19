from django.urls import reverse
from django.core.exceptions import ValidationError
from home.models import HomePage

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase
from wagtail.images.tests.utils import Image, get_test_image_file


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        """Test that root page exists."""
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)
        self.assertEqual(root_page.title, "Root")

    def test_homepage_create(self):
        """Test creating a homepage instance."""
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(
            title="Home",
            hero_title="Welcome",
            hero_subtitle="To our site"
        )
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())
    
    def test_homepage_can_be_created_under_root(self):
        """Test that HomePage can be created as a child of root."""
        root_page = Page.objects.get(pk=1)
        self.assertCanCreateAt(Page, HomePage)


class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """
        Create a homepage instance for testing.
        """
        # Get default site and root page
        self.site = Site.objects.get(is_default_site=True)
        root_page = self.site.root_page
        
        self.homepage = HomePage(
            title="Test Home",
            slug="test-home",
            hero_title="Welcome to My Site",
            hero_subtitle="A great place to visit",
            author_name="Test Author",
            number_of_featured_posts=3,
            number_of_recent_posts=5,
        )
        root_page.add_child(instance=self.homepage)
        revision = self.homepage.save_revision()
        revision.publish()

    def test_homepage_status_code(self):
        """Test that homepage returns 200 status code."""
        url = self.homepage.url
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_homepage_template_used(self):
        """Test that correct template is used."""
        url = self.homepage.url
        response = self.client.get(url)
        self.assertTemplateUsed(response, "home/home_page.html")
    
    def test_homepage_context_has_social_links(self):
        """Test that homepage context includes social links."""
        self.homepage.twitter_url = "https://twitter.com/test"
        self.homepage.github_url = "https://github.com/test"
        revision = self.homepage.save_revision()
        revision.publish()
        
        url = self.homepage.url
        response = self.client.get(url)
        self.assertIn('social_links', response.context)
        self.assertEqual(
            response.context['social_links']['twitter'],
            "https://twitter.com/test"
        )
    
    def test_homepage_context_has_empty_posts_without_blog(self):
        """Test that homepage gracefully handles missing blog app."""
        url = self.homepage.url
        response = self.client.get(url)
        # Should have empty lists when blog app doesn't exist
        self.assertIn('recent_posts', response.context)
        self.assertIn('featured_posts', response.context)
        self.assertEqual(len(response.context['recent_posts']), 0)
        self.assertEqual(len(response.context['featured_posts']), 0)
    
    def test_homepage_str_representation(self):
        """Test string representation of HomePage."""
        self.assertEqual(str(self.homepage), "Test Home")
    
    def test_get_social_links_list_method(self):
        """Test get_social_links_list helper method."""
        self.homepage.website_url = "https://example.com"
        self.homepage.twitter_url = "https://twitter.com/test"
        self.homepage.email_address = "test@example.com"
        revision = self.homepage.save_revision()
        revision.publish()
        
        links = self.homepage.get_social_links_list()
        self.assertEqual(len(links), 3)
        # Check that each link is a tuple with correct structure
        for link in links:
            self.assertEqual(len(link), 4)  # (id, name, url, icon)


class HomePageValidationTests(WagtailPageTestCase):
    """
    Tests for HomePage model validation.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.root_page = Page.objects.get(pk=1)
    
    def test_negative_featured_posts_raises_validation_error(self):
        """Test that negative featured posts count is invalid."""
        homepage = HomePage(
            title="Test Home",
            number_of_featured_posts=-1
        )
        
        with self.assertRaises(ValidationError) as context:
            homepage.clean()
        
        self.assertIn('number_of_featured_posts', context.exception.message_dict)
    
    def test_excessive_featured_posts_raises_validation_error(self):
        """Test that too many featured posts count is invalid."""
        homepage = HomePage(
            title="Test Home",
            number_of_featured_posts=25
        )
        
        with self.assertRaises(ValidationError) as context:
            homepage.clean()
        
        self.assertIn('number_of_featured_posts', context.exception.message_dict)
    
    def test_negative_recent_posts_raises_validation_error(self):
        """Test that negative recent posts count is invalid."""
        homepage = HomePage(
            title="Test Home",
            number_of_recent_posts=-1
        )
        
        with self.assertRaises(ValidationError) as context:
            homepage.clean()
        
        self.assertIn('number_of_recent_posts', context.exception.message_dict)
    
    def test_excessive_recent_posts_raises_validation_error(self):
        """Test that too many recent posts count is invalid."""
        homepage = HomePage(
            title="Test Home",
            number_of_recent_posts=100
        )
        
        with self.assertRaises(ValidationError) as context:
            homepage.clean()
        
        self.assertIn('number_of_recent_posts', context.exception.message_dict)
    
    def test_cta_link_required_when_text_provided(self):
        """Test that CTA link is required when CTA text is provided."""
        homepage = HomePage(
            title="Test Home",
            hero_cta_text="Click Me",
            hero_cta_link=""  # Empty link with text should fail
        )
        
        with self.assertRaises(ValidationError) as context:
            homepage.clean()
        
        self.assertIn('hero_cta_link', context.exception.message_dict)
    
    def test_valid_homepage_passes_validation(self):
        """Test that a valid homepage passes all validation."""
        homepage = HomePage(
            title="Test Home",
            hero_title="Welcome",
            number_of_featured_posts=3,
            number_of_recent_posts=5,
            hero_cta_text="Read More",
            hero_cta_link="https://example.com"
        )
        self.root_page.add_child(instance=homepage)
        
        # Should not raise any validation errors
        try:
            homepage.full_clean()
        except ValidationError:
            self.fail("Valid homepage should not raise ValidationError")


class HomePageMetaTests(WagtailPageTestCase):
    """
    Tests for HomePage Meta class configuration.
    """
    
    def test_homepage_has_correct_verbose_names(self):
        """Test that HomePage has correct verbose names."""
        self.assertEqual(HomePage._meta.verbose_name, "Homepage")
        self.assertEqual(HomePage._meta.verbose_name_plural, "Homepages")
    
    def test_homepage_has_ordering(self):
        """Test that HomePage has ordering configured."""
        self.assertIsNotNone(HomePage._meta.ordering)
        self.assertEqual(HomePage._meta.ordering, ['-first_published_at'])

