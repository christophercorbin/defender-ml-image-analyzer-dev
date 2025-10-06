import boto3
import argparse
import time
from botocore.exceptions import ClientError

# Get arguments
parser = argparse.ArgumentParser(description="Set the environment.")
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod', 'personal', 'soc2'], help='Environment: "dev", "stage", "prod", "personal", or "soc2"')
parser.add_argument('--image-digest', type=str, help='Specific image digest to use (optional)')
parser.add_argument('--repository-name', type=str, help='ECR repository name (optional, overrides default)')
parser.add_argument('--model-name', type=str, help='SageMaker model name (optional, overrides default)')
args = parser.parse_args()

print(f'Creating model for: {args.env}')

# Environment-specific configuration (using placeholders for security)
# In production, these would be loaded from environment variables or AWS Parameter Store
env_configs = {
    'dev': {
        'role': 'arn:aws:iam::{{DEV_ACCOUNT_ID}}:role/aws-sagemaker-role',
        'registry': '{{DEV_ACCOUNT_ID}}.dkr.ecr.us-east-1.amazonaws.com'
    },
    'stage': {
        'role': 'arn:aws:iam::{{STAGE_ACCOUNT_ID}}:role/aws-sagemaker-role',
        'registry': '{{STAGE_ACCOUNT_ID}}.dkr.ecr.us-east-1.amazonaws.com'
    },
    'prod': {
        'role': 'arn:aws:iam::{{PROD_ACCOUNT_ID}}:role/sagemaker-execution-role',
        'registry': '{{PROD_ACCOUNT_ID}}.dkr.ecr.us-east-1.amazonaws.com'
    }
}

if args.env in env_configs:
    role = env_configs[args.env]['role']
    registry = env_configs[args.env]['registry']
else:  # personal or soc2 environment
    # Get current AWS account ID for personal/soc2 environment
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    # Try common SageMaker role names
    iam = boto3.client('iam')
    possible_roles = [
        'SageMakerExecutionRole',  # SOC 2 preferred
        'SageMaker-ExecutionRole',
        'AmazonSageMaker-ExecutionRole',
        f'SageMaker-ExecutionRole-{account_id}',
        'service-role/SageMakerRole'
    ]
    
    role = None
    for role_name in possible_roles:
        try:
            iam.get_role(RoleName=role_name)
            role = f'arn:aws:iam::{account_id}:role/{role_name}'
            print(f'Found SageMaker role: {role_name}')
            break
        except iam.exceptions.NoSuchEntityException:
            continue
    
    if not role:
        # Fallback to default name (will be created by deployment script if needed)
        role = f'arn:aws:iam::{account_id}:role/SageMakerExecutionRole'
        print(f'Using default SageMaker role name (may need creation)')
        
    registry = f'{account_id}.dkr.ecr.us-east-1.amazonaws.com'
    print(f'Using {args.env} environment with account: {account_id}')

# Initialize clients
sagemaker = boto3.client('sagemaker', region_name='us-east-1')
ecr = boto3.client('ecr', region_name='us-east-1')

# Determine model name
if args.model_name:
    model_name = args.model_name
elif args.env == 'personal':
    model_name = 'soc2MlImageAnalyzerPersonal'
elif args.env == 'soc2':
    model_name = 'soc2MlImageAnalyzerHardened'
else:
    model_name = 'soc2MlImageAnalyzer'

# Determine repository name
if args.repository_name:
    repo_name = args.repository_name
elif args.env == 'personal':
    repo_name = 'soc2-ml-image-analyzer-personal'
elif args.env == 'soc2':
    repo_name = 'soc2-ml-image-analyzer-hardened'
else:
    repo_name = 'soc2-ml-image-analyzer'

# Get the specific image digest to use
if args.image_digest:
    image_url = f'{registry}/{repo_name}@{args.image_digest}'
    print(f'Using provided image digest: {args.image_digest}')
else:
    # Get the latest image digest from ECR
    try:
        response = ecr.describe_images(
            repositoryName=repo_name,
            imageIds=[{'imageTag': 'latest'}]
        )
        if response['imageDetails']:
            latest_digest = response['imageDetails'][0]['imageDigest']
            image_url = f'{registry}/{repo_name}@{latest_digest}'
            print(f'Using latest image digest from ECR: {latest_digest}')
        else:
            raise Exception("No image found with 'latest' tag")
    except ClientError as e:
        print(f'Error fetching image digest: {e}')
        # Fallback to tag-based reference (not recommended for production)
        image_url = f'{registry}/{repo_name}:latest'
        print('Warning: Falling back to tag-based reference')

print(f'Image URL: {image_url}')

# Force delete existing model if it exists
try:
    existing_model = sagemaker.describe_model(ModelName=model_name)
    print(f'Model {model_name} already exists. Force deleting...')
    sagemaker.delete_model(ModelName=model_name)
    print('Waiting for model deletion to complete...')
    
    # Wait longer for deletion to fully propagate
    time.sleep(30)
    
    # Verify deletion completed
    retries = 0
    while retries < 10:
        try:
            sagemaker.describe_model(ModelName=model_name)
            print(f'Model still exists, waiting... (attempt {retries + 1}/10)')
            time.sleep(10)
            retries += 1
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                print('Model deletion confirmed.')
                break
            else:
                raise e
    
    if retries >= 10:
        raise Exception("Model deletion did not complete within expected time")
        
except ClientError as e:
    if e.response['Error']['Code'] == 'ValidationException':
        print(f'Model {model_name} does not exist. Creating new one...')
    else:
        raise e

print(f'Creating model with image: {image_url}')

# Create model with explicit image digest
# Prepare environment variables based on deployment type
env_vars = {
    'SAGEMAKER_PROGRAM': 'image-analyzer.py',
    'FORCE_REFRESH': str(int(time.time()))  # Timestamp to force refresh
}

# Add SOC 2 specific environment variables
if args.env == 'soc2':
    env_vars.update({
        'SAGEMAKER_CONTAINER_LOG_LEVEL': '20',
        'SAGEMAKER_REGION': 'us-east-1',
        'SOC2_COMPLIANT': 'true',
        'SECURITY_HARDENED': 'true'
    })
    print('Adding SOC 2 compliance environment variables')

create_model_response = sagemaker.create_model(
    ModelName=model_name,
    PrimaryContainer={
        'Image': image_url,
        'Environment': env_vars
    },
    ExecutionRoleArn=role
)

print(f'Model created successfully: {create_model_response}')
print(f'Model ARN: {create_model_response["ModelArn"]}')

# Verify the model was created with the correct image
verify_response = sagemaker.describe_model(ModelName=model_name)
created_image = verify_response['PrimaryContainer']['Image']
print(f'Verified model image: {created_image}')

if '@sha256:' in created_image:
    created_digest = created_image.split('@')[1]
    expected_digest = image_url.split('@')[1] if '@' in image_url else 'latest'
    if created_digest == expected_digest:
        print('✅ Model created with correct image digest')
    else:
        print(f'⚠️ Warning: Image digest mismatch - Expected: {expected_digest}, Got: {created_digest}')
else:
    print('⚠️ Warning: Model created with tag-based reference instead of digest')