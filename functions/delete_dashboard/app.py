""" Delete CW Dashboards where MWAA environment no longer exists """

import datetime
import json

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from botocore.exceptions import ClientError

logger = Logger()
tracer = Tracer()
metrics = Metrics()

cloudwatch = boto3.client("cloudwatch")
mwaa = boto3.client("mwaa")


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

    # Remove any dashboards for missing environments
    for de in response["DashboardEntries"]:
        # e.g. if Airflow-MyEnv3 not in ['Airflow-MyEnv1', 'Airflow-MyEnv2']
        if de["DashboardName"] not in ["Airflow-" + s for s in mwaa_environments]:
            logger.info(
                f"Deleting dashboard {de['DashboardName']} due to nonexistent MWAA environment."
            )
            try:
                response = cloudwatch.delete_dashboards(
                    DashboardNames=[de["DashboardName"]]
                )
            except ClientError as e:
                print("Unexpected error: %s" % e)
                return de["DashboardName"]
