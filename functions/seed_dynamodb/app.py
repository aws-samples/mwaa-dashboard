""" Custom resource to seed data in DynamoDB """

import logging
import os
from datetime import datetime

import boto3
import cfnresponse

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
            logger.info(
                "Looking for dashboard-template.json at %s", dashboard_template_path
            )
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
        if event["RequestType"] == "Delete":
            logger.info("Deleting DynamoDB table %s", table)
            responseData["Message"] = "Resource deletion successful!"
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    except Exception as exception:
        logger.error("Unexpected error: %s", exception)
        cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
