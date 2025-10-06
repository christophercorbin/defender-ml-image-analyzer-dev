import boto3
import json
import time
import os
from PIL import Image
import sys
import argparse

# Authentication Setup
# Ensure AWS credentials are configured before running tests:
# 1. Configure AWS CLI: aws configure
# 2. Or use environment variables: AWS_PROFILE, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# 3. Or use IAM roles for EC2/Lambda execution

# Initialize the SageMaker client
client = boto3.client('sagemaker-runtime')

parser = argparse.ArgumentParser(description="Set the environment.")
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod', 'test'], help='Environment: "dev", "test", "stage" or "prod"')

# Avoid unittest argument conflict
args, _ = parser.parse_known_args()

# Environment-specific S3 bucket configuration
# In production, these would be loaded from environment variables or AWS Parameter Store
env_buckets = {
    'dev': 'soc2-ml-image-analyzer-dev-{{DEV_ACCOUNT_ID}}',
    'test': 'soc2-ml-image-analyzer-test-{{DEV_ACCOUNT_ID}}',
    'stage': 'soc2-ml-image-analyzer-stage-{{STAGE_ACCOUNT_ID}}',
    'prod': 'soc2-ml-image-analyzer-prod-{{PROD_ACCOUNT_ID}}'
}

if args.env in env_buckets:
    bucket = env_buckets[args.env]
else:
    raise ValueError(f"Invalid environment selection: {args.env}")


# image_dir = "assets"
# image_name = "trudeau-3ppl.jpg"
# image_path = os.path.join(image_dir, image_name)

# Load your image file
# with open(image_path, "rb") as f:
#     payload = bytearray(f.read())

# Specify the SageMaker endpoint and content type
endpoint_name = "soc2MlImageAnalyzerEndpointC5i"
content_type = "application/json"

payload = {
    "bucket": bucket,
    "key": "trudeau3.jpg"
}

for i in range(100): # simulate processing per user
    # Start the timer
    start_time = time.time()

    # Make the inference request
    response = client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType=content_type,
        # Body=payload
        Body=json.dumps(payload).encode('utf-8')
    )

    # Decode the result
    result = json.loads(response['Body'].read().decode())

    # Stop the timer and print the elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Check for error and exit if found
    if 'error' in result:
        print(f"Error in iteration {i+1}: {result}")
        sys.exit(1)

    # print(f"Elapsed time: {elapsed_time} seconds")
    print(f"Iteration {i+1}, took {elapsed_time} seconds, # faces: {len(result)}")

# Open the image file
# img = Image.open(image_path)

# # Loop through faces and crop
# for i, face in enumerate(result):
#     x = face["facial_area"]["x"]
#     y = face["facial_area"]["y"]
#     w = face["facial_area"]["w"]
#     h = face["facial_area"]["h"]

#     # Crop the image
#     img_cropped = img.crop((x, y, x + w, y + h))

#     # Save the cropped face
#     img_cropped.save(f"{image_path}-{i+1}.jpg")



# # Specify the name of your endpoint
# endpoint_name = "defenderImageAnalyzerEndpoint"

# # Sample payload (for example, image encoded as base64, or other formats based on your model)
# payload = json.dumps({"key": "value"})

# # Content type can be "application/json", "text/csv", etc.
# content_type = "application/json"

# # Invoke the endpoint
# response = sagemaker_runtime.invoke_endpoint(
#     EndpointName=endpoint_name,
#     ContentType=content_type,
#     Body=payload
# )

# # Read the inference result
# result = json.loads(response['Body'].read().decode())

# print(result)

###### Initialize the SageMaker client
# client = boto3.client('sagemaker')

# # Check the endpoint status
# response = client.describe_endpoint(EndpointName='defenderImageAnalyzerEndpoint')
# status = response['EndpointStatus']

# print("Endpoint Status:", status)