import boto3
import argparse

# Get arguments
parser = argparse.ArgumentParser(description="Set the environment.")
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod'], help='Environment: "dev", "stage" or "prod"')
args = parser.parse_args()

print(f'Creating model for: {args.env}')

# Specify container role
if args.env == 'dev':
    role = 'arn:aws:iam::722568544242:role/aws-sagemaker-role' 
elif args.env == 'stage':
    role = 'arn:aws:iam::517812868058:role/aws-sagemaker-role' 
else:
    role ='arn:aws:iam::770820631445:role/dme-sagemaker-role'

# Specify ECR container image URL
if args.env == 'dev':
    image_url = '722568544242.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest'
elif args.env == 'stage':
    image_url = '517812868058.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest'
else:
    image_url = '770820631445.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest'

# Initialize SageMaker client
sagemaker = boto3.client('sagemaker', region_name='us-east-1')

# Create model
create_model_response = sagemaker.create_model(
    ModelName='defenderImageAnalyzer',
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
