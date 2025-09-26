import boto3
import json
import time
import os
from PIL import Image
import sys
import argparse

# You need to login to aws account before being able to use the endpoints
# export AWS_PROFILE=722568544242_AWS-Workloads-CTO
# export AWS_ACCESS_KEY_ID="******************" # paste the AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN from aws sso console
# export AWS_SECRET_ACCESS_KEY="******************"
# export AWS_SESSION_TOKEN="******************"
# aws configure list # check the credentials are valid

# Initialize the SageMaker client
client = boto3.client('sagemaker-runtime')

parser = argparse.ArgumentParser(description="Set the environment.")
parser.add_argument('--env', type=str, default='dev', choices=['dev', 'stage', 'prod', 'test'], help='Environment: "dev", "test", "stage" or "prod"')

# Avoid unittest argument conflict
args, _ = parser.parse_known_args()

# Determine bucket based on environment
if args.env == 'dev' or args.env == 'test':
    bucket = 'defender-image-reverse-search-4242'
elif args.env == 'stage':
    bucket = 'defender-image-reverse-search-8058'
elif args.env == 'prod':
    bucket = 'defender-image-reverse-search-1445'
else:
    raise ValueError("Invalid environment selection")


# image_dir = "assets"
# image_name = "trudeau-3ppl.jpg"
# image_path = os.path.join(image_dir, image_name)

# Load your image file
# with open(image_path, "rb") as f:
#     payload = bytearray(f.read())

# Specify the SageMaker endpoint and content type
# endpoint_name = "defenderImageAnalyzerEndpoint"
endpoint_name = "defenderImageAnalyzerEndpointC5i"
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