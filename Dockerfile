FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TRYTOND_CONFIG=/etc/trytond.conf

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    pkg-config \
    libcairo2-dev \
    libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -ms /bin/bash tryton
WORKDIR /home/tryton
USER tryton

# Add user's local bin to PATH
ENV PATH=/home/tryton/.local/bin:$PATH

# Install Python dependencies
COPY --chown=tryton:tryton requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Trytond configuration
COPY --chown=tryton:tryton trytond.conf /etc/trytond.conf

# Copy application code
COPY --chown=tryton:tryton . .

# Install local modules
COPY --chown=tryton:tryton install_local_modules.sh .
RUN chmod +x install_local_modules.sh
RUN ./install_local_modules.sh



# Expose Trytond port
EXPOSE 8090


# ENTRYPOINT ["/entrypoint.sh"] 
