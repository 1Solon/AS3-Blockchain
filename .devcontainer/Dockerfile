FROM python:3.12
LABEL Description="Build environment"

# Upgrade pip
RUN pip install --upgrade pip

# Install zsh
RUN apt-get update && apt-get install -y zsh && rm -rf /var/lib/apt/lists/*

# Make zsh the default shell
RUN chsh -s $(which zsh)

# Install production dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Install development dependencies
COPY requirements-dev.txt /tmp/requirements-dev.txt
RUN pip install -r /tmp/requirements-dev.txt && rm /tmp/requirements-dev.txt