import os
from enum import Enum
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv


class TaskStatus(Enum):
    TO_DO = "TO DO"
    IN_PROGRESS = "IN PROGRESS"
    COMPLETE = "COMPLETE"


class ClickUpClient:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv('CLICKUP_TOKEN')
        self.team_id = os.getenv('CLICKUP_TEAM_ID')
        self.base_url = os.getenv('CLICKUP_ENDPOINT')

    def create_manual_task(self, list_id, attachment, pg_trx_id, description: str = None):
        task = self.create_task(
            list_id=list_id, 
            attachment=attachment, 
            pg_trx_id=pg_trx_id, 
            description=description, 
            task_status=TaskStatus.TO_DO
        )
        self.start_timer(task['id'])

    def create_auto_task(self, list_id, attachment, pg_trx_id, description: str = None):
        tags = ["auto"]
        task = self.create_task(
            list_id=list_id, 
            attachment=attachment, 
            pg_trx_id=pg_trx_id, 
            description=description, 
            task_status=TaskStatus.IN_PROGRESS, 
            tags=tags
        )
        self.start_timer(task['id'])

    def create_task(self, list_id, attachment, pg_trx_id, description: str = None,
                    task_status: TaskStatus = TaskStatus.TO_DO, tags: [str] = None):
        url = f"{self.base_url}/list/{list_id}/task"

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.token
        }
        query = {
            "custom_task_ids": "true",
            "team_id": self.team_id
        }
        payload = {
            "name": f"Ticket_{pg_trx_id}",
            "description": f"ID: {pg_trx_id}\n\nDescription: {description}",
            "status": task_status.value,
            "tags": tags
        }

        response = requests.post(url, json=payload, headers=headers, params=query)
        data = response.json()

        if attachment and attachment != "":
            self.add_attachment(data['id'], attachment, True)

        return data

    def add_attachment(self, task_id, attachment, delete_attachment=False):
        url = f"{self.base_url}/task/{task_id}/attachment"
        headers = {
            "Authorization": self.token
        }
        file = {
            "attachment": (attachment, open(attachment, 'rb'))
        }

        response = requests.post(url, files=file, headers=headers)

        if delete_attachment:
            os.remove(attachment)

        return response.json()

    def start_timer(self, task_id):
        """Start time tracking for the specified task."""
        url = f"{self.base_url}/team/{self.team_id}/time_entries/start"

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.token
        }

        payload = {
            "task_id": task_id,
            "start": int(datetime.now(timezone.utc).timestamp() * 1000)  # Start time in milliseconds
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"Failed to start timer: {response.text}")

        return response.json()
