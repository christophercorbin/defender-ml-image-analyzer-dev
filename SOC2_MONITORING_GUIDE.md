# 📊 SOC 2 SageMaker Deployment Monitoring Guide

## Overview
This guide provides AWS CLI commands to monitor SOC 2 hardened deployments from compliance testing through production readiness.

---

## 🔍 Phase 1: ECR Repository & Image Management

### Check ECR Repository Status
```bash
# Verify SOC 2 repository exists and configuration
aws ecr describe-repositories --repository-names defender-image-analyzer-soc2 --region us-east-1

# Expected output shows:
# - repositoryUri: 438465156498.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer-soc2
# - scanOnPush: true (vulnerability scanning enabled)
# - encryptionType: AES256
```

### Monitor Docker Image Push Progress
```bash
# List all images in SOC 2 repository
aws ecr list-images --repository-name defender-image-analyzer-soc2 --region us-east-1

# Get detailed image information with tags and push timestamps
aws ecr describe-images --repository-name defender-image-analyzer-soc2 --region us-east-1

# Look for these expected tags:
# - soc2-dev-latest
# - soc2-dev-{commit-sha}
# - soc2-latest
```

### Check Image Vulnerability Scan Results
```bash
# Get vulnerability scan summary (SOC 2 compliance requirement)
aws ecr describe-image-scan-findings \
  --repository-name defender-image-analyzer-soc2 \
  --image-id imageTag=soc2-dev-latest \
  --region us-east-1 \
  --query 'imageScanFindings.findingCounts'

# Expected: Low/medium findings only, no CRITICAL or HIGH vulnerabilities
```

---

## 🤖 Phase 2: SageMaker Model Management

### List SOC 2 Hardened Models
```bash
# Find all SOC 2 models (names include timestamps)
aws sagemaker list-models \
  --name-contains "defenderImageAnalyzerSOC2Hardened" \
  --region us-east-1 \
  --max-items 10 \
  --sort-by CreationTime \
  --sort-order Descending

# Models are named: defenderImageAnalyzerSOC2Hardened-dev-YYYYMMDDHHMMSS
```

### Get Model Details
```bash
# Get the most recent model name
LATEST_MODEL=$(aws sagemaker list-models \
  --name-contains "defenderImageAnalyzerSOC2Hardened" \
  --region us-east-1 \
  --query 'Models[0].ModelName' \
  --output text)

echo "Latest SOC 2 model: $LATEST_MODEL"

# Get detailed model configuration
aws sagemaker describe-model --model-name "$LATEST_MODEL" --region us-east-1

# Check for these SOC 2 compliance environment variables:
# - SOC2_COMPLIANT: 'true'
# - SECURITY_HARDENED: 'true'
```

---

## 🎯 Phase 3: Endpoint Deployment Monitoring

### Check Endpoint Status (Primary Command)
```bash
# Monitor SOC 2 development endpoint
aws sagemaker describe-endpoint \
  --endpoint-name defenderImageAnalyzerSOC2HardenedDev \
  --region us-east-1

# Key status values:
# - Creating: Initial deployment phase
# - InService: Ready for traffic ✅
# - Updating: Configuration change in progress
# - Failed: Deployment error ❌
```

### Get Just the Status (Quick Check)
```bash
# Get only the status for quick monitoring
aws sagemaker describe-endpoint \
  --endpoint-name defenderImageAnalyzerSOC2HardenedDev \
  --region us-east-1 \
  --query 'EndpointStatus' \
  --output text

# Returns: Creating | InService | Failed | Updating
```

### Monitor Endpoint Configuration
```bash
# List endpoint configurations for SOC 2
aws sagemaker list-endpoint-configs \
  --name-contains "defenderImageAnalyzerSOC2Hardened" \
  --region us-east-1 \
  --max-items 5

# Get configuration details (instance type, model version)
LATEST_CONFIG=$(aws sagemaker list-endpoint-configs \
  --name-contains "defenderImageAnalyzerSOC2Hardened" \
  --region us-east-1 \
  --query 'EndpointConfigs[0].EndpointConfigName' \
  --output text)

aws sagemaker describe-endpoint-config \
  --endpoint-config-name "$LATEST_CONFIG" \
  --region us-east-1

# Verify: InstanceType should be "ml.c5.large" (CPU-only)
```

---

## 🚨 Troubleshooting Commands

### Check for Deployment Errors
```bash
# Get failure reason if endpoint deployment fails
aws sagemaker describe-endpoint \
  --endpoint-name defenderImageAnalyzerSOC2HardenedDev \
  --region us-east-1 \
  --query 'FailureReason' \
  --output text

# Common issues:
# - Image pull errors (check ECR permissions)
# - Resource limits exceeded
# - Health check failures
```

### Check CloudWatch Logs
```bash
# List log groups for SageMaker endpoints
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/sagemaker/Endpoints/defenderImageAnalyzerSOC2HardenedDev" \
  --region us-east-1

# Get recent log events (replace LOG_GROUP_NAME with actual name)
aws logs get-log-events \
  --log-group-name "/aws/sagemaker/Endpoints/defenderImageAnalyzerSOC2HardenedDev" \
  --log-stream-name "AllTraffic/i-1234567890abcdef0" \
  --region us-east-1 \
  --start-time $(date -d '10 minutes ago' +%s)000
```

---

## 🔄 Continuous Monitoring Loop

### Real-time Status Monitoring
```bash
echo "🔄 Starting SOC 2 endpoint monitoring..."
echo "Press Ctrl+C to stop"

while true; do
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  
  # Check endpoint status
  STATUS=$(aws sagemaker describe-endpoint \
    --endpoint-name defenderImageAnalyzerSOC2HardenedDev \
    --region us-east-1 \
    --query 'EndpointStatus' \
    --output text 2>/dev/null)
  
  if [ "$STATUS" = "InService" ]; then
    echo "✅ [$TIMESTAMP] SOC 2 endpoint is READY! Status: $STATUS"
    echo "🎉 Deployment completed successfully!"
    break
  elif [ "$STATUS" = "Failed" ]; then
    echo "❌ [$TIMESTAMP] SOC 2 endpoint FAILED! Status: $STATUS"
    echo "🔍 Getting failure reason..."
    aws sagemaker describe-endpoint \
      --endpoint-name defenderImageAnalyzerSOC2HardenedDev \
      --region us-east-1 \
      --query 'FailureReason' \
      --output text
    break
  elif [ -n "$STATUS" ]; then
    echo "🔄 [$TIMESTAMP] SOC 2 endpoint Status: $STATUS"
  else
    echo "⏳ [$TIMESTAMP] SOC 2 endpoint not found yet (pipeline still running...)"
  fi
  
  sleep 30
done
```

---

## 📋 Complete Status Check Script

### One-Command Status Overview
```bash
echo "=== 📊 SOC 2 Deployment Status Overview ==="
echo ""

echo "1️⃣ ECR Repository Images:"
IMAGE_COUNT=$(aws ecr list-images --repository-name defender-image-analyzer-soc2 --region us-east-1 --query 'length(imageIds)')
echo "   Found $IMAGE_COUNT images in SOC 2 repository"

if [ "$IMAGE_COUNT" -gt 0 ]; then
  echo "   Latest images:"
  aws ecr list-images --repository-name defender-image-analyzer-soc2 --region us-east-1 --query 'imageIds[*].imageTag' --output table
fi

echo ""
echo "2️⃣ SageMaker Models:"
aws sagemaker list-models --name-contains "defenderImageAnalyzerSOC2Hardened" --region us-east-1 --query 'Models[0:3].[ModelName,CreationTime]' --output table

echo ""
echo "3️⃣ Endpoint Status:"
ENDPOINT_STATUS=$(aws sagemaker describe-endpoint --endpoint-name defenderImageAnalyzerSOC2HardenedDev --region us-east-1 --query 'EndpointStatus' --output text 2>/dev/null)

if [ -n "$ENDPOINT_STATUS" ]; then
  echo "   🎯 defenderImageAnalyzerSOC2HardenedDev: $ENDPOINT_STATUS"
  
  if [ "$ENDPOINT_STATUS" = "InService" ]; then
    echo "   ✅ SOC 2 endpoint is ready for testing!"
    echo "   📡 Endpoint URL available for inference requests"
  fi
else
  echo "   ⏳ Endpoint not created yet (pipeline in progress)"
fi

echo ""
echo "=== End Status Check ==="
```

---

## 🧪 Testing Commands (Once Endpoint is InService)

### Endpoint Health Check
```bash
# Basic endpoint information
aws sagemaker describe-endpoint \
  --endpoint-name defenderImageAnalyzerSOC2HardenedDev \
  --region us-east-1 \
  --query '{Status:EndpointStatus,CreationTime:CreationTime,LastModifiedTime:LastModifiedTime}'

# Check endpoint URL (for SDK usage)
aws sagemaker describe-endpoint \
  --endpoint-name defenderImageAnalyzerSOC2HardenedDev \
  --region us-east-1 \
  --query 'EndpointArn'
```

---

## 📚 Learning Notes

### Understanding the Pipeline Flow
1. **Compliance Phase**: Docker build + security tests
2. **Image Phase**: Push to ECR with vulnerability scanning
3. **Model Phase**: SageMaker model creation with SOC 2 config
4. **Endpoint Phase**: Deployment to ml.c5.large instances
5. **Verification Phase**: Health checks and readiness confirmation

### Key SOC 2 Compliance Indicators
- ✅ Non-root container execution (UID 1000)
- ✅ OpenSSL 3.x security patching
- ✅ Vulnerability scanning enabled
- ✅ Minimal attack surface (multi-stage build)
- ✅ Environment variable security markers

### Common Deployment Timeline
- **Minutes 0-3**: Compliance testing and image build
- **Minutes 3-5**: ECR push and vulnerability scan
- **Minutes 5-7**: SageMaker model creation
- **Minutes 7-12**: Endpoint deployment and startup
- **Minutes 12-15**: Health checks and ready state

---

*💡 Pro Tip: Save commonly used commands as shell aliases in your `~/.zshrc` for faster monitoring!*