# Campus Lost & Found — AWS Serverless Project

## What it does
A small web application where students can report a lost/found item and view reports. It uses AWS API Gateway, AWS Lambda, Amazon DynamoDB, Amazon S3, Amazon SNS, IAM execution permissions, and Amazon CloudWatch.

## Architecture
Browser → API Gateway → Lambda → DynamoDB
                         ↘ S3 (pre-signed upload URL for optional image uploads)
                         ↘ SNS (publish notification)
Lambda logs/errors → CloudWatch Logs

## AWS resources and why they are used
| AWS service/resource | Use in this project | Why it is suitable |
|---|---|---|
| Amazon API Gateway | Exposes HTTPS REST endpoints `/items`, `/upload-url`, `/notify` | Secure managed entry point; no server to maintain |
| AWS Lambda | Runs Python backend logic for each API request | Serverless and scales automatically; pay per invocation |
| Amazon DynamoDB | Stores item reports with itemId as partition key | Managed NoSQL database; flexible item records and on-demand capacity |
| Amazon S3 | Stores uploaded item images; backend creates a short-lived pre-signed upload URL | Durable object storage; private bucket; browser can upload without making bucket public |
| Amazon SNS | Publishes a notification when the demo notification endpoint is called | Publish/subscribe messaging; can fan out to email subscribers |
| Amazon CloudWatch Logs | Captures Lambda execution logs and errors | Monitoring and troubleshooting |
| AWS IAM | Lambda execution role grants access to only the required table, bucket and SNS topic | Authentication between AWS services with least-privilege policies |
| AWS SAM / CloudFormation | Defines and deploys the resources in `template.yaml` | Infrastructure as Code; repeatable deployment |

**Important accuracy note:** the image-upload URL endpoint is implemented and returns a pre-signed S3 URL. The simple web form does not include a file picker, so image uploading is an available API feature but is not part of the main UI demonstration.

## Prerequisites
- An AWS account or an AWS Academy Learner Lab that permits CloudFormation, Lambda, API Gateway, DynamoDB, S3 and SNS.
- AWS CLI configured with credentials (`aws configure`) OR the Academy lab credentials active in your terminal.
- AWS SAM CLI installed.
- Python 3.12.

## Deploy
Open a terminal in this project folder:

```bash
sam build
sam deploy --guided
```

For the guided prompts:
- Stack Name: `campus-lost-found`
- AWS Region: choose the region allowed by your lab (for example `us-east-1`)
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save arguments to configuration file: `Y`

When deployment completes, copy the `ApiUrl` output.

## Run the web app
1. Open `frontend/config.js`.
2. Replace `PASTE_API_URL_HERE` with the `ApiUrl` output. Do not add a trailing slash.
3. In a terminal, run:

```bash
cd frontend
python -m http.server 8000
```

4. Open `http://localhost:8000` in your browser.
5. Submit a sample item, then refresh the list.
6. Click **Send test notification**. This publishes a message to the SNS topic.

## Demonstrate S3 and SNS in the AWS Console
- **DynamoDB:** open the table named in the stack outputs/resources and choose Explore table items. Submit a report and show the new record.
- **Lambda:** open the function created by the stack and show its code/configuration and Monitor tab.
- **CloudWatch:** Lambda → Monitor → View CloudWatch logs; show the request log entries/errors.
- **S3:** open the created bucket. It is private. To demonstrate the image endpoint, send POST `/upload-url` with JSON `{"filename":"demo.jpg","contentType":"image/jpeg"}` using Postman; it returns a time-limited PUT URL. Upload a real image to that URL with a PUT request and `Content-Type: image/jpeg`. Do not make the bucket public.
- **SNS:** open the created topic. To receive email, create an email subscription in the SNS console and confirm the email. Then click the app's notification button. Without a confirmed subscription, the publish still succeeds but no email is delivered.

## API examples
Base URL is the `ApiUrl` output.

Create report:
```http
POST /items
Content-Type: application/json

{
  "title": "Black water bottle",
  "description": "Steel bottle left near the library",
  "category": "Accessories",
  "location": "Central Library",
  "contact": "student@example.com"
}
```

Get reports:
```http
GET /items
```

Get pre-signed S3 upload URL:
```http
POST /upload-url
Content-Type: application/json

{"filename":"demo.jpg","contentType":"image/jpeg"}
```

Publish SNS notification:
```http
POST /notify
Content-Type: application/json

{"message":"A new item was reported."}
```

## What to say in the demonstration
"Campus Lost & Found is a serverless web application. A student submits a report in the browser. The request reaches API Gateway, which invokes Lambda. Lambda validates the data and stores it in DynamoDB. The list page calls the GET endpoint and Lambda reads the records from DynamoDB. For images, the backend can generate a temporary pre-signed S3 upload URL, keeping the bucket private. The notification endpoint publishes to SNS, which can deliver the message to confirmed email subscribers. Lambda execution logs are available in CloudWatch. IAM roles control which AWS resources the Lambda function can access. I used SAM/CloudFormation so the infrastructure can be deployed consistently from one template."

## 60-second viva preparation
- **Why serverless?** No server provisioning; scales with requests; pay-per-use.
- **Why DynamoDB instead of SQL?** The data is simple item records with a unique key and does not require relational joins.
- **Why S3?** Object storage is designed for files/images; it is durable and cost-effective.
- **Why API Gateway?** It exposes managed HTTPS endpoints and routes requests to Lambda.
- **Why SNS?** It decouples notification publishing from email delivery and supports multiple subscribers.
- **What is IAM?** Identity and Access Management; the Lambda execution role grants the function permission to call AWS services.
- **What is CloudWatch?** Monitoring and logging service used to inspect Lambda execution logs.
- **What is Infrastructure as Code?** Describing resources in a template so they can be deployed and recreated consistently.

## Cleanup (avoid ongoing charges)
After the presentation, if you no longer need the project, delete the CloudFormation stack `campus-lost-found` from the CloudFormation console. First empty the S3 bucket if it contains objects, then delete the stack. Check the AWS billing console. AWS charges and Academy restrictions vary; do not assume every service is free.
