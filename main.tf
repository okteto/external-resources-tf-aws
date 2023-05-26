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

output "queue_url" {
  value = aws_sqs_queue.orders_queue.url
  description = "The URL of the SQS queue"
}