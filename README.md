# Prabuddh.me - Django/Wagtail Project

A personal website and blog built with Django and Wagtail CMS, featuring a modular architecture with reusable components. Deployed on Google Cloud Run with Cloud SQL (PostgreSQL) and Google Cloud Storage.

## Architecture

- **Framework**: Django 5.2 + Wagtail 7.1
- **Frontend**: TailwindCSS 3.x + DaisyUI (via django-tailwind)
- **Database**: Cloud SQL with PostgreSQL 17
- **Static/Media Files**: Google Cloud Storage
- **Hosting**: Google Cloud Run
- **CI/CD**: Google Cloud Build

## Project Structure

```
prabuddh-me/
├── core/                   # Base application (reusable blocks, settings, templates)
├── home/                   # Homepage application
├── blog/                   # Blog application (planned)
├── search/                 # Search functionality
├── theme/                  # Tailwind CSS configuration
├── prabuddh_me/           # Project settings and configuration
│   ├── settings/
│   │   ├── base.py        # Common settings
│   │   ├── dev.py         # Development settings
│   │   └── production.py  # Production settings
│   ├── static/            # Project-level static files
│   └── templates/         # Project-level templates
├── static/                # Collected static files
├── media/                 # User-uploaded media
├── documentation/         # Project documentation
├── Dockerfile             # Container configuration
├── Makefile              # Common commands
└── requirements.txt      # Python dependencies
```

## Applications

### Core App

The **core** application serves as the foundation layer, providing reusable components for all other apps.

**Key Features:**
- Base abstract models (BasePage with SEO fields)
- Reusable StreamField blocks (Hero, CTA, Quote, Author Bio, etc.)
- Site-wide settings (SiteSettings, HeaderSettings, FooterSettings)
- Base templates (header, footer, SEO meta tags)
- No custom CSS/JavaScript - pure Tailwind + DaisyUI

**StreamField Blocks Available:**
- `BaseHeadingBlock` - Configurable headings (h1-h6)
- `BaseRichTextBlock` - Rich text with alignment
- `BaseImageBlock` - Images with captions
- `BaseButtonBlock` - DaisyUI styled buttons
- `BaseHeroBlock` - Hero sections with backgrounds
- `BaseCallToActionBlock` - CTA sections
- `BaseAuthorBioBlock` - Author cards with social links
- `BaseRecentPostsBlock` - Blog post displays
- `BaseQuoteBlock` - Styled blockquotes
- `BaseSpacerBlock` - Vertical spacing

**Usage in Other Apps:**
```python
from core.models import BasePage, BaseHeroBlock, BaseRichTextBlock

class MyPage(BasePage):  # Inherit SEO fields
    content = StreamField([
        ('hero', BaseHeroBlock()),
        ('text', BaseRichTextBlock()),
    ], use_json_field=True)
```

📖 [Core App Documentation](core/README.md)

### Home App

The **home** application manages the website's homepage and landing pages.

**Key Features:**
- Extends core.BasePage for SEO
- Uses core StreamField blocks
- Hero section configuration
- Author information and social links
- Featured and recent blog post integration
- Responsive design with TailwindCSS + DaisyUI

**Admin Configuration:**
- Content tab: Hero, StreamField, Author info
- SEO tab: Meta tags, Open Graph
- Settings tab: Featured/recent posts configuration

📖 [Home App Documentation](home/README.md)

### Blog App (Planned)

Coming soon - will use core blocks and BasePage for consistency.

## Design Principles

- **No Custom CSS**: All styling uses TailwindCSS utility classes
- **No JavaScript**: UI achieved with Tailwind and DaisyUI components
- **DRY (Don't Repeat Yourself)**: Reusable components in core app
- **SEO-First**: Built-in SEO optimization via BasePage
- **Wagtail Best Practices**: Follows official documentation standards
- **Production-Grade**: Enterprise-level architecture patterns

## Environment Setup

### Prerequisites

- Python 3.12+
- PostgreSQL (for local development)
- Google Cloud CLI
- Docker (for containerization)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd prabuddh-me
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Run the setup script**
   ```bash
   ./setup_local.sh
   ```

4. **Start the development server**
   ```bash
   make dev
   ```

### Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DJANGO_SETTINGS_MODULE`: `prabuddh_me.settings.dev` (local) or `prabuddh_me.settings.production`
- `DEBUG`: `True` for development, `False` for production
- `SECRET_KEY`: Django secret key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`: Database connection
- `GS_BUCKET_NAME`: Google Cloud Storage bucket name
- `GCP_PROJECT`: Google Cloud project ID

## Content Management

### Wagtail Admin

Access the Wagtail admin interface at `/admin/` to manage:

- **Pages**: Create and edit homepage, blog posts, and other content
- **Images**: Upload and manage media files
- **Documents**: Handle file uploads
- **Settings**: Configure site-wide settings

### Site-Wide Settings

Configure global settings in Wagtail Admin → Settings:

**Site Settings** (`core.SiteSettings`)
- Site name, tagline, and description
- Contact information (email, phone)
- Social media links (Twitter, LinkedIn, GitHub, Facebook, Instagram)
- SEO defaults (meta description, Google Analytics)
- Footer text and copyright

**Header Settings** (`core.HeaderSettings`)
- Logo and site title
- Navigation links (up to 5)
- Search and theme toggle options
- Header positioning (sticky/static)

**Footer Settings** (`core.FooterSettings`)
- Copyright text (with auto year)
- Footer links (up to 4)
- Social media links
- Footer description

**Access in Templates:**
```django
{% load wagtailsettings_tags %}
{% get_settings %}
{{ settings.core.SiteSettings.site_name }}
{{ settings.core.HeaderSettings.site_title }}
{{ settings.core.FooterSettings.copyright_text }}
```

### Creating Content

**Homepage:**
1. Navigate to Pages in Wagtail admin
2. Add child page to root → Select "Homepage"
3. Use StreamField blocks to build content:
   - Hero sections for visual impact
   - Rich text for content
   - Images with captions
   - Call-to-action buttons
   - Author bio cards
   - Recent posts widgets
   - Quotes and spacers
4. Configure SEO settings (inherited from BasePage)
5. Publish when ready

**SEO Optimization:**

All pages extending `BasePage` automatically have:
- `meta_description` - For search engine descriptions
- `meta_keywords` - SEO keywords
- `og_title` - Open Graph title (social sharing)
- `og_description` - Open Graph description
- `og_image` - Social media preview image

### Tailwind CSS

The project uses django-tailwind for styling:

**Development:**
```bash
# Start Tailwind watcher (auto-rebuilds on changes)
make tailwind-watch

# Manual build
make tailwind-build-local
```

**Components:**
- Uses DaisyUI component library
- No custom CSS allowed (per project guidelines)
- All styling via Tailwind utility classes
- Configured in `theme/static_src/`

**Available DaisyUI Components:**
- Buttons, Cards, Badges, Alerts
- Forms, Inputs, Selects
- Navbar, Footer, Hero
- Modals, Dropdowns, Tooltips
- And more: https://daisyui.com/components/

## Deployment

### Google Cloud Setup

1. **Create Cloud SQL instance**
   ```bash
   gcloud sql instances create prabuddh-me \
     --database-version=POSTGRES_17 \
     --tier=db-f1-micro \
     --region=asia-south1
   ```

2. **Create database**
   ```bash
   gcloud sql databases create prabuddh_me_db \
     --instance=prabuddh-me
   ```

3. **Create GCS bucket**
   ```bash
   gsutil mb gs://prabuddh-me-bucket
   gsutil iam ch allUsers:objectViewer gs://prabuddh-me-bucket
   ```

### Cloud Build Deployment

The project uses Cloud Build for automatic deployment from GitHub:

```bash
# Deploy using Cloud Build
make deploy-cloudbuild

# Or directly
gcloud builds submit --config cloudbuild.yaml
```

**Important**: Before using Cloud Build, you need to:
1. Run the setup script: `./setup_cloudbuild.sh`
2. Update the hardcoded values in `cloudbuild.yaml` with your actual:
   - `SECRET_KEY`
   - `DB_PASSWORD` 
   - `SUPERUSER_PASSWORD`
3. Set up a Cloud Build trigger connected to your GitHub repository

### Makefile Deployment

For manual deployment using the Makefile:

```bash
# Complete deployment (build, push, deploy, migrate)
make deploy

# Individual steps
make build    # Build Docker image
make push     # Push to Container Registry
```

### Manual Cloud Run Deployment

Using the Makefile (recommended):
```bash
# Complete deployment pipeline
make deploy
```

Or using raw gcloud commands:
```bash
# Build and push image
make build
make push

# Deploy to Cloud Run
gcloud run deploy prabuddh-me \
  --image gcr.io/prabuddh-me-5/prabuddh-me \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars DJANGO_SETTINGS_MODULE=prabuddh_me.settings.production \
  --set-env-vars CLOUD_RUN=true \
  --add-cloudsql-instances prabuddh-me-5:asia-south1:prabuddh-me
```

## Settings Configuration

The project uses a modular settings structure:

- `base.py`: Common settings shared across environments
- `dev.py`: Development-specific settings
- `production.py`: Production settings for Cloud Run
- `local.py`: Local overrides (not tracked in git)

### Key Features

- **Environment-based configuration** using `python-decouple`
- **Automatic database detection** (Cloud SQL vs local PostgreSQL)
- **Google Cloud Storage integration** for static/media files
- **Security hardening** for production deployment
- **Comprehensive logging** for Cloud Run

## Database Migrations

```bash
# Create migrations
make makemigrations

# Apply migrations
make migrate-local

# Create superuser
make superuser-local
```

## Static Files

- **Development**: Local file storage with WhiteNoise
- **Production**: Google Cloud Storage

## Monitoring and Logs

View Cloud Run logs:
```bash
# Using Makefile
make logs

# Or directly with gcloud
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=prabuddh-me" --limit=100
```

## Common Commands

### Local Development
```bash
# Run development server
make dev

# Run database migrations
make migrate-local

# Create superuser
make superuser-local

# Build Tailwind CSS
make tailwind-build-local

# Run tests
make test

# Check for issues
make check

# Collect static files
make collectstatic

# Shell access
make shell-local

# Database shell
make dbshell
```

### Production/Cloud Run
```bash
# Deploy to Cloud Run
make deploy

# View logs
make logs

# Shell access (containerized)
make shell

# Build Tailwind in container
make tailwind-build

# Clean local Docker images
make clean

# Stop Cloud Run service
make stop
```

### Available Makefile Targets
```bash
# See all available commands
make help
```

## Troubleshooting

### Cloud SQL Connection Issues
- Ensure Cloud SQL Proxy is running for local development
- Check that the Cloud SQL instance allows connections from Cloud Run
- Verify environment variables are correctly set

### Static Files Not Loading
- Confirm GCS bucket permissions are set correctly
- Check that `GS_BUCKET_NAME` environment variable is set
- Verify GCS credentials are properly configured

### Database Migration Issues
- Run `python manage.py showmigrations` to see migration status
- Use `--fake` flag to mark migrations as applied without running them
- Check database connectivity with `python manage.py dbshell`

### Tailwind Not Building
- Check that Node.js is installed (required for django-tailwind)
- Restart the Tailwind watcher: `make tailwind-watch`
- Verify theme app is in INSTALLED_APPS
- Check `theme/static_src/` for configuration issues

### StreamField Block Not Appearing
- Ensure block is imported from `core.models`
- Check that block is included in the StreamField definition
- Verify block template exists in `core/templates/core/blocks/`
- Clear cache and restart server

## Documentation

Comprehensive documentation is available in the `documentation/` directory:

### Setup Guides
- **[Core App Setup Summary](documentation/CORE_APP_SETUP_SUMMARY.md)** - Complete setup of the core foundation layer
- **[Home App Migration Summary](documentation/HOME_APP_MIGRATION_SUMMARY.md)** - Migration from standalone to core-based architecture

### App Documentation
- **[Core App README](core/README.md)** - Base models, blocks, settings, and templates
- **[Home App README](home/README.md)** - Homepage configuration and usage

### Key Concepts

**BasePage Model:**
- Abstract model providing SEO fields to all pages
- Includes meta tags, Open Graph, and Twitter Card support
- Extend this for all custom page types

**StreamField Blocks:**
- Reusable content blocks defined in core
- Import and use in any app's StreamField
- Maintains consistency across the site

**Settings Models:**
- `SiteSettings` - Global site configuration
- `HeaderSettings` - Navigation and header
- `FooterSettings` - Footer and copyright
- Access via `{% get_settings %}` in templates

**Template Hierarchy:**
- `core/base.html` - Main layout template
- App templates extend `core/base.html`
- Block templates in `core/templates/core/blocks/`

### Development Guidelines

From `.github/prompts/general-instructions.md`:

1. **No Custom CSS** - Use only Tailwind utility classes
2. **No JavaScript** - Achieve UI with Tailwind + DaisyUI only
3. **Use Core Blocks** - Import blocks from core.models
4. **Extend BasePage** - For consistent SEO across pages
5. **DaisyUI Components** - Use component library for UI
6. **Follow Wagtail Docs** - Adhere to official best practices

## Project Statistics

- **Code Reduction**: Home app reduced by 73% (1,056 → 282 lines) via core migration
- **Reusable Blocks**: 10 StreamField blocks available in core
- **Settings Models**: 3 (SiteSettings, HeaderSettings, FooterSettings)
- **SEO Fields**: 5 inherited from BasePage (meta_description, keywords, og_title, og_description, og_image)

## Future Enhancements

- **Blog App** - Full-featured blog with categories and tags
- **Search** - Enhanced search functionality
- **Newsletter** - Email subscription integration
- **Analytics** - Enhanced tracking and reporting
- **Portfolio** - Projects showcase section
- **Contact Form** - With spam protection

## License

MIT License (or your preferred license)

## Contact

[Your contact information]
