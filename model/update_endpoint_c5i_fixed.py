import boto3
from datetime import datetime
from botocore.exceptions import ClientError
import argparse
import time

# Get arguments
parser = argparse.ArgumentParser(description="Set the environment.")
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod', 'test', 'personal', 'soc2'], help='Environment: "dev", "stage", "prod", "test", "personal", or "soc2"')
args = parser.parse_args()

print(f'Creating / Updating endpoint for: {args.env}')

# Initialize SageMaker client
sagemaker = boto3.client('sagemaker', region_name='us-east-1')

if args.env == 'personal':
    model_name = 'defenderImageAnalyzerPersonal'
    endpoint_name = 'defenderImageAnalyzerPersonalC5i'
elif args.env == 'soc2':
    model_name = 'defenderImageAnalyzerSOC2Hardened'
    endpoint_name = 'defenderImageAnalyzerSOC2HardenedDev'  # Default to dev for SOC 2
else:
    model_name = 'defenderImageAnalyzer'
    if args.env in ['dev', 'stage', 'prod']:
        endpoint_name = 'defenderImageAnalyzerEndpointC5i'
    else:
        endpoint_name = 'defenderImageAnalyzerEndpointC5i-test'
timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')  # More precise timestamp
endpoint_config_name = f'{endpoint_name}-{timestamp}'

print(f'Endpoint config name: {endpoint_config_name}')

# Verify the model exists and get its details
try:
    model_response = sagemaker.describe_model(ModelName=model_name)
    model_image = model_response['PrimaryContainer']['Image']
    print(f'Model image: {model_image}')
    
    if '@sha256:' in model_image:
        print('✅ Model is using digest-based image reference')
    else:
        print('⚠️ Warning: Model is using tag-based image reference')
        
except ClientError as e:
    print(f'Error: Model {model_name} not found: {e}')
    raise

# Create endpoint configuration with explicit settings to force refresh
endpoint_config_response = sagemaker.create_endpoint_config(
    EndpointConfigName=endpoint_config_name,
    ProductionVariants=[{
        'InstanceType': 'ml.c5.large',
        'InitialInstanceCount': 1,
        'ModelName': model_name,
        'VariantName': 'AllTraffic',
        # Add explicit container startup health check
        'ModelDataDownloadTimeoutInSeconds': 3600,
        'ContainerStartupHealthCheckTimeoutInSeconds': 3600
    }]
)

print(f'Endpoint configuration created: {endpoint_config_response["EndpointConfigArn"]}')

try:
    # Check if endpoint exists
    existing_endpoint = sagemaker.describe_endpoint(EndpointName=endpoint_name)
    current_status = existing_endpoint['EndpointStatus']
    
    print(f"Endpoint '{endpoint_name}' exists with status: {current_status}")
    
    # If endpoint is updating, wait for it to complete first
    if current_status in ['Creating', 'Updating']:
        print('Endpoint is currently updating. Waiting for completion...')
        waiter = sagemaker.get_waiter('endpoint_in_service')
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 120  # Wait up to 60 minutes
            }
        )
        print('Previous update completed.')
    
    # Update the endpoint with the new configuration
    print(f"Updating endpoint with new configuration: {endpoint_config_name}")
    update_response = sagemaker.update_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=endpoint_config_name
    )
    print(f"Update initiated: {update_response}")
    
    # Wait for update to complete
    print('Waiting for endpoint update to complete...')
    waiter = sagemaker.get_waiter('endpoint_in_service')
    waiter.wait(
        EndpointName=endpoint_name,
        WaiterConfig={
            'Delay': 30,
            'MaxAttempts': 120  # Wait up to 60 minutes
        }
    )
    print('✅ Endpoint update completed successfully')
    
except ClientError as e:
    if e.response['Error']['Code'] == 'ValidationException':
        print(f"Endpoint '{endpoint_name}' does not exist. Creating...")
        create_response = sagemaker.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
        print(f"Endpoint creation initiated: {create_response}")
        
        # Wait for creation to complete
        print('Waiting for endpoint creation to complete...')
        waiter = sagemaker.get_waiter('endpoint_in_service')
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 120  # Wait up to 60 minutes
            }
        )
        print('✅ Endpoint created successfully')
    else:
        print(f"Error with endpoint '{endpoint_name}': {e}")
        raise

# Final verification
final_endpoint = sagemaker.describe_endpoint(EndpointName=endpoint_name)
final_image = final_endpoint['ProductionVariants'][0]['DeployedImages'][0]['ResolvedImage']
print(f'Final deployed image: {final_image}')

if '@sha256:' in final_image:
    deployed_digest = final_image.split('@')[1]
    print(f'✅ Endpoint is running with digest: {deployed_digest}')
else:
    print('⚠️ Warning: Endpoint is running with tag-based reference')

print(f'Endpoint {endpoint_name} is ready and updated!')