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
        board_id = webhook_event["boardId"]
        item_id = webhook_event["pulseId"]

        # Fetch board information from monday.com
        board_info = query_board_info(item_id)
        if "error" in board_info:
            return {"statusCode": 500, "body": board_info["error"]}

        item_name = board_info["data"]["items"][0]["name"]
        username = board_info["data"]["me"]["name"]
        column_values = board_info["data"]["items"][0]["column_values"]

        update_text = create_update_text(
            item_name, username, column_values, webhook_event["textBody"]
        )

        for column in column_values:
            if column["type"] == "mirror" and column["display_value"]:
                mirror_field_id = column["display_value"]
                response = create_update(mirror_field_id, update_text)
                if "error" in response:
                    logger.error(f"Error creating update: {response['error']}")
                else:
                    logger.info("Update created")

        return {"statusCode": 200, "body": json.dumps(board_info)}

    # Log an error if neither challenge nor event is found
    logger.error("No challenge or event field found in the received JSON payload")
    return {"statusCode": 400, "body": "No challenge or event field found"}


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
