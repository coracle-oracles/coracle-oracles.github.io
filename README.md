# Coracle website

A Django website for the Coracle Regional Burn.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for package management.

1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run migrations:
   ```bash
   uv run python manage.py migrate
   ```

## Development

Run the development server:
```bash
uv run python manage.py runserver
```

Then visit http://localhost:8000 in your browser.

## Project Structure

- `config/` - Django project settings
- `core/` - Main Django app with views and templates
- `staticfiles/` - Static assets (CSS, JS, images, documents)
  - `css/` - Stylesheets
  - `js/` - JavaScript files
  - `img/` - Images
  - `doc/` - PDF documents

## Making Changes

1. Edit templates in `core/templates/core/`
2. Base template with navigation and footer is in `base.html`
3. Page-specific templates extend the base template

## Production Deployment

For production, you'll need to:

1. Set `DEBUG = False` in settings
2. Configure `ALLOWED_HOSTS`
3. Set a proper `SECRET_KEY` (use environment variable)
4. Run `uv run python manage.py collectstatic`
5. Configure a production web server (gunicorn, nginx, etc.)
