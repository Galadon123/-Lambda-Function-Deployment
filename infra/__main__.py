import pulumi

from VPC import VPC
from SecurityGroups import SecurityGroups
from EC2 import EC2Instance
from ECR import ECRRepository
from IAM import IAMRole
from S3Bucket import S3Bucket

# Initialize resources
vpc = VPC("my-vpc")
sg = SecurityGroups("my-vpc", vpc.vpc.id)
ec2 = EC2Instance("grafana-tempo-otel", vpc.public_subnet.id, [sg.grafana_security_group.id])
ecr = ECRRepository("my-lambda-function")
iam = IAMRole("lambda")
s3_bucket = S3Bucket("lambda-function-bucket-poridhi")

# Export outputs
pulumi.export("vpc_id", vpc.vpc.id)
pulumi.export("igw_id", vpc.igw.id)
pulumi.export("public_subnet_id", vpc.public_subnet.id)
pulumi.export("private_subnet_id", vpc.private_subnet.id)
pulumi.export("public_route_table_id", vpc.public_route_table.id)
pulumi.export("lambda_security_group_id", sg.lambda_security_group.id)