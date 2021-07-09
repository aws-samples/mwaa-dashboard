""" Back up each Airflow-* CW dashboard to DynamoDB """

import datetime
import json
import os

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer

logger = Logger()
tracer = Tracer()
metrics = Metrics()

cloudwatch = boto3.client("cloudwatch")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["DASHBOARD_TEMPLATE_TABLE"])


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):

    response = cloudwatch.list_dashboards(DashboardNamePrefix="Airflow-")
    logger.info(json.dumps(response, indent=2, default=default))

    for de in response["DashboardEntries"]:

        response = cloudwatch.get_dashboard(DashboardName=de["DashboardName"])

        logger.info(
            f"Backing up {response['DashboardName']} to table {os.environ['DASHBOARD_TEMPLATE_TABLE']}"
        )

        response = table.put_item(
            Item={
                "id": response["DashboardName"],
                "data": response["DashboardBody"],
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
        )
