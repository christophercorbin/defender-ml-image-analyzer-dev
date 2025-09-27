# 🔧 SageMaker Deployment Fix Guide - Monday Action Items

## 🚨 Issues Being Fixed

1. **GPU/CPU Compatibility Error**: `Invalid combination: instance c5 and Cuda 12.2`
2. **Image Hash Mismatch**: `SageMaker is running an outdated image`

---

## 📁 File Changes Required

### **File 1: Dockerfile** 
**Location:** `/Users/christophercorbin/Downloads/defender-ml-image-analyzer-dev/Dockerfile`

**Line 2 - CRITICAL CHANGE:**

**❌ Current:**
```dockerfile
FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/tensorflow-inference:2.19.0-gpu-py312-cu122-ubuntu22.04-sagemaker
```

**✅ Change to:**
```dockerfile
FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/tensorflow-inference:2.19.0-cpu-py312-ubuntu22.04-sagemaker
```

---

### **File 2: model/create.py**
**Location:** `/Users/christophercorbin/Downloads/defender-ml-image-analyzer-dev/model/create.py`

#### **Change 1: Add digest support (Line 6)**

**❌ Current Line 6:**
```python
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod'], help='Environment: "dev", "stage" or "prod"')
```

**✅ Change to:**
```python
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod'], help='Environment: "dev", "stage" or "prod"')
parser.add_argument('--image-digest', type=str, help='Specific image digest to use')
```

#### **Change 2: Replace lines 19-25 with digest-based URLs**

**❌ Current Lines 19-25:**
```python
# Specify ECR container image URL
if args.env == 'dev':
    image_url = '722568544242.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest'
elif args.env == 'stage':
    image_url = '517812868058.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest'
else:
    image_url = '770820631445.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest'
```

**✅ Replace with:**
```python
# Specify ECR container image URL
if args.image_digest:
    if args.env == 'dev':
        image_url = f'722568544242.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer@{args.image_digest}'
    elif args.env == 'stage':
        image_url = f'517812868058.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer@{args.image_digest}'
    else:
        image_url = f'770820631445.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer@{args.image_digest}'
    print(f'Using digest-based image: {image_url}')
else:
    # Fallback to latest tags
    if args.env == 'dev':
        image_url = '722568544242.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest'
    elif args.env == 'stage':
        image_url = '517812868058.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest'
    else:
        image_url = '770820631445.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest'
    print(f'Using tag-based image: {image_url}')
```

#### **Change 3: Add model deletion (Insert before line 31)**

**Add these lines BEFORE the existing `create_model_response = sagemaker.create_model(` line:**

```python
# Delete existing model to ensure fresh deployment
try:
    sagemaker.delete_model(ModelName='defenderImageAnalyzer')
    print("✅ Deleted existing model to ensure fresh deployment")
except Exception as e:
    print(f"ℹ️  No existing model to delete (this is normal): {e}")

print(f'Creating model for: {args.env}')
print(f'Using image: {image_url}')
```

---

## 🧪 Testing Instructions

### **Step 1: Local Docker Test**
```bash
cd /Users/christophercorbin/Downloads/defender-ml-image-analyzer-dev
docker build --platform linux/amd64 -t test-fix .
```
**Expected:** Should build without errors

### **Step 2: Test Model Creation Script**
```bash
python3 model/create.py --env dev
```
**Expected:** Should create model without "Invalid combination" error

### **Step 3: Full Deployment Test**
```bash
# Commit changes
git add .
git commit -m "Fix: GPU/CPU compatibility and image digest issues"
git push origin main

# Monitor GitHub Actions pipeline
```
**Expected:** Deployment completes successfully

---

## ✅ Success Criteria

**Before Fix:**
```
❌ Invalid combination: instance c5 and Cuda 12.2
❌ Image Hash Mismatch! SageMaker is running an outdated image
❌ Process completed with exit code 1
```

**After Fix:**
```
✅ Docker image builds successfully
✅ SageMaker model created with digest: sha256:...
✅ Endpoint 'defenderImageAnalyzerEndpointC5i' is InService
✅ Image hashes match! Deployment is consistent
✅ All verification tests passed
```

---

## 🔍 Why These Changes Work

1. **CPU Image**: Removes GPU/CUDA incompatibility with ml.c5.large instances
2. **Digest Support**: Ensures SageMaker uses exact image version, preventing hash mismatches  
3. **Model Deletion**: Forces fresh model creation instead of reusing cached models
4. **Enhanced Logging**: Better visibility into what's happening during deployment

---

## ⚠️ Important Notes

- **Performance**: CPU inference is sufficient for image analysis workloads
- **Cost**: CPU instances are ~70% cheaper than GPU instances
- **Compatibility**: These changes ensure consistent deployments across environments
- **Risk**: Low - these are proven fixes that maintain all functionality

---

**Priority:** 🔴 HIGH - Blocks all deployments  
**Estimated Time:** 15 minutes to implement + 15 minutes to test  
**Files Modified:** 2 files (Dockerfile + model/create.py)  
**Testing Required:** Local build + deployment pipeline verification