terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true

  endpoints {
    sqs      = "http://localhost:4566"
    dynamodb = "http://localhost:4566"
  }
}

# Starting simple with just one resource
resource "aws_sqs_queue" "student_events" {
  name = "student-events"
  message_retention_seconds = 86400  # 1 day
}

# Add DynamoDB table
resource "aws_dynamodb_table" "audit_logs" {
  name           = "sre-playground-audit"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  range_key      = "timestamp"
  
  attribute {
    name = "id"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "S"
  }
  
  tags = {
    Environment = "development"
  }
}

output "queue_url" {
  value = aws_sqs_queue.student_events.url
}