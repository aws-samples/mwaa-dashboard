#!/usr/bin/env python3

import argparse
from datetime import datetime

import boto3

dynamodb = boto3.resource("dynamodb")

parser = argparse.ArgumentParser(
    description="Seed DynamoDB with a CloudWatch dashboard template"
)
parser.add_argument("--table", "-t", required=True, help="DynamoDB table name")
parser.add_argument(
    "--json",
    "-j",
    default="dashboard-template.json",
    help="JSON file (default: dashboard-template.json)",
)
args = parser.parse_args()

print(f"Seeding table {args.table} with dashboard template from {args.json}.")

with open(args.json, "r") as file:
    data = file.read()

    table = dynamodb.Table(args.table)

    response = table.put_item(
        Item={"id": "1", "data": data, "timestamp": datetime.utcnow().isoformat()}
    )

print("Done.")
