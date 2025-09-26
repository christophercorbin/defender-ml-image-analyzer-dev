#!/usr/bin/env python3
"""
Enhanced verification script for SageMaker endpoint image deployment
This script provides better verification than the current pipeline logic
"""

import boto3
import argparse
import sys
from botocore.exceptions import ClientError

def get_ecr_latest_digest(ecr_client, repository_name):
    """Get the latest image digest from ECR"""
    try:
        response = ecr_client.describe_images(
            repositoryName=repository_name,
            imageIds=[{'imageTag': 'latest'}]
        )
        if response['imageDetails']:
            return response['imageDetails'][0]['imageDigest']
        else:
            raise Exception("No image found with 'latest' tag")
    except ClientError as e:
        raise Exception(f"Error fetching ECR image digest: {e}")

def get_sagemaker_deployed_digest(sagemaker_client, endpoint_name):
    """Get the actual deployed image digest from SageMaker endpoint"""
    try:
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        if response['EndpointStatus'] != 'InService':
            raise Exception(f"Endpoint {endpoint_name} is not InService. Status: {response['EndpointStatus']}")
        
        deployed_images = response['ProductionVariants'][0]['DeployedImages']
        if not deployed_images:
            raise Exception(f"No deployed images found for endpoint {endpoint_name}")
        
        resolved_image = deployed_images[0]['ResolvedImage']
        
        # Extract digest from resolved image URL
        if '@sha256:' in resolved_image:
            return resolved_image.split('@')[1]
        else:
            raise Exception(f"Resolved image is not using digest format: {resolved_image}")
            
    except ClientError as e:
        raise Exception(f"Error fetching SageMaker endpoint info: {e}")

def main():
    parser = argparse.ArgumentParser(description="Verify SageMaker endpoint deployment")
    parser.add_argument('--endpoint-name', required=True, help='SageMaker endpoint name')
    parser.add_argument('--repository-name', default='defender-image-analyzer', help='ECR repository name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--expected-digest', help='Expected image digest (if known)')
    args = parser.parse_args()

    # Initialize clients
    sagemaker = boto3.client('sagemaker', region_name=args.region)
    ecr = boto3.client('ecr', region_name=args.region)

    print(f"🔍 Verifying deployment for endpoint: {args.endpoint_name}")
    print(f"📦 ECR repository: {args.repository_name}")
    print(f"🌍 Region: {args.region}")
    print("-" * 50)

    try:
        # Get ECR latest digest
        print("📥 Fetching latest ECR image digest...")
        ecr_digest = get_ecr_latest_digest(ecr, args.repository_name)
        print(f"ECR Latest Digest: {ecr_digest}")

        # Get SageMaker deployed digest  
        print("🚀 Fetching SageMaker deployed image digest...")
        sagemaker_digest = get_sagemaker_deployed_digest(sagemaker, args.endpoint_name)
        print(f"SageMaker Deployed Digest: {sagemaker_digest}")

        print("-" * 50)

        # Compare digests
        if ecr_digest == sagemaker_digest:
            print("✅ SUCCESS: Image digests match!")
            print("🎉 SageMaker endpoint is running the latest ECR image.")
            exit_code = 0
        else:
            print("❌ FAILURE: Image digest mismatch!")
            print(f"ECR Digest:       {ecr_digest}")
            print(f"SageMaker Digest: {sagemaker_digest}")
            print("💡 SageMaker endpoint is running an outdated image.")
            exit_code = 1

        # Additional check if expected digest was provided
        if args.expected_digest:
            print(f"\n🎯 Expected Digest: {args.expected_digest}")
            if sagemaker_digest == args.expected_digest:
                print("✅ SageMaker digest matches expected digest")
            else:
                print("❌ SageMaker digest does NOT match expected digest")
                exit_code = 1

        sys.exit(exit_code)

    except Exception as e:
        print(f"💥 ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()