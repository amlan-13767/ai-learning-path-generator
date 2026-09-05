FROM ai-learning-path-generator-worker:latest

WORKDIR /app

RUN pip install --no-cache-dir \
	gunicorn \
	flask-cors \
	Flask-SQLAlchemy==3.1.1 \
	Flask-Login==0.6.3 \
	Flask-WTF==1.2.1 \
	Flask-Migrate==4.0.7 \
	'Flask-Dance[google]==7.1.0' \
	email-validator==2.1.0.post1 \
	psycopg2-binary>=2.9.9

# The worker image already contains the full application runtime dependencies
# and the src package. Add the API and web application packages on top.
COPY backend/ /app/backend/
COPY web_app/ /app/web_app/
COPY config.py /app/config.py
COPY init_render_db.py /app/init_render_db.py
COPY migrations/ /app/migrations/

# Copy .env if exists
COPY .env* /app/

EXPOSE 5000

# Use shell form so $PORT expands on Render
CMD ["sh", "-c", "gunicorn backend.app:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 30"]
