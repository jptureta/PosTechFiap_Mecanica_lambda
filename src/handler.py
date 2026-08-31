import json


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Oficina Mecânica Lambda funcionando"}),
        "headers": {"Content-Type": "application/json"},
    }
