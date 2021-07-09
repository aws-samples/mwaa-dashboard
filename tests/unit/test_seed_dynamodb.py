import os
from unittest import mock
import logging
import boto3
import pytest

from moto import mock_dynamodb2

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

TEST_TABLE = "TestTable"


@pytest.fixture(autouse=True)
def mock_settings_env_vars():
    with mock.patch.dict(
        os.environ,
        {
            "DASHBOARD_TEMPLATE_TABLE": TEST_TABLE,
            "LAMBDA_TASK_ROOT": os.path.abspath("functions/seed_dynamodb"),
        },
    ):
        yield


@pytest.fixture()
def mock_event():
    return {
        "ResponseURL": "https://cloudformation.us-east-1.amazonaws.com/",
        "StackId": "1",
        "RequestId": "731e49b0-063d-1edb-8b44-87fdd57cb310",
        "RequestType": "Create",
        "LogicalResourceId": "MyResourceId",
    }


class MockContext(object):
    def __init__(self):
        self.log_stream_name = "test-stream"


@mock_dynamodb2
def test_lambda_handler(mock_event, mocker):
    context = MockContext()
    from functions.seed_dynamodb import app

    assert os.environ["DASHBOARD_TEMPLATE_TABLE"] == TEST_TABLE
    assert "seed_dynamodb" in os.environ["LAMBDA_TASK_ROOT"]

    conn = boto3.client("dynamodb")

    conn.create_table(
        TableName=TEST_TABLE,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )

    ret = app.lambda_handler(mock_event, context)

    logger.info(ret)
