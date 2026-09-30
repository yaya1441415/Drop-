import json, os, time
import boto3
import redis
from decimal_encoder import DecimalEncoder


POST_LIFETIME_SECONDS = int(os.environ['POST_LIFETIME_SECONDS'])
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT') or None)
table = dynamodb.Table(os.environ['TABLE_NAME'])
REDIS_HOST = os.environ.get('REDIS_HOST')
r = redis.Redis(
        host=REDIS_HOST,
        port=6379, 
        decode_responses=True,
        socket_connect_timeout=0.5,
        socket_timeout=0.5,
    ) if REDIS_HOST else None




def handler(event, context):
    _id = event['pathParameters']['id'] 

    key = 'post:'+_id
    cached_post = None
    if r is not None:
        try:
            cached_post = r.get(key)
        except redis.RedisError as e:
            print("REDIS ERROR (continuing without cache):", str(e))

    if cached_post is not None:
        #CACHE HIT: return the cached data
        print("Cache Hit")
        return {"statusCode":200, "body": cached_post}
    else:
        print("Cache miss")
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

        expiry_timestamp = int(response['Item']['expiry'])
        post = response["Item"]
        body = json.dumps({"post": post}, cls=DecimalEncoder)

        if r is not None:
            try:
                r.set(key, body, exat=expiry_timestamp) 
            except redis.RedisError as e:
                print("REDIS ERROR (continuing without cache):", str(e))
            
        return {
            "statusCode": 200,
            "body": json.dumps({"post": post}, cls=DecimalEncoder),
        }

