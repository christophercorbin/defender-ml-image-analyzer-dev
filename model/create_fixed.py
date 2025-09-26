import boto3
import argparse
import time
from botocore.exceptions import ClientError

# Get arguments
parser = argparse.ArgumentParser(description="Set the environment.")
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod'], help='Environment: "dev", "stage" or "prod"')
parser.add_argument('--image-digest', type=str, help='Specific image digest to use (optional)')
args = parser.parse_args()

print(f'Creating model for: {args.env}')

# Specify container role
if args.env == 'dev':
    role = 'arn:aws:iam::722568544242:role/aws-sagemaker-role'
    registry = '722568544242.dkr.ecr.us-east-1.amazonaws.com'
elif args.env == 'stage':
    role = 'arn:aws:iam::517812868058:role/aws-sagemaker-role'
    registry = '517812868058.dkr.ecr.us-east-1.amazonaws.com'
else:
    role = 'arn:aws:iam::770820631445:role/dme-sagemaker-role'
    registry = '770820631445.dkr.ecr.us-east-1.amazonaws.com'

# Initialize clients
sagemaker = boto3.client('sagemaker', region_name='us-east-1')
ecr = boto3.client('ecr', region_name='us-east-1')

model_name = 'defenderImageAnalyzer'

# Get the specific image digest to use
if args.image_digest:
    image_url = f'{registry}/defender-image-analyzer@{args.image_digest}'
    print(f'Using provided image digest: {args.image_digest}')
else:
    # Get the latest image digest from ECR
    try:
        response = ecr.describe_images(
            repositoryName='defender-image-analyzer',
            imageIds=[{'imageTag': 'latest'}]
        )
        if response['imageDetails']:
            latest_digest = response['imageDetails'][0]['imageDigest']
            image_url = f'{registry}/defender-image-analyzer@{latest_digest}'
            print(f'Using latest image digest from ECR: {latest_digest}')
        else:
            raise Exception("No image found with 'latest' tag")
    except ClientError as e:
        print(f'Error fetching image digest: {e}')
        # Fallback to tag-based reference (not recommended for production)
        image_url = f'{registry}/defender-image-analyzer:latest'
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
create_model_response = sagemaker.create_model(
    ModelName=model_name,
    PrimaryContainer={
        'Image': image_url,
        # Force SageMaker to pull fresh image by adding environment variable
        'Environment': {
            'SAGEMAKER_PROGRAM': 'image-analyzer.py',
            'FORCE_REFRESH': str(int(time.time()))  # Timestamp to force refresh
        }
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