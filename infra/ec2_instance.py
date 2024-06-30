import pulumi
import pulumi_aws as aws

class EC2Instance:
    def __init__(self, name: str, subnet_id: pulumi.Output[str], security_group_id: pulumi.Output[str]):
        ami_id = aws.ec2.get_ami(most_recent=True,
                                 owners=["amazon"],
                                 filters=[{"name": "name", "values": ["amzn2-ami-hvm-*-x86_64-gp2"]}]
                                 ).id
        self.instance = aws.ec2.Instance(name,
                                         instance_type="t2.micro",
                                         ami=ami_id,
                                         subnet_id=subnet_id,
                                         vpc_security_group_ids=[security_group_id],
                                         tags={"Name": name})
        pulumi.export("ec2_instance_id", self.instance.id)
