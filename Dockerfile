
# 1 
FROM python:3.12.2

# 2
RUN pip install Flask gunicorn openai firebase-admin Flask-Bcrypt Flask-Cors Flask-Session

# 3
COPY ./ /app
WORKDIR /app/server/src

# 4
ENV PORT 8080

# 5
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app