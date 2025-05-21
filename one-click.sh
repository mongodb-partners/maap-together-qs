#!/bin/ksh
export AWS_ACCESS_KEY_ID="***************"
export AWS_SECRET_ACCESS_KEY="***************"
export AWS_SESSION_TOKEN="***************"

# Variables
INFRA_STACK_NAME="MAAP-Together-Stack-Infrastructure"
EC2_STACK_NAME="MAAP-Together-Stack-Compute"
ECRImageURI="public.ecr.aws/s2e1n3u8/mongodb-together:latest"
INFRA_TEMPLATE_FILE="deploy-infra.yaml"
EC2_TEMPLATE_FILE="deploy-ec2.yaml"

AWS_REGION=$(aws configure get region)
AWS_Zone="a"  #Subnet and Server AWS Availability Zone
AvailabilityZone="$AWS_REGION$AWS_Zone"
EC2_INSTANCE_TYPE="t3.xlarge"
ServerInstanceProfile="MAAPTogetherServerInstanceProfile"

INITIAL_INSTANCE_COUNT="1"
VolumeSize=100

GIT_REPO_URL="https://github.com/mongodb-partners/maap-together-qs.git"

TAG_NAME="MAAP-Together-One-Click"
ENDPOINT_NAME="One-Click-Endpoint-Together"

MongoDBClusterName="MongoDBTogetherV1"
MongoDBUserName="admin"
MongoDBPassword="pass123"
APIPUBLICKEY="*****************"
APIPRIVATEKEY="*****************"
GROUPID="*****************"
TOGETHER_API_KEY="*****************"

# Log file setup
LOG_FILE="./logs/one-click-deployment.log"
EC2_LIVE_LOG_FILE="./logs/ec2-live-logs.log"

# Initialize log
mkdir -p logs

log_message() {
    print "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a $LOG_FILE
}

# Log start of deployment
log_message "Deployment script started."
log_message "AWS Region: $AWS_REGION"

create_key()
{
  # Parameters
  KEY_NAME="MAAPTogetherKeyV2"  # You can change the key pair name as desired
  KEY_FILE="${KEY_NAME}.pem"

  # Check if the key pair exists
  EXISTING_KEY=$(aws ec2 describe-key-pairs --key-names "$KEY_NAME" --query "KeyPairs[0].KeyName" --output text 2>/dev/null)

  if [[ "$EXISTING_KEY" == "$KEY_NAME" ]]; then
    log_message "Key pair $KEY_NAME already exists. Using existing key."
  else
    # Create the key pair
    aws ec2 create-key-pair --key-name "$KEY_NAME" --query "KeyMaterial" --output text > "$KEY_FILE"
    chmod 400 "$KEY_FILE"
    log_message "Key pair created and saved to $KEY_FILE"
  fi
}

deploy_infra()
{
  # Deploy the CloudFormation stack
  log_message "Deploying CloudFormation stack: $INFRA_STACK_NAME..."
  log_message "$(aws cloudformation deploy \
    --template-file "$INFRA_TEMPLATE_FILE" \
    --stack-name "$INFRA_STACK_NAME" \
    --region "$AWS_REGION" \
    --parameter-overrides \
      AvailabilityZone="$AvailabilityZone" \
      ServerInstanceProfile="$ServerInstanceProfile" \
    --capabilities CAPABILITY_NAMED_IAM)"

  # Check deployment status
  if [[ $? -ne 0 ]]; then
    log_message "Error: Failed to deploy the stack."
    exit 1
  fi

  log_message "CloudFormation stack $INFRA_STACK_NAME deployed successfully."

  # Retrieve outputs for reference
  log_message "Fetching stack outputs..."
  log_message "\n$(aws cloudformation describe-stacks \
    --stack-name "$INFRA_STACK_NAME" \
    --query "Stacks[0].Outputs" \
    --output table --region "$AWS_REGION")"

  # Retrieve and store stack outputs in variables

  VPC_ID=$(aws cloudformation describe-stacks \
    --stack-name "$INFRA_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='VPCID'].OutputValue" \
    --output text --region "$AWS_REGION")

  SUBNET_ID=$(aws cloudformation describe-stacks \
    --stack-name "$INFRA_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='SubnetID'].OutputValue" \
    --output text --region "$AWS_REGION")

  SECURITY_GROUP_ID=$(aws cloudformation describe-stacks \
    --stack-name "$INFRA_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='SecurityGroupID'].OutputValue" \
    --output text --region "$AWS_REGION")

  IAM_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$INFRA_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='IAMRoleARN'].OutputValue" \
    --output text --region "$AWS_REGION")

  IAM_INSTANCE_PROFILE=$(aws cloudformation describe-stacks \
    --stack-name "$INFRA_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='IAMInstanceProfile'].OutputValue" \
    --output text --region "$AWS_REGION")

  # Check if the variables were successfully populated
  if [[ -z "$VPC_ID" || -z "$SUBNET_ID" || -z "$SECURITY_GROUP_ID" || -z "$IAM_ROLE_ARN" || -z "$IAM_INSTANCE_PROFILE" ]]; then
    log_message "Error: One or more stack outputs were not retrieved correctly."
    exit 1
  fi

  # log_message the retrieved variables for confirmation
  log_message "INFRA Stack Outputs:"
  log_message "VPC ID: $VPC_ID"
  log_message "Subnet ID: $SUBNET_ID"
  log_message "Security Group ID: $SECURITY_GROUP_ID"
  log_message "IAM Role ARN: $IAM_ROLE_ARN"
  log_message "IAM Instance Profile: $IAM_INSTANCE_PROFILE"

}


deploy_ec2()
{
  typeset -A ami_map # Image name: "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-20240927" (Ubuntu Server 22.04 LTS (HVM) SSD Volume Type)
  ami_map=(
      ["ap-northeast-1"]="ami-0ac6b9b2908f3e20d"
      ["ap-northeast-2"]="ami-042e76978adeb8c48"
      ["ap-south-1"]="ami-09b0a86a2c84101e1"
      ["ap-southeast-1"]="ami-03fa85deedfcac80b"
      ["ap-southeast-2"]="ami-040e71e7b8391cae4"
      ["ca-central-1"]="ami-00498a47f0a5d4232"
      ["eu-central-1"]="ami-0745b7d4092315796"
      ["eu-north-1"]="ami-089146c5626baa6bf"
      ["eu-west-1"]="ami-0a422d70f727fe93e"
      ["eu-west-2"]="ami-03ceeb33c1e4abcd1"
      ["eu-west-3"]="ami-07db896e164bc4476"
      ["sa-east-1"]="ami-036f48ec20249562a"
      ["us-east-1"]="ami-005fc0f236362e99f"
      ["us-east-2"]="ami-00eb69d236edcfaf8"
      ["us-west-1"]="ami-0819a8650d771b8be"
      ["us-west-2"]="ami-0b8c6b923777519db"
  )

  # Validate the region
  if [[ -z "${ami_map[$AWS_REGION]}" ]]; then
      log_message "Error: AMI ID not available for region $AWS_REGION."
      exit 1
  fi

  # Get the AMI ID for the current region
  AMI_ID=${ami_map[$AWS_REGION]}
  log_message "AMI ID: $AMI_ID"

  # Deploy the CloudFormation stack
  log_message "Deploying CloudFormation stack: $EC2_STACK_NAME..."
  log_message "$(aws cloudformation create-stack \
    --stack-name "$EC2_STACK_NAME" \
    --template-body "file://$EC2_TEMPLATE_FILE" \
    --parameters \
      ParameterKey=KeyName,ParameterValue="$KEY_NAME" \
      ParameterKey=SubnetId,ParameterValue="$SUBNET_ID" \
      ParameterKey=AMIId,ParameterValue="$AMI_ID" \
      ParameterKey=SecurityGroupId,ParameterValue="$SECURITY_GROUP_ID" \
      ParameterKey=IAMInstanceProfile,ParameterValue="$IAM_INSTANCE_PROFILE" \
      ParameterKey=GitRepoURL,ParameterValue="$GIT_REPO_URL" \
      ParameterKey=MongoDBClusterName,ParameterValue="$MongoDBClusterName" \
      ParameterKey=MongoDBUserName,ParameterValue="$MongoDBUserName" \
      ParameterKey=MongoDBPassword,ParameterValue="$MongoDBPassword" \
      ParameterKey=APIPUBLICKEY,ParameterValue="$APIPUBLICKEY" \
      ParameterKey=APIPRIVATEKEY,ParameterValue="$APIPRIVATEKEY" \
      ParameterKey=AWSRegion,ParameterValue="$AWS_REGION" \
      ParameterKey=InstanceType,ParameterValue="$EC2_INSTANCE_TYPE" \
      ParameterKey=AvailabilityZone,ParameterValue="$AvailabilityZone" \
      ParameterKey=VolumeSize,ParameterValue=$VolumeSize \
      ParameterKey=ECRImageURI,ParameterValue=$ECRImageURI \
      ParameterKey=TogetherAPI,ParameterValue=$TOGETHER_API_KEY \
      ParameterKey=GROUPID,ParameterValue="$GROUPID")"


  log_message "CloudFormation stack creation initiated. Waiting for stack to complete..."

  # Wait for stack creation to complete
  log_message "$(aws cloudformation wait stack-create-complete --stack-name "$EC2_STACK_NAME" --region "$AWS_REGION")"

  if [ $? -ne 0 ]; then
    log_message "Error: Stack creation failed."
    exit 1
  fi

  log_message "EC2 Deployment complete."

  # Retrieve stack outputs
  log_message "Retrieving stack outputs..."
  log_message "\n$(aws cloudformation describe-stacks \
    --stack-name "$EC2_STACK_NAME" \
    --query "Stacks[0].Outputs" \
    --output table)"



  URL=$(aws cloudformation describe-stacks \
    --stack-name "$EC2_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='EC2PublicIP'].OutputValue" \
    --output text)

  FULL_URL="http://$URL:7860"
  #TODO: Add the URL to env file

  log_message "The application will be available at $FULL_URL once all the deployment is complete."

}


log_ec2_message() {
    print "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a $EC2_LIVE_LOG_FILE
}
# Function to read logs from EC2

read_logs() {
  log_message "Starting to read logs from EC2 $URL..."   
  sleep 30
  ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" "ubuntu@$URL" "tail -f -n +1 deployment.log" | while read -r line; do
    log_ec2_message "$line"
  done &

  SSH_PID=$!
}


create_key

deploy_infra

deploy_ec2

# Start reading EC2 logs
read_logs


# Monitor URL status in the foreground
while true; do
  if curl --silent --head --fail "$FULL_URL"; then
    log_message "The application is now live at $FULL_URL. Launching..."
    # Launch the URL in the default web browser
    open "$FULL_URL" &>/dev/null || xdg-open "$FULL_URL" || log_message "Please open $FULL_URL in your browser."
    sleep 30
    kill "$SSH_PID" &>/dev/null
    log_message "Completed."
    break
  else
    log_message "Waiting for the application to be up..."
    sleep 60  # Wait for 60 seconds before checking again
  fi
done