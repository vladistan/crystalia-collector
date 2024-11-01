import pulumi
import pulumi_aws as aws

from pulumi_terraform import state

import json
import boto3

config = pulumi.Config()

# Import the Terraform state
terraform_state = state.RemoteStateReference(
    "terraform_tubes_remote_state",
    "s3",
    state.S3BackendArgs(bucket="db-tform-state", key="tubes/v1", region="us-east-1"),
)


sts = boto3.client("sts")
account_id = sts.get_caller_identity()["Account"]


project_name = "crystalia-collector-batch"
service_role_arn = f"arn:aws:iam::{account_id}:role/aws-service-role/batch.amazonaws.com/AWSServiceRoleForBatch"
logs_resource_arn = f"arn:aws:logs:us-east-1:{account_id}:log-group:/aws/batch/job:*"

vpc_id = terraform_state.get_output("vpc")
private_subnet = terraform_state.get_output("aws_subnets_private")[0]
sg_adm_access_linux = terraform_state.get_output("sg_adm_access_linux")
sg_all_outbound = terraform_state.get_output("sg_all_outbound")

# Create an AWS resource (S3 Bucket)
bucket = aws.s3.BucketV2("bucket", bucket=f"{project_name}-work-bucket")
enable_docker_tester = config.get_bool("enable_docker_tester")

task_role = aws.iam.Role(
    "ecsInstanceRole",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com",
                    },
                },
            ],
        },
    ),
)

ecs_register_container_instance_policy = aws.iam.RolePolicy(
    "ecs-register-container-instance",
    role=task_role.id,
    policy=bucket.arn.apply(
        lambda arn: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject",
                            "s3:ListBucket",
                        ],
                        "Resource": [arn, f"{arn}/*"],
                    },
                ],
            },
        ),
    ),
)

# Attach the managed policy the task role
managed_policy_attachment = aws.iam.RolePolicyAttachment(
    "ecsInstanceRolePolicyAttachment",
    role=task_role.id,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role",
)

instance_profile = aws.iam.InstanceProfile(
    "ecsInstanceProfile",
    name="ecsInstanceProfile",
    role=task_role.name,
)

batch_env = aws.batch.ComputeEnvironment(
    "Compute-EC2-1",
    compute_environment_name=f"{project_name}-compute-ec2-3",
    compute_resources={
        "max_vcpus": 240,
        "security_group_ids": [sg_adm_access_linux["id"], sg_all_outbound["id"]],
        "type": "EC2",
        "subnets": [private_subnet],
        "instance_role": instance_profile.arn,
        "instance_types": ["optimal"],
        "min_vcpus": 0,
        "desired_vcpus": 0,
        "ec2_key_pair": "pair2021",
        "tags": {
            "Name": "Crystalia Batch Instance",
        },
    },
    service_role=service_role_arn,
    state="ENABLED",
    type="MANAGED",
    opts=pulumi.ResourceOptions(protect=True),
)

job_queue = aws.batch.JobQueue(
    f"{project_name}-process",
    name=f"{project_name}-process-2",
    priority=1,
    compute_environments=[batch_env.arn],
    state="ENABLED",
)

ecr_repo = aws.ecr.Repository(
    f"{project_name}-repo",
    name=f"{project_name}-repo",
    image_scanning_configuration={"scanOnPush": False},
)


task_policy = aws.iam.Policy(
    f"{project_name}-task-ecs",
    name=f"{project_name}-task-ecs",
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket",
                    ],
                    "Resource": [
                        "arn:aws:s3:::*",
                        "arn:aws:s3:::*/*",
                        "arn:aws:s3:::1000genomes-dragen-v4.0",
                        "arn:aws:s3:::1000genomes-dragen-v4.0/*",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    "Resource": logs_resource_arn,
                },
            ],
        },
    ),
)

task_role = aws.iam.Role(
    f"{project_name}-task-ecs",
    name=f"{project_name}-task-ecs",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                },
            ],
        },
    ),
    tags={
        "Name": f"{project_name}-task-ecs",
        "ManagedBy": "pulumi",
    },
)

task_role_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{project_name}-task-ecs-attachment",
    role=task_role.name,
    policy_arn=task_policy.arn,
)


job_definition = aws.batch.JobDefinition(
    f"{project_name}-process",
    name=f"{project_name}-process",
    type="container",
    platform_capabilities=["FARGATE"],
    container_properties=ecr_repo.repository_url.apply(
        lambda repo_url: pulumi.Output.json_dumps(
            {
                "command": ["echo", "Ref::bucket", "Ref::object_key"],
                "image": f"{repo_url}:v0.1",
                "executionRoleArn": task_role.arn,
                "resourceRequirements": [
                    {"type": "VCPU", "value": "1"},
                    {"type": "MEMORY", "value": "2048"},
                ],
                "logConfiguration": {"logDriver": "awslogs"},
            },
        ),
    ),
)

pulumi.export("ecr_repo_url", ecr_repo.repository_url)
pulumi.export("bucket_name", bucket.id)
