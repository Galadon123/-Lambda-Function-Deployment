import pulumi
import pulumi_aws as aws

class PublicSubnet:
    def __init__(self, name: str, vpc_id: pulumi.Output[str], cidr_block: str, availability_zone: str):
        self.subnet = aws.ec2.Subnet(name,
                                     vpc_id=vpc_id,
                                     cidr_block=cidr_block,
                                     availability_zone=availability_zone,
                                     map_public_ip_on_launch=True,
                                     tags={"Name": name})
        self.route_table_association = aws.ec2.RouteTableAssociation(f"{name}-rta",
                                                                     subnet_id=self.subnet.id,
                                                                     route_table_id=vpc_id.apply(lambda vpc_id: aws.ec2.get_route_table(vpc_id=vpc_id, tags={"Name": "my-vpc-public-rt"}).id))
        pulumi.export("public_subnet_id", self.subnet.id)
