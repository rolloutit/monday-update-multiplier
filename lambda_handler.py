import os
import json
import logging
import requests


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


MONDAY_API_KEY = os.environ["MONDAY_API_KEY"]
MONDAY_API_URL = os.environ["MONDAY_API_URL"]
MONDAY_API_VERSION = os.environ["MONDAY_API_VERSION"]


def lambda_handler(event, context):
    # Parse the incoming JSON payload from the webhook
    try:
        body = json.loads(event["body"])
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return {"statusCode": 400, "body": "Invalid JSON"}

    # Log the entire JSON body
    logger.info("Received JSON payload: %s", body)

    # Handle the challenge
    if "challenge" in body:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"challenge": body["challenge"]}),
        }

    # Handle the event
    if "event" in body:
        webhook_event = body["event"]
        item_id = webhook_event["pulseId"]

        # Fetch board information from monday.com
        board_info = query_board_info(item_id)
        logger.info(f"Board info: {board_info}")
        if "error" in board_info:
            logger.error(f"Error fetching board info: {board_info['error']}")
            return {"statusCode": 500, "body": board_info["error"]}
        try:
            item_name = board_info["data"]["items"][0]["name"]
            username = board_info["data"]["me"]["name"]
            column_values = board_info["data"]["items"][0]["column_values"]
        except KeyError as e:
            logger.error(f"Error parsing board info: {e}")
            return {"statusCode": 500, "body": f"Error parsing board info: {e}"}

        update_text = create_update_text(
            item_name, username, column_values, webhook_event["textBody"]
        )
        connected_board_found = False
        for column in column_values:
            if column["type"] == "mirror" and column["display_value"]:
                connected_item_id = column["display_value"]
                response = create_update(connected_item_id, update_text)
                if "error" in response:
                    logger.error(f"Error creating update: {response['error']}")
                else:
                    connected_board_found = True
                    logger.info("Update created in connected board")
        if not connected_board_found:
            logger.info("No connected board found")

        return {"statusCode": 200, "body": json.dumps(board_info)}

    # Log an error if neither challenge nor event is found
    logger.error("No challenge or event field found in the received JSON payload")
    return {"statusCode": 400, "body": "No challenge or event field found"}


# Helper function to handle API requests
def make_api_request(url, query, variables, headers):
    try:
        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                f"API request failed with status code {response.status_code}: {response.text}"
            )
            return {
                "error": f"API request failed with status code {response.status_code}"
            }
    except requests.RequestException as e:
        logger.error(f"API request resulted in an exception: {e}")
        return {"error": str(e)}


def create_update_text(item_name, username, column_values, update_message):
    connected_boards_dict = {}
    for single_column in column_values:
        if single_column["column"]["type"] == "board_relation":
            connected_boards_dict[single_column["column"]["title"]] = single_column[
                "display_value"
            ]

    # Construct the update text
    update_text = f"Activity name: {item_name}\nCreator: {username}\n"

    # Append display values if they exist
    for category, value in connected_boards_dict.items():
        if value:
            update_text += f"{category}: {value}\n"

    # Append the custom update message
    update_text += f"Message: {update_message}\n"

    return update_text


def create_update(item_id, text):
    query = """
    mutation ($itemId: ID!, $text: String!) {
        create_update (item_id: $itemId, body: $text) {
            id
        }
    }
    """
    # variables = {"boardId": board_id, "itemId": item_id}
    variables = {"itemId": item_id, "text": text}

    # Set up the request headers
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json",
        "API-Version": MONDAY_API_VERSION,
    }

    # Make the API request
    return make_api_request(MONDAY_API_URL, query, variables, headers)


def query_board_info(item_id):
    """
    Fetches board information from monday.com using the GraphQL API v2 and returns it as a JSON object.
    """
    # Define the GraphQL query
    query = """
    query($ID: [ID!]) {
        me {
            name
        }
        items(ids: $ID) {
            name
            column_values {
                id
                type
                value
                text
                column {
                    id
                    title
                    type
                }
                ... on MirrorValue {
                    display_value
                }
                ... on BoardRelationValue {
                    display_value
                }
            }

        }
    }
    """

    variables = {"ID": item_id}

    # Set up the request headers
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json",
        "API-Version": MONDAY_API_VERSION,
    }

    # Make the API request
    return make_api_request(MONDAY_API_URL, query, variables, headers)
