#!/bin/sh

export $(grep -v '^#' .env | xargs)

# download files from azure blob storage into the data folder
python /scripts/azure_downloader.py

# Run the scraper script
python scrapper_script.py

# Apply database migrations
python /app/manage.py migrate

# Collect static files (optional, typically used in production)
python /app/manage.py collectstatic --noinput

# Create indexes in elastic search
python /scripts/rag.py

# Start the Django development server
exec python /app/manage.py runserver 0.0.0.0:8000
