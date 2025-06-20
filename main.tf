terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.67.0"
    }
  }

  backend "kubernetes" {
    secret_suffix    = "okteto"
  }
  
  required_version = ">= 1.2.0"
}

variable "bucket_name" {
  description = "Name of the S3 Bucket"
  type        = string
  default     = ""
  validation {
    condition     = length(var.bucket_name) > 1
    error_message = "Please specify the name of the S3 bucket"
  }
}

variable "queue_name" {
  description = "Name of the SQS Queue"
  type        = string
  default     = ""
  validation {
    condition     = length(var.queue_name) > 1
    error_message = "Please specify the name of the SQS queue"
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

provider "aws" {
  region  = var.region
}

resource "aws_s3_bucket" "checks_bucket" {
    bucket = var.bucket_name
    force_destroy = true
}

resource "aws_sqs_queue" "orders_queue"  {
    name = var.queue_name       
}

# Create dedicated IAM user for the application
resource "aws_iam_user" "app_user" {
  name = "${var.bucket_name}-app-user"
  path = "/"

  tags = {
    Name        = "${var.bucket_name}-app-user"
    Environment = "okteto"
    ManagedBy   = "terraform"
  }
}

# Create IAM policy with minimal required permissions
resource "aws_iam_policy" "app_policy" {
  name        = "${var.bucket_name}-app-policy"
  path        = "/"
  description = "Policy for ${var.bucket_name} application access to S3 and SQS"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.checks_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.checks_bucket.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl"
        ]
        Resource = aws_sqs_queue.orders_queue.arn
      }
    ]
  })

  tags = {
    Name        = "${var.bucket_name}-app-policy"
    Environment = "okteto"
    ManagedBy   = "terraform"
  }
}

# Attach policy to user
resource "aws_iam_user_policy_attachment" "app_policy_attachment" {
  user       = aws_iam_user.app_user.name
  policy_arn = aws_iam_policy.app_policy.arn
}

# Create access keys for the IAM user
resource "aws_iam_access_key" "app_access_key" {
  user = aws_iam_user.app_user.name
}

output "queue_url" {
  value = aws_sqs_queue.orders_queue.url
  description = "The URL of the SQS queue"
}

output "iam_access_key_id" {
  value = aws_iam_access_key.app_access_key.id
  description = "The access key ID for the dedicated IAM user"
}

output "iam_secret_access_key" {
  value = aws_iam_access_key.app_access_key.secret
  description = "The secret access key for the dedicated IAM user"
  sensitive = true
}