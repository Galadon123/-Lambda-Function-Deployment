import pulumi
import pulumi_aws as aws

# Create VPC
vpc = aws.ec2.Vpc("my-vpc",
                  cidr_block="10.0.0.0/16",
                  tags={"Name": "my-vpc"})

# Ensure VPC is created before creating other resources
vpc_created = vpc.id.apply(lambda _: True)

# Create Internet Gateway
igw = aws.ec2.InternetGateway("my-vpc-igw",
                              vpc_id=vpc.id,
                              opts=pulumi.ResourceOptions(depends_on=[vpc]),
                              tags={"Name": "my-vpc-igw"})

# Create Route Table
route_table = aws.ec2.RouteTable("my-vpc-public-rt",
                                 vpc_id=vpc.id,
                                 routes=[{
                                     "cidr_block": "0.0.0.0/0",
                                     "gateway_id": igw.id,
                                 }],
                                 opts=pulumi.ResourceOptions(depends_on=[igw]),
                                 tags={"Name": "my-vpc-public-rt"})

# Create Public Subnet within vpc
public_subnet = aws.ec2.Subnet("public-subnet",
                               vpc_id=vpc.id,
                               cidr_block="10.0.1.0/24",
                               availability_zone="us-east-1a",
                               opts=pulumi.ResourceOptions(depends_on=[vpc]),
                               tags={"Name": "public-subnet"})

# Associate Route Table with Subnet
route_table_association = aws.ec2.RouteTableAssociation("public-subnet-association",
                                                        subnet_id=public_subnet.id,
                                                        route_table_id=route_table.id,
                                                        opts=pulumi.ResourceOptions(depends_on=[route_table]))

# Create Security Groupfefgdfvsaedfgweafg
security_group = aws.ec2.SecurityGroup("lambda-security-group",
                                       vpc_id=vpc.id,
                                       description="Allow HTTP inbound traffic",
                                       ingress=[{
                                           "protocol": "tcp",
                                           "from_port": 80,
                                           "to_port": 80,
                                           "cidr_blocks": ["0.0.0.0/0"],
                                       }],
                                       opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                       tags={"Name": "lambda-security-group"})

# Create ECR Repository
ecr_repo = aws.ecr.Repository("my-lambda-function",
                              image_scanning_configuration={"scanOnPush": True},
                              tags={"Name": "my-lambda-function"})

# Create IAM Role for Lambda
lambda_role = aws.iam.Role("lambda-role",
                           assume_role_policy="""{
                               "Version": "2012-10-17",
                               "Statement": [
                                   {
                                       "Action": "sts:AssumeRole",
                                       "Principal": {
                                           "Service": "lambda.amazonaws.com"
                                       },
                                       "Effect": "Allow",
                                       "Sid": ""
                                   }
                               ]
                           }""")

# Attach Policy to Role
s3_policy = aws.iam.Policy("s3Policy",
                           policy="""{
                               "Version": "2012-10-17",
                               "Statement": [
                                   {
                                       "Effect": "Allow",
                                       "Action": "s3:GetObject",
                                       "Resource": "arn:aws:s3:::lambda-function-bucket-poridhi/pulumi-outputs.json"
                                   }
                               ]
                           }""")

lambda_role_policy_attachment = aws.iam.RolePolicyAttachment("lambdaRolePolicyAttachment",
                                                             role=lambda_role.name,
                                                             policy_arn=s3_policy.arn)

# Create EC2 Instance for Grafana Tempo
ec2_instance = aws.ec2.Instance("grafana-tempo",
                                instance_type="t2.micro",
                                ami="ami-04b70fa74e45c3917",  # Amazon Linux 2 AMI (HVM), SSD Volume Type
                                subnet_id=public_subnet.id,
                                vpc_security_group_ids=[security_group.id],
                                tags={"Name": "grafana-tempo"})

# Export outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("igw_id", igw.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("route_table_id", route_table.id)
pulumi.export("ec2_instance_id", ec2_instance.id)
pulumi.export("ecr_registry", ecr_repo.registry_id)
pulumi.export("lambda_role_arn", lambda_role.arn)
pulumi.export("ec2_instance_public_ip", ec2_instance.public_ip)
