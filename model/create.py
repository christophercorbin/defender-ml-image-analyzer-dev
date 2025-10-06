import boto3
import argparse

# Get arguments
parser = argparse.ArgumentParser(description="Set the environment.")
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod'], help='Environment: "dev", "stage" or "prod"')
args = parser.parse_args()

print(f'Creating model for: {args.env}')

# Environment-specific configuration
# In production, these would be loaded from environment variables or AWS Parameter Store
env_config = {
    'dev': {
        'role': 'arn:aws:iam::{{DEV_ACCOUNT_ID}}:role/aws-sagemaker-role',
        'image_url': '{{DEV_ACCOUNT_ID}}.dkr.ecr.us-east-1.amazonaws.com/soc2-ml-image-analyzer:latest'
    },
    'stage': {
        'role': 'arn:aws:iam::{{STAGE_ACCOUNT_ID}}:role/aws-sagemaker-role',
        'image_url': '{{STAGE_ACCOUNT_ID}}.dkr.ecr.us-east-1.amazonaws.com/soc2-ml-image-analyzer:latest'
    },
    'prod': {
        'role': 'arn:aws:iam::{{PROD_ACCOUNT_ID}}:role/sagemaker-execution-role',
        'image_url': '{{PROD_ACCOUNT_ID}}.dkr.ecr.us-east-1.amazonaws.com/soc2-ml-image-analyzer:latest'
    }
}

role = env_config[args.env]['role']
image_url = env_config[args.env]['image_url']

# Initialize SageMaker client
sagemaker = boto3.client('sagemaker', region_name='us-east-1')

# Create model
create_model_response = sagemaker.create_model(
    ModelName='soc2MlImageAnalyzer',
    PrimaryContainer={
        'Image': image_url,
        # 'ModelDataUrl': 's3://your-bucket/your-model.tar.gz'  # Optional if your image contains the model
    },
    ExecutionRoleArn=role
)

print(f'Model created with response: {create_model_response}')

# endpoint_config_name = 'defenderImageAnalyzerConfig5'

# Deploy endpoint
# sagemaker.create_endpoint_config(
#     EndpointConfigName=endpoint_config_name,
#     ProductionVariants=[{
#         'InstanceType': 'ml.g4dn.xlarge',
#         'InitialInstanceCount': 1,
#         'ModelName': 'defenderImageAnalyzer',
#         'VariantName': 'AllTraffic'
#     }]
# )

# Create endpoint 
# sagemaker.create_endpoint(
#     EndpointName='defenderImageAnalyzerEndpoint',
#     EndpointConfigName='defenderImageAnalyzerConfig1'
# )

# sagemaker.update_endpoint(
#     EndpointName='defenderImageAnalyzerEndpoint',
#     EndpointConfigName=endpoint_config_name
# )
