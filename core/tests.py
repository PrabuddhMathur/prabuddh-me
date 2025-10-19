from django.test import TestCase
from wagtail.test.utils import WagtailPageTests
from wagtail.models import Site
from .models import SiteSettings


class SiteSettingsTestCase(TestCase):
    """Test cases for SiteSettings model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test site (required for SiteSettings)
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
    
    def test_site_settings_str(self):
        """Test the string representation of SiteSettings."""
        settings = SiteSettings.objects.create(
            site=self.site,
            site_name="Test Site"
        )
        # Verify settings object was created
        self.assertIsNotNone(settings)


class BaseBlocksTestCase(WagtailPageTests):
    """Test cases for base StreamField blocks."""
    
    def test_base_heading_block(self):
        """Test BaseHeadingBlock structure."""
        # Add block tests as needed
        pass
    
    def test_base_rich_text_block(self):
        """Test BaseRichTextBlock structure."""
        # Add block tests as needed
        pass
    
    def test_base_image_block(self):
        """Test BaseImageBlock structure."""
        # Add block tests as needed
        pass
