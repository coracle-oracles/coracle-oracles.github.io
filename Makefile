.PHONY: init migrate seed run clean

# Load environment variables from .env
include .env
export

# Initialize database (migrate and seed)
init: migrate seed

# Run database migrations
migrate:
	uv run python manage.py migrate

# Insert seed data
seed:
	sqlite3 db.sqlite3 < seed.sql

# Run the development server
run:
	uv run python manage.py runserver

# Create a superuser
superuser:
	uv run python manage.py createsuperuser

# Reset database (delete and reinitialize)
reset:
	rm -f db.sqlite3
	$(MAKE) init
