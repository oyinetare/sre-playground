import uuid
from datetime import datetime
from typing import Any

import boto3


class AuditService:
    def __init__(self):
        self.dynamodb = None
        self.table = None

    def initialise(self):
        """Initialise DynamoDB client"""
        try:
            self.dynamodb = boto3.resource(
                "dynamodb",
                endpoint_url="http://localstack:4566",
                region_name="us-east-1",
                aws_access_key_id="test",
                aws_secret_access_key="test",
            )
            self.table = self.dynamodb.Table("sre-playground-audit")
            print("Audit Service initialised")
        except Exception as e:
            print(f"Failed to initialise Audit Service: {e}")

    def log_action(self, action: str, details: dict[str, Any]):
        """Log an action to audit trail"""
        if not self.table:
            return

        try:
            self.table.put_item(
                Item={
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": action,
                    "details": details,
                }
            )
        except Exception as e:
            print(f"Failed to log audit: {e}")


audit_service = AuditService()
