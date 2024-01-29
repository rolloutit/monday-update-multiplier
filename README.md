# AWS Lambda Python Script for Monday.com Integration for Update multiplication across multiple Boards

This repository contains a Python script and Serverless Framework configuration for an AWS Lambda function. The function is designed to interact with Monday.com via webhooks and the Monday.com GraphQL API. It processes incoming webhook events, updates items on Monday.com, and logs relevant information for efficient monitoring and debugging.

## Features

- **Webhook Processing**: Handles incoming JSON payloads from Monday.com webhooks.
- **Challenge Response**: Responds to Monday.com webhook challenges for verification.
- **Error Handling**: Robust error handling for JSON decoding and API requests.
- **Logging**: Detailed logging for debugging and monitoring.
- **Creating Updates**: Generates and posts updates to connected boards on Monday.com.

## Monday.com Setup

To integrate your AWS Lambda function with Monday.com, follow these steps:

### 1. Acquire the Monday API Key

- Log in to your Monday.com account.
- Navigate to the "Developers" section and access the "My access tokens" section to generate and/or copy your API key.

### 2. Create an Activity Board

- Set up an activity board on Monday.com.
- Add "Connect Board" fields to allow items from different boards to be connected to an activity item.

### 3. Create ID Field

- For each board that will be connected, create a unique ID field. This ensures that items from these boards can be identified.

### 4. Set Up Mirror Fields

- On your activity board, create mirror fields corresponding to each connected board.
- These mirror fields will display the connected board item IDs.

### 5. Create a Webhook Integration

- In the activity board, set up a webhook integration.
- Configure the webhook to trigger when a new update is posted.

### 6. Configure Webhook with AWS API Gateway Endpoint

- Copy the endpoint URL from your deployed AWS API Gateway.
- Paste this URL into the webhook setup field in Monday.com.

After completing these steps, your Monday.com setup will be ready to interact with the AWS Lambda function via webhooks.

## Serverless Framework Configuration

The Lambda function is configured and deployed using the Serverless Framework. Here's an overview of the `serverless.yml` configuration:

```yml
org: org-name
app: app-name
service: monday-update-multiplier
frameworkVersion: "3"

provider:
  name: aws
  runtime: python3.11
  region: eu-central-1
  stage: ${opt:stage, 'dev'}

  # Define the resource policy
  apiGateway:
    resourcePolicy:
      - Effect: "Allow"
        Principal: "*"
        Action: "execute-api:Invoke"
        Resource:
          - "execute-api:/*/*/*"
        Condition:
          IpAddress:
            aws:SourceIp:
              - "82.115.214.0/24"
              - "185.66.202.0/23"
              - "185.237.4.0/22"

functions:
  mondayUpdateMultiplier:
    handler: lambda_handler.lambda_handler
    environment: ${file(env.json)}
    timeout: 15
    memorySize: 128
    events:
      - http:
          path: /monday-gateway
          method: any
    layers:
      - Ref: PythonRequirementsLambdaLayer
custom:
  pythonRequirements:
    layer: true

plugins:
  - serverless-python-requirements
```

## API Gateway Resource Policy for IP Whitelisting

To enhance the security of the Lambda function, the `serverless.yml` includes an API Gateway resource policy that restricts access to specific IP ranges used by Monday.com. This ensures that only requests from these IPs can reach the function, providing an additional security layer.

### IP Whitelisting Configuration

The configuration allows traffic from the following Monday.com IP ranges:

- `82.115.214.0/24`
- `185.66.202.0/23`
- `185.237.4.0/22`

This is defined in the `provider.apiGateway.resourcePolicy` section of the `serverless.yml`, where each IP range is specified under the `Condition.IpAddress.aws:SourceIp` field.

## Configuration

Set up the following environment variables in `env.json`:

- `MONDAY_API_KEY`: Your API key for authentication with Monday.com.
- `MONDAY_API_URL`: The URL endpoint for Monday.com's API.
- `MONDAY_API_VERSION`: The version of the Monday.com API you are targeting.

## Deployment

To deploy the function, ensure you have Serverless Framework installed and configured. Then, run the following command:

```bash
serverless deploy --stage <stage-name>
```

Replace <stage-name> with your desired stage, such as dev or prod.

## Main Components

### Lambda Handler

- `lambda_handler(event, context)`: The main function AWS Lambda calls when the script is executed. It parses the incoming webhook event and processes it accordingly.

### Helper Functions

- `make_api_request(url, query, variables, headers)`: Sends POST requests to the Monday.com API and handles responses and errors.
- `create_update_text(item_name, username, column_values, update_message)`: Constructs a formatted text string for updates in connected boards.
- `create_update(item_id, update_text)`: Executes a GraphQL mutation to create an update in a specific item on Monday.com.
- `query_item_info(item_id)`: Fetches item information from Monday.com using GraphQL.

## Usage

1. **Deploy the script using Serverless Framework** to your AWS Lambda environment.
2. **Configure a webhook in Monday.com** to point to the deployed Lambda function's HTTP endpoint.
3. **Trigger the webhook** to process events, which will log information and interact with Monday.com based on the configuration.

## Logging

Logs are crucial for understanding the function's behavior. The script logs:

- Received webhook payload.
- Results of API requests.
- Detailed error messages in case of failures.

## Error Handling

The script has robust error handling for:

- JSON decoding errors.
- API request failures.
- Parsing item information from the response.

## Security Notes

- Ensure that the `MONDAY_API_KEY` is securely stored and not exposed.
- Regularly review and update IAM roles and permissions associated with the Lambda function.

## Contributions

Contributions are welcome. Please open an issue or submit a pull request with your suggested changes or improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

_This README is part of a GitHub Gist detailing an AWS Lambda Python script for integrating with Monday.com._
