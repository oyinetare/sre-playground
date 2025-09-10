from unittest.mock import Mock, patch

from app.services.cache_service import CacheService
from app.services.sqs_service import SQSService


class TestCacheService:
    """Test caching functionality"""

    @patch("redis.Redis")
    def test_cache_get_returns_none_when_key_missing(self, mock_redis):
        """Cache should return None for missing keys"""
        mock_redis_instance = Mock()
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance

        cache = CacheService()
        cache.initialise()

        result = cache.get("missing_key")
        assert result is None
        mock_redis_instance.get.assert_called_once_with("missing_key")

    @patch("redis.Redis")
    def test_cache_set_with_ttl(self, mock_redis):
        """Cache should set values with TTL"""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = CacheService()
        cache.initialise()

        cache.set("test_key", {"data": "value"}, ttl=60)

        mock_redis_instance.setex.assert_called_once()
        call_args = mock_redis_instance.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 60  # TTL
        assert '"data": "value"' in call_args[0][2]


class TestSQSService:
    """Test message queue functionality"""

    @patch("boto3.client")
    def test_sqs_send_event_success(self, mock_boto_client):
        """SQS should successfully send events"""
        mock_sqs = Mock()
        mock_sqs.send_message.return_value = {"MessageId": "12345"}
        mock_boto_client.return_value = mock_sqs

        sqs_service = SQSService()
        sqs_service.initialise()

        result = sqs_service.send_event("test_event", {"key": "value"})

        assert result
        mock_sqs.send_message.assert_called_once()

    @patch("boto3.client")
    def test_sqs_send_event_handles_failure(self, mock_boto_client):
        """SQS should handle send failures gracefully"""
        mock_sqs = Mock()
        mock_sqs.send_message.side_effect = Exception("SQS Error")
        mock_boto_client.return_value = mock_sqs

        sqs_service = SQSService()
        sqs_service.initialise()

        result = sqs_service.send_event("test_event", {"key": "value"})

        assert not result  # Should return False, not raise
