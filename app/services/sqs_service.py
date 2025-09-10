import json
import time

import boto3

from app.core.logging import logger


class SQSService:
    def __init__(self):
        self.sqs = None
        self.queue_url = None

    def initialise(self):
        """Initialise SQS client - call this on app startup"""
        try:
            self.sqs = boto3.client(
                "sqs",
                endpoint_url="http://localstack:4566",
                region_name="us-east-1",
                aws_access_key_id="test",
                aws_secret_access_key="test",
            )
            # Get queue URL from Terraform output
            self.queue_url = "http://localstack:4566/000000000000/student-events"
            print("SQS Service initialised")
        except Exception as e:
            print(f"Failed to initialise SQS: {e}")

    def send_event(self, event_type: str, data: dict) -> bool:
        """Send event to SQS - returns True if successful"""
        if not self.sqs:
            print("SQS not initialised")
            return False

        try:
            # correlation_id = correlation_id_var.get()

            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(
                    {
                        # 'correlation_id': correlation_id,
                        "event_type": event_type,
                        "data": data,
                        "timestamp": str(time.time()),
                    }
                ),
            )

            logger.info(
                "Sent SQS message",
                extra={
                    "event_type": event_type,
                    # "correlation_id": correlation_id
                },
            )

            print(f"Sent {event_type} event to SQS")
            return True
        except Exception as e:
            print(f"Failed to send SQS message: {e}")
            return False


# Global instance
sqs_service = SQSService()
