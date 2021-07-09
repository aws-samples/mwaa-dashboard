""" Restore Airflow-* CW dashboards from DynamoDB """

import datetime
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

    dashboard_name = event[0]

    response = table.get_item(Item={"id": dashboard_name})
