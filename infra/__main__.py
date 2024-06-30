from vpc import VPC
from subnet import PublicSubnet
from ecr_repository import ECRRepository
from lambda_role import LambdaRole
from security_group import SecurityGroup
from ec2_instance import EC2Instance

# Create the VPC and related resources
vpc = VPC("my-vpc", "10.0.0.0/16")

# Create public subnet
public_subnet = PublicSubnet("public-subnet", vpc.vpc.id, "10.0.1.0/24", "us-east-1a")

# Create ECR repository
ecr_repo = ECRRepository("my-lambda-function")

# Create Lambda role
lambda_role = LambdaRole("lambda-role")

# Create security group
lambda_security_group = SecurityGroup("lambda-security-group", vpc.vpc.id)

# Create EC2 instance in public subnet for Grafana Tempo
ec2_instance = EC2Instance("grafana-tempo", public_subnet.subnet.id, lambda_security_group.security_group.id)
