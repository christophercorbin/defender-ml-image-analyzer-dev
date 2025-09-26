# Deepface releases
This endpoint's model comes from the Deepface package
https://github.com/serengil/deepface/releases

# Update the model & endpoint
Run the following to build the image
For 4242 (dev)
```
export AWS_PROFILE=722568544242_AWS-Workloads-CTO
export AWS_ACCESS_KEY_ID="******************" # paste the AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN from aws sso console
export AWS_SECRET_ACCESS_KEY="******************"
export AWS_SESSION_TOKEN="******************"
aws configure list # check the credentials are valid
aws ecr get-login-password # get the security token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.us-east-1.amazonaws.com # login to docker 
# optional steps (if running on local dev machine)
docker rmi -f dme-image-analyzer # remove previously built image (might contain outdated, vulnerable packages)
docker system prune # to remove cache
docker build -t dme-image-analyzer .
```
For 8058 (stage: no need to run the below if the image was already built by ^)
```
export AWS_PROFILE=517812868058_AWS-Workloads-CTO
export AWS_ACCESS_KEY_ID="******************" # paste the AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN from aws sso console
export AWS_SECRET_ACCESS_KEY="******************"
export AWS_SESSION_TOKEN="******************"
aws configure list # check the credentials are valid
aws ecr get-login-password # get the security token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.us-east-1.amazonaws.com # login to docker 
docker build -t dme-image-analyzer .
```
For 1445 (prod: no need to run the below if the image was already built by ^)
```
export AWS_PROFILE=770820631445_AWS-Workloads-CTO
export AWS_ACCESS_KEY_ID="******************" # paste the AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN from aws sso console
export AWS_SECRET_ACCESS_KEY="******************"
export AWS_SESSION_TOKEN="******************"
aws configure list # check the credentials are valid
aws ecr get-login-password # get the security token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.us-east-1.amazonaws.com # login to docker 
docker build -t dme-image-analyzer .
```

## Test the model image is built correctly by running the docker container locally
```
docker run -p 8080:8080 dme-image-analyzer
docker run -p 8080:8080 -it --rm dme-image-analyzer
# make sure container boots up without any errors
# in a separate shell, ping the endpoint, make sure it returns pong
curl -X GET localhost:8080/ping
curl -X GET localhost:8080/test # Verify response contains 3 faces and an embedding for each
```

Run the following to tag and push the updated model to AWS ECR
For 4242 (dev)
```
export AWS_PROFILE=722568544242_AWS-Workloads-CTO
aws configure list # check the credentials
aws ecr get-login-password # get the security token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 722568544242.dkr.ecr.us-east-1.amazonaws.com # login to docker 
docker tag dme-image-analyzer:latest 722568544242.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest
docker push 722568544242.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest
```
For 8058 (stage)
```
export AWS_PROFILE=517812868058_AWS-Workloads-CTO
aws configure list # check the credentials
aws ecr get-login-password # get the security token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 517812868058.dkr.ecr.us-east-1.amazonaws.com # login to docker 
docker tag dme-image-analyzer:latest 517812868058.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest
docker push 517812868058.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest
```

For 1445 (prod)
```
export AWS_PROFILE=770820631445_CTODevelopers
aws configure list # check the credentials
aws ecr get-login-password # get the security token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 770820631445.dkr.ecr.us-east-1.amazonaws.com # login to docker 
docker tag dme-image-analyzer:latest 770820631445.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest
docker push 770820631445.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest
```

Delete the existing models from SageMaker Console (both 3046 and 1445)

Run the following to create new model and update the endpoint in SageMaker
For 4242 (dev)
```
export AWS_PROFILE=722568544242_CTODevelopers
aws configure list # check the credentials
python3 model/create.py --env dev
python3 model/update_endpoint_c6i2x.py --env dev
python3 model/update_endpoint_c5i.py --env dev
python3 model/update_endpoint_c6i2x.py --env test
python3 model/update_endpoint_c5i.py --env test

# Make sure response from each results in 200
```

For 8058
```
export AWS_PROFILE=517812868058_CTODevelopers
aws configure list # check the credentials
python3 model/create.py --env stage
python3 model/update_endpoint_c6i2x.py --env stage
python3 model/update_endpoint_c5i.py --env stage

# Make sure response from each results in 200
```
For 1445
```
export AWS_PROFILE=770820631445_CTODevelopers
aws configure list # check the credentials
python3 model/create.py --env prod
python3 model/update_endpoint_c6i2x.py --env prod
python3 model/update_endpoint_c5i.py --env prod

# Make sure response from each results in 200
```

## Verfication
### Ensures that the endpoints updated/created are running the latest version with good status
For example:
```
aws sagemaker describe-endpoint --region us-east-1 --endpoint-name defenderImageAnalyzerEndpointC5i --output json
{
    "EndpointName": "defenderImageAnalyzerEndpointC5i",
    "EndpointArn": "arn:aws:sagemaker:us-east-1:722568544242:endpoint/defenderImageAnalyzerEndpointC5i",
    "EndpointConfigName": "defenderImageAnalyzerEndpointC5i-20250203-1007",
    "ProductionVariants": [
        {
            "VariantName": "AllTraffic",
            "DeployedImages": [
                {
                    "SpecifiedImage": "722568544242.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer:latest",
                    "ResolvedImage": "722568544242.dkr.ecr.us-east-1.amazonaws.com/defender-image-analyzer@sha256:d5417e938cb9c129c079266dc5ee1e2531ac249a9c94ad3053bb7f2a3330b662",
                    "ResolutionTime": 1738606042.64
                }
            ],
            "CurrentWeight": 1.0,
            "DesiredWeight": 1.0,
            "CurrentInstanceCount": 1,
            "DesiredInstanceCount": 1
        }
    ],
    "EndpointStatus": "InService",
    "CreationTime": 1736877690.051,
    "LastModifiedTime": 1738606460.335
}

# The latest tag from "SpecifiedImage" in ECR has the same hash as the one in "ResolvedImage"
# Endpoint status says: "InService"
# "FailureReason": This field does not present
```
### Testing


# Troubleshooting
```
# Describe model
aws sagemaker describe-model --model-name defenderImageAnalyzer --region us-east-1 --output json

# Describe endpoint
aws sagemaker describe-endpoint --endpoint-name defenderImageAnalyzerEndpointC5i --region us-east-1 --output json

# List endpoint configuration
aws sagemaker list-endpoint-configs --region us-east-1 --output json

# Describe autoscaling policy
aws application-autoscaling describe-scaling-policies --service-namespace sagemaker --resource-id endpoint/defenderImageAnalyzerEndpointC5i-test/variant/AllTraffic  --region us-east-1

# Describe autoscaling activities
aws application-autoscaling describe-scaling-activities --service-namespace sagemaker --resource-id endpoint/defenderImageAnalyzerEndpointC5i/variant/AllTraffic --scalable-dimension sagemaker:variant:DesiredInstanceCount --region us-east-1 --max-items 3 --output json



```

# To check if the Scaling policy for the endpoint is registerd
aws application-autoscaling describe-scalable-targets \
  --service-namespace sagemaker \
  --resource-ids endpoint/defenderImageAnalyzerEndpointC5i/variant/AllTraffic \
  --region us-east-1 --output json

aws application-autoscaling describe-scalable-targets \
  --service-namespace sagemaker \
  --resource-ids endpoint/defenderImageAnalyzerEndpointC6i2x/variant/AllTraffic \
  --region us-east-1 --output json

# add a custome policy for auto-scaling for faster scale-in/out
aws application-autoscaling put-scaling-policy \
  --policy-name defenderImageAnalyzerEndpointC5i-scaling-policy \
  --service-namespace sagemaker \
  --resource-id endpoint/defenderImageAnalyzerEndpointC5i/variant/AllTraffic \
  --scalable-dimension sagemaker:variant:DesiredInstanceCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 5.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "SageMakerVariantConcurrentRequestsPerModelHighResolution"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 600
  }' \
  --region us-east-1

aws application-autoscaling put-scaling-policy \
  --policy-name defenderImageAnalyzerEndpointC6i2x-scaling-policy \
  --service-namespace sagemaker \
  --resource-id endpoint/defenderImageAnalyzerEndpointC5i/variant/AllTraffic \
  --scalable-dimension sagemaker:variant:DesiredInstanceCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 5.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "SageMakerVariantConcurrentRequestsPerModelHighResolution"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 600
  }' \
  --region us-east-1

  Security Updates - 2025-09-04
  Security Updates - 2025-09-16
  
