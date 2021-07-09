""" Delete CW Alarms for nonexistent MWAA environments """

import datetime
import json
from typing import List

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer

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

    alarms_to_delete = []
    paginator = cloudwatch.get_paginator("describe_alarms")
    for response in paginator.paginate(AlarmNamePrefix="Airflow-"):
        logger.debug(json.dumps(response["MetricAlarms"], indent=2, default=default))
        for alarm in response["MetricAlarms"]:
            alarm_arn = alarm["AlarmArn"]
            alarm_tags = cloudwatch.list_tags_for_resource(ResourceARN=alarm_arn)
            # if alarm is tagged with a nonexistent MWAA environment, mark it for deletion
            if not has_tag_with_value_in_list(
                alarm_tags["Tags"], "MWAAEnvironment", mwaa_environments
            ):
                alarms_to_delete.append(alarm["AlarmName"])

    if len(alarms_to_delete) == 0:
        logger.info("No alarms to delete.")
        return

    logger.info("Deleting alarms: " + ",".join(alarms_to_delete))
    cloudwatch.delete_alarms(AlarmNames=alarms_to_delete)


def has_tag_with_value_in_list(tag_dict: dict, tag_key: str, tag_values: List[str]):
    """ Determine if an alarm has an environment tag in the list. """
    list = [
        tag for tag in tag_dict if tag["Key"] == tag_key and tag["Value"] in tag_values
    ]
    return len(list) > 0
