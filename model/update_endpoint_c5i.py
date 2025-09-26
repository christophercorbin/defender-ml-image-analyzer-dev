import boto3
from datetime import datetime
from botocore.exceptions import ClientError
import argparse

# Get arguments
parser = argparse.ArgumentParser(description="Set the environment.")
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod', 'test'], help='Environment: "dev", "stage" or "prod" or "test"')
args = parser.parse_args()

print(f'Creating / Updating endpoint for: {args.env}')

# Initialize SageMaker client
sagemaker = boto3.client('sagemaker', region_name='us-east-1')

model_name = 'defenderImageAnalyzer'
endpoint_name = 'defenderImageAnalyzerEndpointC5i'  if args.env == 'dev' or args.env == "stage" or args.env == 'prod' else 'defenderImageAnalyzerEndpointC5i-test'
timestamp = datetime.now().strftime('%Y%m%d-%H%M')
endpoint_config_name = f'{endpoint_name}-{timestamp}'
print(f'Endpoint config name: {endpoint_config_name}')

# Deploy endpoint
sagemaker.create_endpoint_config(
    EndpointConfigName=endpoint_config_name,
    ProductionVariants=[{
        'InstanceType': 'ml.c5.large',
        'InitialInstanceCount': 1,
        'ModelName': model_name,
        'VariantName': 'AllTraffic'
    }]
)

try:
    # Describe the endpoint, to check if it exists
    response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
    # If the call to describe_endpoint is successful, it means the endpoint exists
    # and you can call update_endpoint
    print(f"Endpoint '{endpoint_name}' exists. Updating...")
    response = sagemaker.update_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=endpoint_config_name
    )
    print(f"Updated response: {response}")
except ClientError as e:
    # If a ClientError is raised, check if it's because the endpoint does not exist
    if e.response['Error']['Code'] == 'ValidationException':
        # If the endpoint does not exist, create it
        print(f"Endpoint '{endpoint_name}' does not exist. Creating...")
        response = sagemaker.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
    else:
        # If a different kind of ClientError occurred, re-raise it
        print(f"Endpoint '{endpoint_name}' described some error: {e}")
        raise