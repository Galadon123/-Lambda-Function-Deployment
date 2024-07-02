import pulumi
import pulumi_aws as aws

class S3Bucket:
    def __init__(self, name):
        self.bucket = aws.s3.Bucket(name,
                                    bucket=name,
                                    acl="public-read",
                                    tags={"Name": name})

        pulumi.export("bucket_name", self.bucket.bucket)