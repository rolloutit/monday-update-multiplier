# AWS Lambda Python Script for Monday.com Integration

This repository contains a Python script and Serverless Framework configuration for an AWS Lambda function. The function is designed to interact with Monday.com via webhooks and the Monday.com GraphQL API. It processes incoming webhook events, updates items on Monday.com, and logs relevant information for efficient monitoring and debugging.

## Features

- **Webhook Processing**: Handles incoming JSON payloads from Monday.com webhooks.
- **Challenge Response**: Responds to Monday.com webhook challenges for verification.
- **Error Handling**: Robust error handling for JSON decoding and API requests.
- **Logging**: Detailed logging for debugging and monitoring.
- **Creating Updates**: Generates and posts updates to connected boards on Monday.com.

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
  region: eu-central-1 #your aws region
  stage: ${opt:stage, 'dev'}

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
