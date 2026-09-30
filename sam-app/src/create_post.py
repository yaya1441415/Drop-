import json, os, uuid, time
import boto3
from botocore.config import Config

POST_LIFETIME_SECONDS = int(os.environ['POST_LIFETIME_SECONDS'])
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=os.environ.get('DYNAMODB_ENDPOINT') or None,
    config=Config(connect_timeout=2, read_timeout=2, retries={'max_attempts': 1}),
)
table = dynamodb.Table(os.environ['TABLE_NAME'])
def handler(event, context):
    body = event.get('body')

    if not body:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid Body"})}
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    if 'title' not in data:
        return {"statusCode": 400, "body": json.dumps({"error": "title is required"})}
    
    title =  data['title']
    author = data.get('author', 'Anonymous')
    created_at = int(time.time())
    _type = 'post'
    

    post_id = str(uuid.uuid4())

    try:
        table.put_item(Item={
            'id': post_id,
            'title': title,
            'author': author,
            'created_at': created_at,
            'type' : _type,
            'expiry': created_at+POST_LIFETIME_SECONDS
        })

        return {
            "statusCode": 201,
            "body": json.dumps({"id": post_id, "message": "Post created"})
        }

    except Exception as e:
        print("DYNAMODB ERROR:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": "Could not save post"})}



    