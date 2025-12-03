FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY setup.py MANIFEST.in ./
COPY master_of_jokes ./master_of_jokes

# Install dependencies and the app in development mode
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV FLASK_APP=master_of_jokes
ENV FLASK_ENV=development

# Expose port
EXPOSE 5000

# Initialize the database
RUN flask init-db

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]
