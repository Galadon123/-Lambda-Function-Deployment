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

# Create Public Subnet within VPC c
public_subnet = aws.ec2.Subnet("public-subnet",
                               vpc_id=vpc.id,
                               cidr_block="10.0.1.0/24",
                               availability_zone="us-east-1a",
                               map_public_ip_on_launch=True,
                               opts=pulumi.ResourceOptions(depends_on=[vpc]),
                               tags={"Name": "public-subnet"})

# Associate Route Table with Public Subnet
public_route_table_association = aws.ec2.RouteTableAssociation("public-subnet-association",
                                                               subnet_id=public_subnet.id,
                                                               route_table_id=public_route_table.id,
                                                               opts=pulumi.ResourceOptions(depends_on=[public_route_table]))

# Create Security Group for EC2 Instance
ec2_security_group = aws.ec2.SecurityGroup("ec2-security-group",
                                           vpc_id=vpc.id,
                                           description="Allow SSH and HTTP traffic",
                                           ingress=[
                                               {
                                                   "protocol": "tcp",
                                                   "from_port": 22,
                                                   "to_port": 22,
                                                   "cidr_blocks": ["0.0.0.0/0"],
                                               },
                                               {
                                                   "protocol": "tcp",
                                                   "from_port": 80,
                                                   "to_port": 80,
                                                   "cidr_blocks": ["0.0.0.0/0"],
                                               },
                                           ],
                                           egress=[
                                               {
                                                   "protocol": "-1",
                                                   "from_port": 0,
                                                   "to_port": 0,
                                                   "cidr_blocks": ["0.0.0.0/0"],
                                               },
                                           ],
                                           opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                           tags={"Name": "ec2-security-group"})

ec2_instance = aws.ec2.Instance("my-ec2-instance",
                                instance_type="t2.micro",
                                vpc_security_group_ids=[ec2_security_group.id],
                                subnet_id=public_subnet.id,
                                ami="ami-04a81a99f5ec58529",  # Example AMI ID, replace with your desired AMIs
                                tags={"Name": "my-ec2-instance"},
                                opts=pulumi.ResourceOptions(depends_on=[public_subnet, ec2_security_group]))
# Create Private Subnet within VPC
private_subnet = aws.ec2.Subnet("private-subnet",
                                vpc_id=vpc.id,
                                cidr_block="10.0.2.0/24",
                                availability_zone="us-east-1b",
                                map_public_ip_on_launch=False,
                                opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                tags={"Name": "private-subnet"})

# Create Route Table for Private Subnet
private_route_table = aws.ec2.RouteTable("my-vpc-private-rt",
                                         vpc_id=vpc.id,
                                         routes=[{
                                             "cidr_block": "10.0.0.0/16",
                                             "gateway_id": "local",
                                         }],
                                         opts=pulumi.ResourceOptions(depends_on=[igw]),
                                         tags={"Name": "my-vpc-private-rt"})

# Associate Route Table with Private Subnet
private_route_table_association = aws.ec2.RouteTableAssociation("private-subnet-association",
                                                                subnet_id=private_subnet.id,
                                                                route_table_id=private_route_table.id,
                                                                opts=pulumi.ResourceOptions(depends_on=[private_route_table]))

# Create Security Group for Lambda functions
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

# Create IAM Role for Lambda with trust policy
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

# Create Inline Policy allowing GetObject on pulumi-outputs.json in the S3 bucket
bucket_name = "lambda-function-bucket-poridhi"
bucket = aws.s3.Bucket(bucket_name)

# Get the ARN of the bucket
bucket_arn = bucket.arn

lambda_s3_policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowLambdaReadS3",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                f"arn:aws:s3:::{bucket_arn}/pulumi-outputs.json"
            ]
        }
    ]
}

lambda_s3_policy = aws.iam.Policy("lambdaS3Policy", policy=json.dumps(lambda_s3_policy_document))

# Attach the policy to tb he IAM Role
lambda_role_policy_attachment = aws.iam.RolePolicyAttachment("lambdaRolePolicyAttachment",
                                                             role=lambda_role.name,
                                                             policy_arn=lambda_s3_policy.arn)

# Create ECR Repository f
repository = aws.ecr.Repository("my-ecr-repo",
                                 opts=pulumi.ResourceOptions(depends_on=[lambda_role]))

# Export Outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("public_route_table_id", public_route_table.id)
pulumi.export("private_route_table_id", private_route_table.id)
pulumi.export("ec2_security_group_id", ec2_security_group.id)
pulumi.export("lambda_security_group_id", lambda_security_group.id)
pulumi.export("lambda_role_arn", lambda_role.arn)
pulumi.export("bucket_name", bucket.bucket)
pulumi.export("ecr_repo_url", repository.repository_url)
pulumi.export("ecr_registry", repository.registry_id)
pulumi.export("ec2_private_ip", ec2_instance.private_ip)