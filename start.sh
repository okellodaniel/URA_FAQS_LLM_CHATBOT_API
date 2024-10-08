#!/bin/sh

# Run the scraper script
python scrapper_script.py

# After the scraper finishes, start the Streamlit app
# exec streamlit run ./app/app.py --server.port=8501 --server.address=0.0.0.0

# Apply database migrations
python /app/manage.py migrate

# Collect static files (optional, typically used in production)
python /app/manage.py collectstatic --noinput

# Start the Django development server
exec python /app/manage.py runserver 0.0.0.0:8000
