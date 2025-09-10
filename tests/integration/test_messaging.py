import json
from unittest.mock import Mock, patch


class TestMessagingIntegration:
    """Test SQS messaging integration"""

    @patch("boto3.client")
    def test_student_creation_sends_sqs_message(self, mock_boto, client):
        """Creating a student should send SQS message"""
        # Mock SQS
        mock_sqs = Mock()
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        mock_sqs.get_queue_url.return_value = {"QueueUrl": "http://test"}
        mock_boto.return_value = mock_sqs

        # Create student
        response = client.post(
            "/api/v1/students",
            json={"first_name": "Message", "last_name": "Test", "grade": 9},
        )

        assert response.status_code == 201

        # Verify SQS was called
        mock_sqs.send_message.assert_called()
        call_args = mock_sqs.send_message.call_args

        # Verify message content
        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["event_type"] == "student_created"
        assert message_body["data"]["name"] == "Message Test"

    @patch("boto3.resource")
    def test_student_creation_logs_audit(self, mock_boto_resource, client):
        """Creating a student should log to audit table"""
        # Mock DynamoDB
        mock_table = Mock()
        mock_table.put_item.return_value = {}

        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb

        # Create student
        response = client.post(
            "/api/v1/students",
            json={"first_name": "Audit", "last_name": "Test", "grade": 7},
        )

        assert response.status_code == 201

        # Verify audit log was created
        mock_table.put_item.assert_called()
        call_args = mock_table.put_item.call_args

        audit_item = call_args[1]["Item"]
        assert audit_item["action"] == "student_created"
        assert "timestamp" in audit_item
        assert "id" in audit_item
