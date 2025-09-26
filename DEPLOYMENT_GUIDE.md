# Personal Defender Image Analyzer - Deployment Guide

This guide helps you set up and deploy the Defender Image Analyzer with TensorFlow 2.19.0 upgrade to your personal AWS environment.

## 🎯 Overview

- **Docker Image**: TensorFlow 2.19.0 with Python 3.12 on Ubuntu 22.04
- **AWS Services**: ECR, SageMaker
- **CI/CD**: GitHub Actions with personal AWS account
- **Fixed Issues**: Image hash mismatch error resolved with explicit digest deployment

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Ensure you have these installed
- Docker Desktop (running)
- AWS CLI configured with your credentials
- Python 3.10+
- Git
```

### 2. Configure AWS Credentials

```bash
# Configure your personal AWS credentials
aws configure

# Verify access
aws sts get-caller-identity
```

### 3. Local Testing (Recommended First)

```bash
# Test the complete deployment locally first
python3 scripts/local_deploy.py

# Or run individual steps
python3 scripts/local_deploy.py --skip-deploy  # Only build and push image
python3 scripts/local_deploy.py --skip-build   # Only deploy to SageMaker
```

### 4. GitHub CI/CD Setup

1. **Push to GitHub**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/defender-ml-image-analyzer-dev.git
git push -u origin main
```

2. **Set GitHub Secrets**:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `AWS_ACCESS_KEY_ID`: Your AWS access key
     - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

3. **Trigger Deployment**:
   - Push to `main` branch to trigger deployment
   - Create PR to `main` to trigger tests only

## 📋 What Gets Deployed

### AWS Resources Created:
- **ECR Repository**: `defender-image-analyzer-personal`
- **SageMaker Model**: `defenderImageAnalyzerPersonal`  
- **SageMaker Endpoint**: `defenderImageAnalyzerPersonalC5i`
- **IAM Role**: `SageMaker-ExecutionRole` (if doesn't exist)

### Docker Image:
- **Base**: `763104351884.dkr.ecr.us-east-1.amazonaws.com/tensorflow-inference:2.19.0-gpu-py312-cu122-ubuntu22.04-sagemaker`
- **Application**: Flask app with DeepFace for face embedding analysis
- **Platform**: `linux/amd64` for SageMaker compatibility

## 🔧 Key Improvements Over Work Version

### ✅ Fixed Issues:
1. **Image Hash Mismatch**: Uses explicit image digests instead of `latest` tags
2. **Model Caching**: Proper model deletion and recreation with verification
3. **Timing Issues**: Extended wait times and proper endpoint status checking
4. **Environment Support**: Clean separation of personal vs work environments

### 🚀 Enhanced Features:
- **Local Testing**: Full local deployment script for testing
- **Better Logging**: Comprehensive logs with emojis for easy reading
- **Verification**: Enhanced deployment verification script
- **Error Handling**: Robust error handling and retry logic

## 📊 Testing the Deployment

### Test Endpoints:

```bash
# Get your endpoint URL from AWS Console or:
aws sagemaker describe-endpoint --endpoint-name defenderImageAnalyzerPersonalC5i

# Test ping endpoint (replace with actual endpoint URL)
curl -X GET https://your-endpoint-url/ping

# Test with verification script
python3 verify_deployment.py --endpoint-name defenderImageAnalyzerPersonalC5i
```

### Local Container Testing:

```bash
# Build and test locally
docker build --platform linux/amd64 -t defender-test .
docker run -d --platform linux/amd64 -p 8080:8080 --name test defender-test

# Test locally
curl -X GET http://localhost:8080/ping

# Cleanup
docker stop test && docker rm test
```

## 🔍 Troubleshooting

### Common Issues:

1. **Docker Platform Issues**:
   ```bash
   # Always use linux/amd64 for SageMaker compatibility
   docker build --platform linux/amd64 -t image-name .
   ```

2. **AWS Permissions**:
   ```bash
   # Ensure your user has these permissions:
   - ECR: Full access to your repositories
   - SageMaker: Full access for model/endpoint management
   - IAM: Role creation (or pre-create the SageMaker-ExecutionRole)
   ```

3. **Image Hash Mismatch**:
   - This should be fixed with the new digest-based deployment
   - Check logs for digest verification steps

4. **SageMaker Endpoint Issues**:
   ```bash
   # Check endpoint status
   aws sagemaker describe-endpoint --endpoint-name defenderImageAnalyzerPersonalC5i
   
   # Check endpoint logs in CloudWatch
   ```

### Debug Commands:

```bash
# Check ECR images
aws ecr describe-images --repository-name defender-image-analyzer-personal

# Check SageMaker model
aws sagemaker describe-model --model-name defenderImageAnalyzerPersonal

# Check endpoint status
aws sagemaker describe-endpoint --endpoint-name defenderImageAnalyzerPersonalC5i

# Run verification
python3 verify_deployment.py --endpoint-name defenderImageAnalyzerPersonalC5i
```

## 📈 Cost Optimization

- **Instance Type**: Uses `ml.c5.large` for cost efficiency
- **Auto-scaling**: Not enabled by default (you can add it)
- **Cleanup**: Delete endpoints when not in use:
  ```bash
  aws sagemaker delete-endpoint --endpoint-name defenderImageAnalyzerPersonalC5i
  ```

## 🎉 Success Indicators

When everything is working, you should see:
- ✅ Docker build completes without errors
- ✅ Image pushes to ECR successfully  
- ✅ SageMaker model creates with correct image digest
- ✅ Endpoint becomes "InService"
- ✅ Hash verification passes
- ✅ Ping endpoint responds with `{"message": "Pong"}`

## 🔄 CI/CD Pipeline Flow

1. **PR Creation** → Build and test Docker image
2. **Push to Main** → Full deployment:
   - Build and push to ECR
   - Create/update SageMaker model with digest
   - Update endpoint with new configuration
   - Verify deployment success
   - Run integration tests

Your personal CI/CD pipeline is now ready to deploy the TensorFlow 2.19.0 upgraded Defender Image Analyzer! 🚀