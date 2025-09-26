# Use an official Python runtime as a parent image
FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/tensorflow-inference:2.19.0-cpu-py312-ubuntu22.04-sagemaker

# Rtrieve the new key directly from Nginx and adding it to your system's list of trusted keys
# This is to prevent GPG signing key expiration when updating nginx
RUN curl -fsSL https://nginx.org/keys/nginx_signing.key | apt-key add -

# Upgrade all packages and install the required libraries
RUN apt-get update && apt-get upgrade -y && apt-get install -y libgl1-mesa-glx

# Remove unnecessary packages that cause unresolved vulnerabilities
RUN apt-get remove --purge -y emacs emacs-bin-common emacs-common
RUN apt-get autoremove -y
RUN apt-get clean

# Set the working directory
# WORKDIR /app

# Install required packages from requirements.txt and deepface library which will install the required dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
# Install DeepFace directly in the Dockerfile to keep requirements.txt smaller
RUN pip install deepface==0.0.93

# Copy code and model
COPY image-analyzer.py /opt/ml/code/
COPY serve /usr/bin/serve

# Copy test files for testing
COPY testing/assets testing/assets
COPY testing/integration/test_endpoints.py testing/integration/test_endpoints.py

# Make the serve script executable
RUN chmod +x /usr/bin/serve

# Expose port for SageMaker
EXPOSE 8080

# Set entry point
ENTRYPOINT ["serve"]
