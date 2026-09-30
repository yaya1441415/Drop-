import json, os, time
import boto3
from boto3.dynamodb.conditions import Key
from decimal_encoder import DecimalEncoder

POST_LIFETIME_SECONDS = int(os.environ['POST_LIFETIME_SECONDS'])
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT') or None)
table = dynamodb.Table(os.environ['TABLE_NAME'])


def handler(event, context):
    cutoff = int(time.time()) - POST_LIFETIME_SECONDS
    try:
        response = table.query(
            IndexName="TypeCreatedAtIndex",
            KeyConditionExpression=Key("type").eq("post") & Key("created_at").gt(cutoff),
            ScanIndexForward=False,# reverse the default order to desc
            Limit=20,
        )
    except Exception as e:
        print("DYNAMODB ERROR:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": "Could not load posts"})}

    posts = response["Items"]

    return {
        "statusCode": 200,
        "body": json.dumps({"posts": posts}, cls=DecimalEncoder),
    }

    