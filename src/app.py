import json
import os
import uuid
import boto3
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
sns = boto3.client("sns")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
TOPIC_ARN = os.environ["TOPIC_ARN"]
table = dynamodb.Table(TABLE_NAME)

def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
        },
        "body": json.dumps(body, default=decimal_default)
    }

def decimal_default(value):
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError

def lambda_handler(event, context):
    method = event.get("httpMethod", "")
    path = event.get("path", "")

    if method == "OPTIONS":
        return response(200, {"message": "CORS preflight OK"})

    try:
        if path.endswith("/items") and method == "GET":
            result = table.scan()
            items = result.get("Items", [])
            items.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            return response(200, {"items": items})

        body = json.loads(event.get("body") or "{}")

        if path.endswith("/items") and method == "POST":
            required = ["title", "description", "category", "location", "contact"]
            missing = [key for key in required if not str(body.get(key, "")).strip()]
            if missing:
                return response(400, {"error": "Missing fields: " + ", ".join(missing)})

            item = {
                "itemId": str(uuid.uuid4()),
                "title": body["title"].strip(),
                "description": body["description"].strip(),
                "category": body["category"],
                "location": body["location"].strip(),
                "contact": body["contact"].strip(),
                "status": "OPEN",
                "createdAt": datetime.now(timezone.utc).isoformat()
            }
            table.put_item(Item=item)
            return response(201, {"message": "Lost/found item posted successfully", "item": item})

        if path.endswith("/upload-url") and method == "POST":
            filename = body.get("filename", "upload.jpg")
            content_type = body.get("contentType", "image/jpeg")
            key = f"uploads/{uuid.uuid4()}-{os.path.basename(filename)}"
            url = s3.generate_presigned_url(
                "put_object",
                Params={"Bucket": BUCKET_NAME, "Key": key, "ContentType": content_type},
                ExpiresIn=300
            )
            return response(200, {"uploadUrl": url, "key": key, "expiresInSeconds": 300})

        if path.endswith("/notify") and method == "POST":
            message = body.get("message", "A new campus lost-and-found update is available.")
            sns.publish(
                TopicArn=TOPIC_ARN,
                Subject="Campus Lost & Found Update",
                Message=message
            )
            return response(200, {"message": "Notification published to SNS topic"})

        return response(404, {"error": "Route not found"})
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {str(exc)}")
        return response(500, {"error": "Internal server error. Check CloudWatch logs."})
