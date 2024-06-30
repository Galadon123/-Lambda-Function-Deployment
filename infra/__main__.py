import pulumi
import pulumi_aws as aws

# Create a VPC
vpc = aws.ec2.Vpc("my-vpc",
                  cidr_block="10.0.0.0/16",
                  tags={"Name": "my-vpc"})

# Ensure the VPC is created before creating dependent resources
vpc_created = vpc.id.apply(lambda _: True)

# Create an Internet Gateway
igw = aws.ec2.InternetGateway("internet-gateway",
                              vpc_id=vpc.id,
                              opts=pulumi.ResourceOptions(depends_on=[vpc]),
                              tags={"Name": "internet-gateway"})

# Create a Public Subnet
public_subnet = aws.ec2.Subnet("public-subnet",
                               vpc_id=vpc.id,
                               cidr_block="10.0.1.0/24",
                               availability_zone="us-east-1a",
                               map_public_ip_on_launch=True,
                               opts=pulumi.ResourceOptions(depends_on=[vpc]),
                               tags={"Name": "public-subnet"})

# Create a Route Table for the public subnet
public_route_table = aws.ec2.RouteTable("public-route-table",
                                        vpc_id=vpc.id,
                                        routes=[{
                                            "cidr_block": "0.0.0.0/0",
                                            "gateway_id": igw.id,
                                        }],
                                        opts=pulumi.ResourceOptions(depends_on=[igw]),
                                        tags={"Name": "public-route-table"})

# Associate the Route Table with the public subnet
public_route_table_association = aws.ec2.RouteTableAssociation("public-route-table-association",
                                                               subnet_id=public_subnet.id,
                                                               route_table_id=public_route_table.id,
                                                               opts=pulumi.ResourceOptions(depends_on=[public_route_table]))

# Create a Security Group for the public instance
public_security_group = aws.ec2.SecurityGroup("public-secgrp",
                                              vpc_id=vpc.id,
                                              description="Enable HTTP and SSH access",
                                              ingress=[{
                                                  "protocol": "tcp",
                                                  "from_port": 80,
                                                  "to_port": 80,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }, {
                                                  "protocol": "tcp",
                                                  "from_port": 22,
                                                  "to_port": 22,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                              egress=[{
                                                  "protocol": "-1",
                                                  "from_port": 0,
                                                  "to_port": 0,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                              opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                              tags={"Name": "public-secgrp"})

# Use the specified Ubuntu 24.04 LTS AMI
ami_id = "ami-04b70fa74e45c3917"

# Create an EC2 instance in the public subnet
public_instance = aws.ec2.Instance("public-instance",
                                   instance_type="t2.micro",
                                   vpc_security_group_ids=[public_security_group.id],
                                   ami=ami_id,
                                   subnet_id=public_subnet.id,
                                   key_name="MyKeyPair",
                                   associate_public_ip_address=True,
                                   opts=pulumi.ResourceOptions(depends_on=[public_subnet, public_security_group]),
                                   tags={"Name": "public-instance"})

# Create the Grafana Tempo instance
grafana_instance = aws.ec2.Instance("grafana-tempo",
                                    instance_type="t2.micro",
                                    ami=ami_id,
                                    subnet_id=public_subnet.id,
                                    vpc_security_group_ids=[public_security_group.id],
                                    key_name="MyKeyPair",
                                    associate_public_ip_address=True,
                                    opts=pulumi.ResourceOptions(depends_on=[public_subnet, public_security_group]),
                                    tags={"Name": "grafana-tempo"})

# Export Outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("igw_id", igw.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("route_table_id", public_route_table.id)
pulumi.export("public_instance_id", public_instance.id)
pulumi.export("public_instance_ip", public_instance.public_ip)
pulumi.export("grafana_instance_id", grafana_instance.id)
pulumi.export("grafana_instance_ip", grafana_instance.public_ip)
