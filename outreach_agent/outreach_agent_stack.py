from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    Duration,
)
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from constructs import Construct
from pathlib import Path
import os

class OutreachAgentStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create DynamoDB Table
        table = dynamodb.Table(
            self, "OutreachTable",
            table_name="devops-outreach-db",
            partition_key=dynamodb.Attribute(name="company_website", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # Shared role with Secrets Manager and DynamoDB access
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
            ]
        )

        # Create Lambdas
        lambdas = {}
        for name in ["perplexity_targets", "company_ranker", "apollo_scraper", "slack_notifier"]:
            lambdas[name] = PythonFunction(
                self,
                f"{name}_function",
                function_name=f"{name}_function",
                entry=str(Path("src") / name),
                index="lambda_function.py",
                handler="lambda_handler",
                runtime=_lambda.Runtime.PYTHON_3_12,
                timeout=Duration.seconds(210),
                role=lambda_role,
            )

        # Step Function Tasks
        # Perplexity Lambda
        perplexity_task = tasks.LambdaInvoke(
            self, "Generate Target Companies",
            lambda_function=lambdas["perplexity_targets"],
            output_path="$.Payload"
        )

        # Ranker Lambda
        ranker_task = tasks.LambdaInvoke(
            self, "Rank Companies",
            lambda_function=lambdas["company_ranker"],
            payload=sfn.TaskInput.from_object({
                "websites": sfn.JsonPath.string_at("$.websites")
            }),
            output_path="$.Payload"
        )

        # Apollo Lambda
        apollo_task = tasks.LambdaInvoke(
            self, "Find Contacts with Apollo",
            lambda_function=lambdas["apollo_scraper"],
            payload=sfn.TaskInput.from_object({
                "websites": sfn.JsonPath.string_at("$.websites")
            }),
            output_path="$.Payload"
        )

        # Slack Notifier Lambda
        notifier_task = tasks.LambdaInvoke(
            self, "Notify via Slack",
            lambda_function=lambdas["slack_notifier"],
            payload=sfn.TaskInput.from_object({
                "websites": sfn.JsonPath.string_at("$[0].websites")
            }),
            output_path="$.Payload"
        )

        # Parallel block
        parallel_tasks = sfn.Parallel(self, "Rank and Enrich Contacts")
        parallel_tasks.branch(ranker_task)
        parallel_tasks.branch(apollo_task)

        # Define the full sequence
        definition = (
            perplexity_task
            .next(parallel_tasks)
            .next(notifier_task)
        )

        # Create the State Machine
        sfn.StateMachine(
            self, "OutreachWorkflow",
            definition=definition,
            timeout=Duration.minutes(5),
            state_machine_name="DevOpsOutreachPipeline"
        )
