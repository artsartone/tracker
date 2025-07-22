import os
from yandex_tracker_client import TrackerClient

client = TrackerClient(token=os.environ["TOKEN"], cloud_org_id=os.environ["ORG"])
TARGET_STATUS = "closed"


def handler(event, context):
    try:
        issue = client.issues[event["queryStringParameters"]["id"]]

        subtasks = []
        for link in issue.links:
            if link.direction == "outward" and hasattr(link.object, "key"):
                subtask = client.issues[link.object.key]
                subtasks.append(subtask)

        if not subtasks:
            return {"statusCode": 404, "body": "Subtasks not found"}

        if any(task.status.key != TARGET_STATUS for task in subtasks):
            if not hasattr(issue, "previousStatus") or not issue.previousStatus:
                return {"statusCode": 404, "body": "Previous status not found"}

            previous_status_key = issue.previousStatus.key

            transitions = issue.transitions
            target_transition = None
            for transition in transitions:
                if transition.to.key == previous_status_key:
                    target_transition = transition
                    break

            if not target_transition:
                return {
                    "statusCode": 400,
                    "body": f"No transition available to {previous_status_key}",
                }

            target_transition.execute()

            return {
                "statusCode": 200,
                "body": "Ok",
            }

        return {
            "statusCode": 200,
            "body": "All subtasks are closed — no rollback needed",
        }

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
