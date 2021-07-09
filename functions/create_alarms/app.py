""" Create CW Alarms for all MWAA environments """

import datetime
import json

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

    # Create or update CW alarms for all MWAA environments
    for env in mwaa_environments:

        print(f"Creating alarm Airflow-{env}-UnhealthyWorker")
        cloudwatch.put_metric_alarm(
            AlarmName=f"Airflow-{env}-UnhealthyWorker",
            AlarmDescription="Worker tasks queued no tasks running 15 minutes",
            ComparisonOperator="GreaterThanThreshold",
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=0.0,
            TreatMissingData="missing",
            ActionsEnabled=True,
            Metrics=[
                {
                    "Id": "e1",
                    "Label": "QueuedGreaterThanRunningAndRunningIsZero",
                    "Expression": "IF(m1 > m2 AND m2 == 0, 1, 0)",
                    "ReturnData": True,
                },
                {
                    "Id": "m1",
                    "ReturnData": False,
                    "MetricStat": {
                        "Period": 900,
                        "Stat": "Maximum",
                        "Metric": {
                            "Namespace": "AmazonMWAA",
                            "MetricName": "QueuedTasks",
                            "Dimensions": [
                                {"Name": "Function", "Value": "Executor"},
                                {"Name": "Environment", "Value": env},
                            ],
                        },
                    },
                },
                {
                    "Id": "m2",
                    "ReturnData": False,
                    "MetricStat": {
                        "Period": 900,
                        "Stat": "Maximum",
                        "Metric": {
                            "Namespace": "AmazonMWAA",
                            "MetricName": "RunningTasks",
                            "Dimensions": [
                                {"Name": "Function", "Value": "Executor"},
                                {"Name": "Environment", "Value": env},
                            ],
                        },
                    },
                },
            ],
            Tags=[{"Key": "MWAAEnvironment", "Value": env}],
        )

        print(f"Creating alarm Airflow-{env}-HeartbeatFail")
        cloudwatch.put_metric_alarm(
            AlarmName=f"Airflow-{env}-HeartbeatFail",
            AlarmDescription="Scheduler no heartbeat 5 minutes",
            ComparisonOperator="LessThanOrEqualToThreshold",
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=0.0,
            TreatMissingData="breaching",
            ActionsEnabled=True,
            Metrics=[
                {
                    "Id": "m1",
                    "ReturnData": True,
                    "MetricStat": {
                        "Period": 300,
                        "Stat": "Average",
                        "Metric": {
                            "Namespace": "AmazonMWAA",
                            "MetricName": "SchedulerHeartbeat",
                            "Dimensions": [
                                {"Name": "Function", "Value": "Scheduler"},
                                {"Name": "Environment", "Value": env},
                            ],
                        },
                    },
                }
            ],
            Tags=[{"Key": "MWAAEnvironment", "Value": env}],
        )
