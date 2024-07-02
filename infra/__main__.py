import pulumi
import pulumi_aws as aws
import json

# Create VPC
vpc = aws.ec2.Vpc("my-vpc",
                  cidr_block="10.0.0.0/16",
                  tags={"Name": "my-vpc"})

# Create Internet Gateway
igw = aws.ec2.InternetGateway("my-vpc-igw",
                              vpc_id=vpc.id,
                              opts=pulumi.ResourceOptions(depends_on=[vpc]),
                              tags={"Name": "my-vpc-igw"})

# Create Route Table for Public Subnet
public_route_table = aws.ec2.RouteTable("my-vpc-public-rt",
                                        vpc_id=vpc.id,
                                        routes=[{
                                            "cidr_block": "0.0.0.0/0",
                                            "gateway_id": igw.id,
                                        }],
                                        opts=pulumi.ResourceOptions(depends_on=[igw]),
                                        tags={"Name": "my-vpc-public-rt"})

# Create Public Subnet within VPC for Grafana Tempo instance
public_subnet = aws.ec2.Subnet("public-subnet",
                               vpc_id=vpc.id,
                               cidr_block="10.0.1.0/24",
                               availability_zone="us-east-1a",
                               map_public_ip_on_launch=True,  # Enable automatic public IP assignment
                               opts=pulumi.ResourceOptions(depends_on=[vpc]),
                               tags={"Name": "public-subnet"})

# Associate Route Table with Public Subnet
public_route_table_association = aws.ec2.RouteTableAssociation("public-subnet-association",
                                                               subnet_id=public_subnet.id,
                                                               route_table_id=public_route_table.id,
                                                               opts=pulumi.ResourceOptions(depends_on=[public_route_table]))

# Create Security Group for Grafana Tempo instance
grafana_security_group = aws.ec2.SecurityGroup("grafana-security-group",
                                               vpc_id=vpc.id,
                                               description="Allow All traffic",
                                               ingress=[{
                                                  "protocol": "-1",  # All protocols
                                                  "from_port": 0,
                                                  "to_port": 0,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                               egress=[{
                                                   "protocol": "-1",  # All protocols
                                                   "from_port": 0,
                                                   "to_port": 0,
                                                   "cidr_blocks": ["0.0.0.0/0"],
                                               }],
                                               opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                               tags={"Name": "grafana-security-group"})

# Create EC2 Instance for Grafana, Tempo, and OTEL
ec2_instance = aws.ec2.Instance("grafana-tempo-otel",
                                instance_type="t2.micro",
                                ami="ami-04b70fa74e45c3917",  # Ubuntu 24.04 AMI
                                subnet_id=public_subnet.id,
                                vpc_security_group_ids=[grafana_security_group.id],
                                associate_public_ip_address=True,  # Ensure public IP is associated
                                tags={"Name": "grafana-tempo-otel"})

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

# Attach Policies to Role
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

# Attach additional policies for EC2 network interface creation and management
lambda_role_policy_attachment_ec2 = aws.iam.RolePolicyAttachment("lambdaRolePolicyAttachmentEC2",
                                                                 role=lambda_role.name,
                                                                 policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole")

# Create S3 Bucket
bucket_name = "lambda-function-bucket-poridhi"
bucket = aws.s3.Bucket(bucket_name)

# Create Private Subnet within VPC for Lambda function
private_subnet = aws.ec2.Subnet("private-subnet",
                                vpc_id=vpc.id,
                                cidr_block="10.0.2.0/24",
                                availability_zone="us-east-1a",
                                map_public_ip_on_launch=False,  # Disable automatic public IP assignment
                                opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                tags={"Name": "private-subnet"})

# Create Route Table for Private Subnet
private_route_table = aws.ec2.RouteTable("my-vpc-private-rt",
                                         vpc_id=vpc.id,
                                         routes=[{
                                             "cidr_block": "0.0.0.0/0",
                                             "gateway_id": igw.id,  # Modify as per your requirements for a NAT Gateway or another route
                                         }],
                                         opts=pulumi.ResourceOptions(depends_on=[igw]),
                                         tags={"Name": "my-vpc-private-rt"})

# Associate Route Table with Private Subnet
private_route_table_association = aws.ec2.RouteTableAssociation("private-subnet-association",
                                                                subnet_id=private_subnet.id,
                                                                route_table_id=private_route_table.id,
                                                                opts=pulumi.ResourceOptions(depends_on=[private_route_table]))

# Create Security Group for Lambda function
lambda_security_group = aws.ec2.SecurityGroup("lambda-security-group",
                                              vpc_id=vpc.id,
                                              description="Allow all traffic",
                                              ingress=[{
                                                  "protocol": "-1",  # All protocols
                                                  "from_port": 0,
                                                  "to_port": 0,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                              egress=[{
                                                  "protocol": "-1",  # All protocols
                                                  "from_port": 0,
                                                  "to_port": 0,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                              opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                              tags={"Name": "lambda-security-group"})

# Create IAM Role for GitHub Actions
github_actions_role = aws.iam.Role("github-actions-role",
                                   assume_role_policy=json.dumps({
                                       "Version": "2012-10-17",
                                       "Statement": [
                                           {
                                               "Effect": "Allow",
                                               "Principal": {
                                                   "Service": "actions.amazonaws.com"
                                               },
                                               "Action": "sts:AssumeRole"
                                           }
                                       ]
                                   }))

# S3 policy with dynamic values
bucket_arn = bucket.arn.apply(lambda arn: arn)
bucket_arn_with_wildcard = bucket.arn.apply(lambda arn: f"{arn}/*")

s3_policy_document = pulumi.Output.all(bucket_arn, bucket_arn_with_wildcard).apply(lambda args: json.dumps({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                args[0],
                args[1]
            ]
        }
    ]
}))

s3_policy = aws.iam.Policy("s3Policy",
    policy=s3_policy_document
)

# Attach Policies to GitHub Actions Role
github_actions_role_policy_attachment = aws.iam.RolePolicyAttachment("githubActionsRolePolicyAttachment",
                                                                     role=github_actions_role.name,
                                                                     policy_arn=s3_policy.arn)

# Export outputs
pulumi.export("bucket_name", bucket.bucket)
pulumi.export("bucket_arn", bucket.arn)
pulumi.export("vpc_id", vpc.id)
pulumi.export("igw_id", igw.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("ec2_instance_id", ec2_instance.id)
pulumi.export("ec2_instance_public_ip", ec2_instance.public_ip)
pulumi.export("ec2_instance_private_ip", ec2_instance.private_ip)
pulumi.export("lambda_role_arn", lambda_role.arn)
pulumi.export("grafana_security_group_id", grafana_security_group.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("private_route_table_id", private_route_table.id)
pulumi.export("lambda_security_group_id", lambda_security_group.id)
pulumi.export("github_actions_role_arn", github_actions_role.arn)
