import os
from yandex_tracker_client import TrackerClient

client = TrackerClient(token=os.environ["TOKEN"], cloud_org_id=os.environ["ORG"])
TARGET_STATUS = "closed"


def handler(event, context):
    try:
        issue = client.issues[event["queryStringParameters"]["id"]]

        parent_issue = None
        for link in issue.links:
            if link.direction == "inward" and hasattr(link.object, "key"):
                parent_issue = client.issues[link.object.key]
                break

        subtasks = []
        for link in parent_issue.links:
            if link.direction == "outward" and hasattr(link.object, "key"):
                key = link.object.key
                if key != issue.key:
                    subtask = client.issues[key]
                    subtasks.append(subtask)

        all_closed = all(task.status.key == TARGET_STATUS for task in subtasks)
        if not all_closed:
            return {"statusCode": 400, "body": "Not all subtasks are closed"}

        transitions = parent_issue.transitions
        target_transition = None
        for transition in transitions:
            if transition.to.key == TARGET_STATUS:
                target_transition = transition
                break

        if not target_transition:
            return {
                "statusCode": 400,
                "body": f"Cannot transition parent issue to {TARGET_STATUS}",
            }

        target_transition.execute()
        return {"statusCode": 200, "body": "ok"}

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
