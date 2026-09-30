import json, os, time
import boto3
from decimal_encoder import DecimalEncoder


POST_LIFETIME_SECONDS = int(os.environ['POST_LIFETIME_SECONDS'])
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT') or None)
table = dynamodb.Table(os.environ['TABLE_NAME'])


def handler(event, context):
    _id = event['pathParameters']['id'] 

    try:
        response = table.get_item(Key={'id':_id})
    except Exception as e:
        print("DYNAMODB ERROR:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": "Could not load the post"})}

    if 'Item' not in response:
        return {"statusCode": 404, "body": json.dumps({"error": "Could not load the post"})}

    created_at = response['Item']['created_at']
    if created_at + POST_LIFETIME_SECONDS <= int(time.time()):
        return {"statusCode": 410, "body": json.dumps({"error": "Could not load the post"})}

    post = response["Item"]
    
    return {
        "statusCode": 200,
        "body": json.dumps({"post": post}, cls=DecimalEncoder),
    }

