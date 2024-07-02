import pulumi
import pulumi_aws as aws

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

# Attach additional policies for EC2 network interface creation and management fasfa
lambda_role_policy_attachment_ec2 = aws.iam.RolePolicyAttachment("lambdaRolePolicyAttachmentEC2",
                                                                 role=lambda_role.name,
                                                                 policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole")

# Create S3 Bucket
import pulumi
import pulumi_aws as aws

# Explicitly specify the bucket name
bucket_name = "lambda-function-bucket-poridhi"

# Create S3 Bucket
bucket = aws.s3.Bucket(bucket_name)

pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
# Export outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("igw_id", igw.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("ec2_instance_id", ec2_instance.id)
pulumi.export("ec2_instance_public_ip", ec2_instance.public_ip)
pulumi.export("ec2_instance_private_ip", ec2_instance.private_ip)

pulumi.export("lambda_role_arn", lambda_role.arn)
pulumi.export("grafana_security_group_id", grafana_security_group.id)
