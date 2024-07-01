import pulumi
import pulumi_aws as aws

class SecurityGroups:
    def __init__(self, name, vpc_id):
        self.grafana_security_group = aws.ec2.SecurityGroup(f"{name}-grafana-sg",
                                                            vpc_id=vpc_id,
                                                            description="Allow All traffic",
                                                            ingress=[{
                                                                "protocol": "-1",
                                                                "from_port": 0,
                                                                "to_port": 0,
                                                                "cidr_blocks": ["0.0.0.0/0"],
                                                            }],
                                                            egress=[{
                                                                "protocol": "-1",
                                                                "from_port": 0,
                                                                "to_port": 0,
                                                                "cidr_blocks": ["0.0.0.0/0"],
                                                            }],
                                                            tags={"Name": f"{name}-grafana-sg"})

        self.lambda_security_group = aws.ec2.SecurityGroup(f"{name}-lambda-sg",
                                                           vpc_id=vpc_id,
                                                           description="Allow all traffic",
                                                           ingress=[{
                                                               "protocol": "-1",
                                                               "from_port": 0,
                                                               "to_port": 0,
                                                               "cidr_blocks": ["0.0.0.0/0"],
                                                           }],
                                                           egress=[{
                                                               "protocol": "-1",
                                                               "from_port": 0,
                                                               "to_port": 0,
                                                               "cidr_blocks": ["0.0.0.0/0"],
                                                           }],
                                                           tags={"Name": f"{name}-lambda-sg"})
