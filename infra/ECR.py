import pulumi
import pulumi_aws as aws

class ECRRepository:
    def __init__(self, name):
        self.repository = aws.ecr.Repository(f"{name}-ecr",
                                             image_scanning_configuration={"scanOnPush": True},
                                             tags={"Name": f"{name}-ecr"})

        pulumi.export("ecr_registry", self.repository.registry_id)
        pulumi.export("ecr_repo_url", self.repository.repository_url)