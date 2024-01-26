import os
import json
import logging
import requests


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


MONDAY_API_KEY = os.environ["MONDAY_API_KEY"]


def lambda_handler(event, context):
    # Parse the incoming JSON payload from the webhook
    body = json.loads(event["body"])

    # Log the entire JSON body
    logger.info("Received JSON payload: %s", body)

    # Check if there's a challenge field in the request
    if "challenge" in body:
        challenge = body["challenge"]

        # Respond with the same challenge
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"challenge": challenge}),
        }
    if "event" in body:
        event = body["event"]
        board_id = event["boardId"]
        item_id = event["pulseId"]

        logger.info("Board ID: %s", board_id)
        logger.info("Item ID: %s", item_id)

        # Fetch board information from monday.com
        board_info = query_board_info(item_id)
        logger.info("Board info: %s", board_info)
        item_name = board_info["data"]["items"][0]["name"]
        username = board_info["data"]["me"]["name"]
        update_message = event["textBody"]
        column_values = board_info["data"]["items"][0]["column_values"]
        logger.info("Columns: %s", column_values)
        update_text = event["textBody"]
        logger.info("Update text: %s", update_text)
        update_text = create_update_text(
            item_name, username, column_values, update_message
        )
        for column in column_values:
            if column["type"] == "mirror" and column["display_value"] != "":
                mirror_field_id = column["display_value"]
                logger.info(
                    "Identification for mirror field %s: %s",
                    column["id"],
                    mirror_field_id,
                )
                response = create_update(mirror_field_id, update_text)
                logger.info("Response: %s", response)
                logger.info("Update created")

        logger.info("Item name: %s", item_name)

        return {"statusCode": 200, "body": json.dumps(board_info)}

    # Handle other types of requests or errors here
    logger.error("No challenge or event field found in the received JSON payload")
    return {"statusCode": 400, "body": json.dumps("No challenge found")}


def create_update_text(item_name, username, column_values, update_message):
    id_dict = {
        "Contacts": "connect_boards37",
        "Candidates": "connect_boards79",
        "Clients": "connect_boards6",
        "Positions": "connect_boards61",
        "Partners": "connect_boards0",
        "Leads": "connect_boards7",
    }

    # Create a dictionary to hold the display values
    display_values = {category: None for category in id_dict.keys()}

    # Iterate over column values and extract display values
    for element in column_values:
        for category, id_value in id_dict.items():
            if element["id"] == id_value:
                display_values[category] = element.get("display_value")

    # Construct the update text
    update_text = f"Activity name: {item_name}\nCreator: {username}\n"

    # Append display values if they exist
    for category, value in display_values.items():
        if value:
            update_text += f"{category}: {value}\n"

    # Append the custom update message
    update_text += f"Message: {update_message}\n"

    return update_text


def create_update(item_id: str, text: str) -> dict[str, str]:
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
        "API-Version": "2024-01",
    }

    # Make the API request
    response = requests.post(
        "https://api.monday.com/v2/",
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=500,
    )
    if response.status_code == 200:
        return response.json()

    return {"error": f"Failed to fetch board info, status code {response.status_code}"}


def query_board_info(item_id: str) -> dict[str, str]:
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
        "API-Version": "2024-01",
    }

    # Make the API request
    response = requests.post(
        "https://api.monday.com/v2/",
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=500,
    )
    if response.status_code == 200:
        return response.json()
    return {"error": f"Failed to fetch board info, status code {response.status_code}"}
