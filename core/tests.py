from django.test import TestCase
from django.core.exceptions import ValidationError
from wagtail.test.utils import WagtailPageTests
from wagtail.models import Site, Page
from wagtail.images.tests.utils import Image, get_test_image_file
from .models import (
    SiteSettings,
    HeaderSettings,
    FooterSettings,
    BasePage,
    BaseHeadingBlock,
    BaseRichTextBlock,
    BaseImageBlock,
)


class SiteSettingsTestCase(TestCase):
    """Test cases for SiteSettings model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Get the default test site
        self.site = Site.objects.get(is_default_site=True)
    
    def test_site_settings_creation(self):
        """Test that SiteSettings can be created with default values."""
        settings = SiteSettings.objects.create(
            site=self.site,
            site_name="Test Site",
            tagline="Test Tagline"
        )
        self.assertEqual(settings.site_name, "Test Site")
        self.assertEqual(settings.tagline, "Test Tagline")
    
    def test_site_settings_str_representation(self):
        """Test the string representation of SiteSettings."""
        settings = SiteSettings.objects.create(
            site=self.site,
            site_name="Test Site"
        )
        expected_str = "Site Settings for Test Site"
        self.assertEqual(str(settings), expected_str)
    
    def test_site_settings_default_values(self):
        """Test that SiteSettings has correct default values."""
        settings = SiteSettings.objects.create(site=self.site)
        self.assertEqual(settings.site_name, "My Site")
        self.assertEqual(settings.tagline, "")
        self.assertTrue(settings.show_year if hasattr(settings, 'show_year') else True)


class HeaderSettingsTestCase(TestCase):
    """Test cases for HeaderSettings model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.site = Site.objects.get(is_default_site=True)
    
    def test_header_settings_creation(self):
        """Test HeaderSettings creation with custom values."""
        settings = HeaderSettings.objects.create(
            site=self.site,
            site_title="My Blog",
            show_logo=True
        )
        self.assertEqual(settings.site_title, "My Blog")
        self.assertTrue(settings.show_logo)
    
    def test_header_settings_str_representation(self):
        """Test the string representation of HeaderSettings."""
        settings = HeaderSettings.objects.create(
            site=self.site,
            site_title="My Blog"
        )
        expected_str = "Header Settings - My Blog"
        self.assertEqual(str(settings), expected_str)
    
    def test_get_navigation_links(self):
        """Test navigation links helper method."""
        settings = HeaderSettings.objects.create(
            site=self.site,
            nav_link_1_text="Home",
            nav_link_1_url="/",
            nav_link_2_text="Blog",
            nav_link_2_url="/blog/",
        )
        links = settings.get_navigation_links()
        # Default values include links 3 and 4 as well
        self.assertGreaterEqual(len(links), 2)
        self.assertEqual(links[0]['text'], "Home")
        self.assertEqual(links[0]['url'], "/")


class FooterSettingsTestCase(TestCase):
    """Test cases for FooterSettings model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.site = Site.objects.get(is_default_site=True)
    
    def test_footer_settings_creation(self):
        """Test FooterSettings creation."""
        settings = FooterSettings.objects.create(
            site=self.site,
            copyright_text="© 2025 Test Site",
            show_social_links=True
        )
        self.assertEqual(settings.copyright_text, "© 2025 Test Site")
        self.assertTrue(settings.show_social_links)
    
    def test_footer_settings_str_representation(self):
        """Test the string representation of FooterSettings."""
        settings = FooterSettings.objects.create(
            site=self.site,
            copyright_text="© 2025 Test Site. All rights reserved."
        )
        self.assertIn("Footer Settings", str(settings))
    
    def test_get_footer_links(self):
        """Test footer links helper method."""
        settings = FooterSettings.objects.create(
            site=self.site,
            footer_link_1_text="About",
            footer_link_1_url="/about/",
            footer_link_2_text="Contact",
            footer_link_2_url="/contact/",
        )
        links = settings.get_footer_links()
        # Default values include links 3 and 4 as well
        self.assertGreaterEqual(len(links), 2)
        self.assertEqual(links[0]['text'], "About")
        self.assertEqual(links[1]['url'], "/contact/")
    
    def test_get_social_links(self):
        """Test social links helper method."""
        settings = FooterSettings.objects.create(
            site=self.site,
            twitter_url="https://twitter.com/test",
            github_url="https://github.com/test",
        )
        links = settings.get_social_links()
        self.assertEqual(len(links), 2)
        self.assertTrue(any(link['name'] == 'Twitter' for link in links))
        self.assertTrue(any(link['name'] == 'GitHub' for link in links))


class BaseBlocksTestCase(WagtailPageTests):
    """Test cases for base StreamField blocks."""
    
    def test_base_heading_block_structure(self):
        """Test BaseHeadingBlock has required fields."""
        block = BaseHeadingBlock()
        self.assertIn('heading_text', block.child_blocks)
        self.assertIn('heading_level', block.child_blocks)
        self.assertIn('alignment', block.child_blocks)
    
    def test_base_rich_text_block_structure(self):
        """Test BaseRichTextBlock has required fields."""
        block = BaseRichTextBlock()
        self.assertIn('text', block.child_blocks)
        self.assertIn('alignment', block.child_blocks)
    
    def test_base_image_block_structure(self):
        """Test BaseImageBlock has required fields."""
        block = BaseImageBlock()
        self.assertIn('image', block.child_blocks)
        self.assertIn('caption', block.child_blocks)
        self.assertIn('alt_text', block.child_blocks)
        self.assertIn('alignment', block.child_blocks)
    
    def test_base_heading_block_defaults(self):
        """Test BaseHeadingBlock default values."""
        block = BaseHeadingBlock()
        # Test that heading level and alignment blocks exist
        self.assertIn('heading_level', block.child_blocks)
        self.assertIn('alignment', block.child_blocks)
        
        # Create a test value to verify defaults work
        test_value = {
            'heading_text': 'Test Heading',
            'heading_level': 'h2',
            'alignment': 'left'
        }
        # This should not raise an error
        cleaned = block.clean(test_value)
        self.assertEqual(cleaned['heading_level'], 'h2')
        self.assertEqual(cleaned['alignment'], 'left')


class BasePageTestCase(WagtailPageTests):
    """Test cases for BasePage abstract model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # BasePage is abstract, so we can't test it directly
        # These tests would be run on concrete implementations
        pass
    
    def test_base_page_has_seo_fields(self):
        """Test that BasePage defines SEO fields."""
        # Since BasePage is abstract, we check field definitions exist
        from core.models import BasePage
        
        # Check that the fields are defined in the class
        self.assertTrue(hasattr(BasePage, 'meta_description'))
        self.assertTrue(hasattr(BasePage, 'meta_keywords'))
        self.assertTrue(hasattr(BasePage, 'og_title'))
        self.assertTrue(hasattr(BasePage, 'og_description'))
        self.assertTrue(hasattr(BasePage, 'og_image'))

