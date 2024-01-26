import os
import json
import logging
import requests


# Set up logging for debugging and monitoring purposes
logger = logging.getLogger()
logger.setLevel(logging.INFO)


MONDAY_API_KEY = os.environ["MONDAY_API_KEY"]
MONDAY_API_URL = os.environ["MONDAY_API_URL"]
MONDAY_API_VERSION = os.environ["MONDAY_API_VERSION"]


def lambda_handler(event, context):
    """
    The main handler for the AWS Lambda function.
    Processes incoming webhook events, interacts with Monday.com API, and logs relevant information.
    """
    # Attempt to parse the JSON payload from the webhook
    try:
        body = json.loads(event["body"])
    except json.JSONDecodeError as e:
        # Log and return error if JSON is invalid
        logger.error(f"Error decoding JSON: {e}")
        return {"statusCode": 400, "body": "Invalid JSON"}

    # Log the received JSON payload for debugging
    logger.info("Received JSON payload: %s", body)

    # Respond to Monday.com webhook challenge for verification
    if "challenge" in body:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"challenge": body["challenge"]}),
        }

    # Process the event data if present
    if "event" in body:
        webhook_event = body["event"]
        item_id = webhook_event["pulseId"]

        # Fetch item information from monday.com using the item's ID
        item_info = query_item_info(item_id)
        logger.info(f"Item info: {item_info}")
        if "error" in item_info:
            logger.error(f"Error fetching item info: {item_info['error']}")
            return {"statusCode": 500, "body": item_info["error"]}
        # Extract relevant information from the item data
        try:
            item_name = item_info["data"]["items"][0]["name"]
            username = item_info["data"]["me"]["name"]
            column_values = item_info["data"]["items"][0]["column_values"]
        except KeyError as e:
            # Log and return error if parsing item info fails
            logger.error(f"Error parsing item info: {e}")
            return {"statusCode": 500, "body": f"Error parsing item info: {e}"}
        # Generate update text for the connected board's update
        update_text = create_update_text(
            item_name, username, column_values, webhook_event["textBody"]
        )
        # Create an update in the connected board if it exists
        connected_board_found = False
        for column in column_values:
            if column["type"] == "mirror" and column["display_value"]:
                # There can be multiple connected items from the same board, so we need to loop through each one
                connected_item_id_list = column["display_value"].split(",")
                logger.info(f"Connected board IDs: {connected_item_id_list}")
                for connected_item_id in connected_item_id_list:
                    # Create an update in the connected board
                    response = create_update(connected_item_id, update_text)
                    if "error" in response:
                        # Log and return error if creating update fails
                        logger.error(f"Error creating update: {response['error']}")
                    else:
                        connected_board_found = True
                        logger.info("Update created in connected board")
        if not connected_board_found:
            # Log if no connected board is found for updates
            logger.info("No connected board found")
        # Return the item info for debugging
        return {"statusCode": 200, "body": json.dumps(item_info)}

    # Log an error if neither challenge nor event is found
    logger.error("No challenge or event field found in the received JSON payload")
    return {"statusCode": 400, "body": "No challenge or event field found"}


# Helper function to handle API requests to Monday.com
def make_api_request(url, query, variables, headers):
    """
    Sends a POST request to the specified URL with given query and variables.
    Handles response and errors for API interactions.
    """
    try:
        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=30,
        )
        # Check if the response is successful
        if response.status_code == 200:
            return response.json()
        else:
            # Log error details if the response status code indicates a failure
            logger.error(
                f"API request failed with status code {response.status_code}: {response.text}"
            )
            return {
                "error": f"API request failed with status code {response.status_code}"
            }
    except requests.RequestException as e:
        # Log exception details if the request fails
        logger.error(f"API request resulted in an exception: {e}")
        return {"error": str(e)}


# Helper function to create update text for connected board
def create_update_text(item_name, username, column_values, update_message):
    """
    Constructs a formatted text string based on item details and update message.
    This text is used for updates in connected boards on Monday.com.
    """
    connected_boards_dict = {}
    # Loop through each column's values to build a dictionary of connected boards and their values
    # The keys are the connected board's column titles and
    # the values are the connected board's display values (The name of the connected board item)
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

    # Append the custom update message received from the webhook
    update_text += f"Message: {update_message}\n"

    return update_text


# Function to create an update in a specific item on Monday.com
def create_update(item_id, update_text):
    """
    Executes a GraphQL mutation to create an update in a specific item on Monday.com.
    Takes the item ID and the update text as input.
    """
    query = """
    mutation ($itemId: ID!, $text: String!) {
        create_update (item_id: $itemId, body: $text) {
            id
        }
    }
    """
    # variables = {"boardId": board_id, "itemId": item_id}
    variables = {"itemId": item_id, "text": update_text}

    # Set up the request headers
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json",
        "API-Version": MONDAY_API_VERSION,
    }

    # Make the API request
    return make_api_request(MONDAY_API_URL, query, variables, headers)


# Function to fetch item information from Monday.com
def query_item_info(item_id):
    """
    Fetches item information from monday.com using the GraphQL API v2 and returns it as a JSON object.
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
