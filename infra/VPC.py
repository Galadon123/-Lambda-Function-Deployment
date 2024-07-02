import pulumi
import pulumi_aws as aws

class VPC:
    def __init__(self, name):
        self.vpc = aws.ec2.Vpc(f"{name}-vpc",
                               cidr_block="10.0.0.0/16",
                               tags={"Name": f"{name}-vpc"})

        self.igw = aws.ec2.InternetGateway(f"{name}-igw",
                                           vpc_id=self.vpc.id,
                                           tags={"Name": f"{name}-igw"})

        self.public_route_table = aws.ec2.RouteTable(f"{name}-public-rt",
                                                     vpc_id=self.vpc.id,
                                                     routes=[{
                                                         "cidr_block": "0.0.0.0/0",
                                                         "gateway_id": self.igw.id,
                                                     }],
                                                     tags={"Name": f"{name}-public-rt"})

        self.public_subnet = aws.ec2.Subnet(f"{name}-public-subnet",
                                            vpc_id=self.vpc.id,
                                            cidr_block="10.0.1.0/24",
                                            availability_zone="us-east-1a",
                                            map_public_ip_on_launch=True,
                                            tags={"Name": f"{name}-public-subnet"})

        self.private_subnet = aws.ec2.Subnet(f"{name}-private-subnet",
                                             vpc_id=self.vpc.id,
                                             cidr_block="10.0.2.0/24",
                                             availability_zone="us-east-1a",
                                             map_public_ip_on_launch=False,
                                             tags={"Name": f"{name}-private-subnet"})

        self.public_route_table_association = aws.ec2.RouteTableAssociation(f"{name}-public-subnet-association",
                                                                           subnet_id=self.public_subnet.id,
                                                                           route_table_id=self.public_route_table.id)

        pulumi.export("vpc_id", self.vpc.id)
        pulumi.export("igw_id", self.igw.id)
        pulumi.export("public_subnet_id", self.public_subnet.id)
        pulumi.export("private_subnet_id", self.private_subnet.id)
        pulumi.export("public_route_table_id", self.public_route_table.id)
