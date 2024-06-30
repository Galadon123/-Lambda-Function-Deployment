import pulumi
import pulumi_aws as aws

class VPC:
    def __init__(self, name: str, cidr_block: str):
        self.vpc = aws.ec2.Vpc(name,
                               cidr_block=cidr_block,
                               tags={"Name": name})
        self.igw = aws.ec2.InternetGateway(f"{name}-igw",
                                           vpc_id=self.vpc.id,
                                           tags={"Name": f"{name}-igw"})
        self.route_table = aws.ec2.RouteTable(f"{name}-public-rt",
                                              vpc_id=self.vpc.id,
                                              routes=[{
                                                  "cidr_block": "0.0.0.0/0",
                                                  "gateway_id": self.igw.id,
                                              }],
                                              tags={"Name": f"{name}-public-rt"})
        pulumi.export("vpc_id", self.vpc.id)
        pulumi.export("igw_id", self.igw.id)
        pulumi.export("route_table_id", self.route_table.id)
