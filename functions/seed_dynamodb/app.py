""" Custom resource to seed data in DynamoDB """

import logging
import os

import boto3
import cfnresponse
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["DASHBOARD_TEMPLATE_TABLE"])


def lambda_handler(event, context):
    logger.info(event)
    responseData = {}

    try:
        if event["RequestType"] == "Create":
            dashboard_template_path = (
                os.environ["LAMBDA_TASK_ROOT"] + "/dashboard-template.json"
            )
            print("Looking for dashboard-template.json at " + dashboard_template_path)
            template_data = open(dashboard_template_path).read()

            response = table.put_item(
                Item={
                    "id": "1",
                    "data": template_data,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            logger.info(response)
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    except Exception as e:
        logger.error("Unexpected error: %s" % e)
        cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
