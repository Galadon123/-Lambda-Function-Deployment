import pulumi
import pulumi_aws as aws

class IAMRole:
    def __init__(self, name):
        self.role = aws.iam.Role(f"{name}-role",
                                 assume_role_policy="""{
                                     "Version": "2012-10-17",
                                     "Statement": [
                                         {
                                             "Action": "sts:AssumeRole",
                                             "Principal": {
                                                 "Service": "lambda.amazonaws.com"
                                             },
                                             "Effect": "Allow",
                                             "Sid": ""
                                         }
                                     ]
                                 }""")

        self.s3_policy = aws.iam.Policy(f"{name}-s3Policy",
                                        policy="""{
                                            "Version": "2012-10-17",
                                            "Statement": [
                                                {
                                                    "Effect": "Allow",
                                                    "Action": "s3:GetObject",
                                                    "Resource": "arn:aws:s3:::lambda-function-bucket-poridhi/pulumi-outputs.json"
                                                }
                                            ]
                                        }""")

        self.role_policy_attachment = aws.iam.RolePolicyAttachment(f"{name}-rolePolicyAttachment",
                                                                   role=self.role.name,
                                                                   policy_arn=self.s3_policy.arn)

        self.ec2_policy_attachment = aws.iam.RolePolicyAttachment(f"{name}-rolePolicyAttachmentEC2",
                                                                  role=self.role.name,
                                                                  policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole")

        pulumi.export("lambda_role_arn", self.role.arn)