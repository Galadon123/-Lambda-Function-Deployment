import pulumi
import pulumi_aws as aws

class EC2Instance:
    def __init__(self, name, subnet_id, security_group_ids):
        self.instance = aws.ec2.Instance(f"{name}-instance",
                                         instance_type="t2.micro",
                                         ami="ami-04b70fa74e45c3917",
                                         subnet_id=subnet_id,
                                         vpc_security_group_ids=security_group_ids,
                                         associate_public_ip_address=True,
                                         tags={"Name": f"{name}-instance"})

        pulumi.export("ec2_instance_id", self.instance.id)
        pulumi.export("ec2_instance_public_ip", self.instance.public_ip)
        pulumi.export("ec2_instance_private_ip", self.instance.private_ip)