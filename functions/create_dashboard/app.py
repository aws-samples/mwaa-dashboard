""" Create CW Dashboards for all MWAA environments """

import datetime
import json
import os

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer

logger = Logger()
tracer = Tracer()
metrics = Metrics()

cloudwatch = boto3.client("cloudwatch")
mwaa = boto3.client("mwaa")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["DASHBOARD_TEMPLATE_TABLE"])
response = table.get_item(Key={"id": "1"})
dashboard_template = response["Item"]["data"]


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):

    logger.info(json.dumps(event, indent=2, default=default))

    mwaa_environments = mwaa.list_environments()["Environments"]

    logger.info(f"Airflow environments: {json.dumps(mwaa_environments, indent=2)}")

    response = cloudwatch.list_dashboards(DashboardNamePrefix="Airflow-")
    logger.info(json.dumps(response, indent=2, default=default))

    # Create or update dashboards for new/existing environments
    for env in mwaa_environments:

        dashboard_name = f"Airflow-{env}"

        dashboard_body = dashboard_template.replace(
            "${AWS::Region}", os.getenv("AWS_REGION", "us-east-1")
        ).replace("${EnvironmentName}", env)

        logger.info(f"Creating/updating dashboard: {dashboard_name}")
        logger.debug(dashboard_body)

        response = cloudwatch.put_dashboard(
            DashboardName=dashboard_name, DashboardBody=dashboard_body
        )

        logger.info(json.dumps(response, indent=2))
