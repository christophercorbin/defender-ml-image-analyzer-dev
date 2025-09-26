#!/usr/bin/env python3
"""
Local deployment script for testing the personal Defender Image Analyzer setup
This script helps you test the deployment process locally before using CI/CD
"""

import boto3
import argparse
import subprocess
import sys
import time
from botocore.exceptions import ClientError

def run_command(command, description=""):
    """Run a shell command and return the result"""
    print(f"🔄 {description}")
    print(f"   Command: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"   Error: {e.stderr}")
        raise

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials configured for account: {identity['Account']}")
        print(f"   User/Role: {identity['Arn']}")
        return identity['Account']
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        print("   Please run: aws configure")
        sys.exit(1)

def check_docker():
    """Check if Docker is running"""
    try:
        run_command("docker info", "Checking Docker")
        return True
    except:
        print("❌ Docker is not running. Please start Docker Desktop.")
        return False

def create_ecr_repository(ecr_client, repo_name, region):
    """Create ECR repository if it doesn't exist"""
    try:
        ecr_client.describe_repositories(repositoryNames=[repo_name])
        print(f"✅ ECR repository '{repo_name}' already exists")
    except ClientError as e:
        if e.response['Error']['Code'] == 'RepositoryNotFoundException':
            print(f"🔄 Creating ECR repository '{repo_name}'...")
            ecr_client.create_repository(repositoryName=repo_name)
            print(f"✅ ECR repository '{repo_name}' created")
        else:
            raise

def create_sagemaker_role(iam_client, account_id):
    """Create SageMaker execution role if it doesn't exist"""
    role_name = 'SageMaker-ExecutionRole'
    
    try:
        role = iam_client.get_role(RoleName=role_name)
        print(f"✅ SageMaker role '{role_name}' already exists")
        return role['Role']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"🔄 Creating SageMaker execution role...")
            
            # Trust policy for SageMaker
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "sagemaker.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            # Create the role
            role_response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=str(trust_policy).replace("'", '"'),
                Description='SageMaker execution role for personal defender image analyzer'
            )
            
            # Attach required policies
            policies = [
                'arn:aws:iam::aws:policy/AmazonSageMakerFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess',  # If you need S3 access
            ]
            
            for policy in policies:
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
            
            print(f"✅ SageMaker role '{role_name}' created")
            return role_response['Role']['Arn']
        else:
            raise

def main():
    parser = argparse.ArgumentParser(description="Local deployment for personal environment")
    parser.add_argument('--skip-build', action='store_true', help='Skip Docker build step')
    parser.add_argument('--skip-deploy', action='store_true', help='Skip SageMaker deployment')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()

    print("🚀 Personal Defender Image Analyzer - Local Deployment")
    print("=" * 55)

    # Check prerequisites
    account_id = check_aws_credentials()
    if not check_docker():
        sys.exit(1)

    # Configuration
    region = args.region
    ecr_repo = 'defender-image-analyzer-personal'
    model_name = 'defenderImageAnalyzerPersonal'
    endpoint_name = 'defenderImageAnalyzerPersonalC5i'

    # Initialize AWS clients
    ecr = boto3.client('ecr', region_name=region)
    iam = boto3.client('iam', region_name=region)
    
    print(f"🎯 Target Configuration:")
    print(f"   Account: {account_id}")
    print(f"   Region: {region}")
    print(f"   ECR Repository: {ecr_repo}")
    print(f"   SageMaker Model: {model_name}")
    print(f"   SageMaker Endpoint: {endpoint_name}")
    print()

    try:
        # Step 1: Setup AWS resources
        print("📋 Step 1: Setting up AWS resources...")
        create_ecr_repository(ecr, ecr_repo, region)
        role_arn = create_sagemaker_role(iam, account_id)
        print()

        if not args.skip_build:
            # Step 2: Build and push Docker image
            print("📋 Step 2: Building and pushing Docker image...")
            
            # Get ECR login
            login_cmd = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com"
            run_command(login_cmd, "Logging into ECR")
            
            # Also login to AWS ML registry for base image
            base_login_cmd = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin 763104351884.dkr.ecr.us-east-1.amazonaws.com"
            run_command(base_login_cmd, "Logging into AWS ML registry")
            
            # Build image
            image_tag = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{ecr_repo}:latest"
            build_cmd = f"docker build --platform linux/amd64 -t {image_tag} ."
            run_command(build_cmd, "Building Docker image")
            
            # Push image
            push_cmd = f"docker push {image_tag}"
            run_command(push_cmd, "Pushing Docker image to ECR")
            print()

        if not args.skip_deploy:
            # Step 3: Deploy to SageMaker
            print("📋 Step 3: Deploying to SageMaker...")
            
            # Get image digest
            print("🔍 Getting latest image digest...")
            images_response = ecr.describe_images(
                repositoryName=ecr_repo,
                imageIds=[{'imageTag': 'latest'}]
            )
            image_digest = images_response['imageDetails'][0]['imageDigest']
            print(f"   Image digest: {image_digest}")
            
            # Create model
            create_cmd = f"python3 model/create_fixed.py --env personal --image-digest {image_digest}"
            run_command(create_cmd, "Creating SageMaker model")
            
            # Update endpoint
            update_cmd = f"python3 model/update_endpoint_c5i_fixed.py --env personal"
            run_command(update_cmd, "Updating SageMaker endpoint")
            
            print("⏳ Waiting for endpoint deployment (this may take 5-10 minutes)...")
            time.sleep(60)  # Initial wait
            
            # Verify deployment
            verify_cmd = f"python3 verify_deployment.py --endpoint-name {endpoint_name} --repository-name {ecr_repo} --expected-digest {image_digest}"
            run_command(verify_cmd, "Verifying deployment")
            print()

        print("🎉 Local deployment completed successfully!")
        print("\n📋 Next steps:")
        print("1. Test your endpoint locally or through AWS Console")
        print("2. Push your code to GitHub to trigger the CI/CD pipeline")
        print("3. Set up GitHub secrets for AWS credentials")
        print(f"4. Your endpoint is available at: {endpoint_name}")

    except Exception as e:
        print(f"💥 Deployment failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()