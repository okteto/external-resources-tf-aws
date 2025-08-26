# Prompt
Implement Dedicated IAM Credentials for Microservices Development Environment You are an expert Cloud Native and AWS security engineer. Your task is to implement dedicated IAM users, roles, and keys for each microservice in a development environment, replacing shared credentials with service-specific ones that follow the principle of least privilege. 

## Context 
- **Environment**: Okteto-based Kubernetes development environment 
- **Application**: 3-microservice architecture (menu, kitchen, check services) 
- **Current State**: All services share the same AWS credentials 
- **Goal**: Each service gets its own dedicated IAM user with minimal required permissions 

## Requirements
1. **Dedicated IAM Resources**: Create separate IAM users, roles, and access keys for each service 
2. **Principle of Least Privilege**: Each service can ONLY access its specific AWS resources 
3. **Lifecycle Management**: IAM resources must be created/destroyed with the environment 
4. **Development-Friendly**: Simple terraform output extraction, use output and environment variables 
5. **Create dedicated Kubernetes secret per service** 
6. **Create end to end tests**: Create tests that validate the end to end functionality of each service as needed

## Validation Criteria
1. Unique Credentials: Each service has different AWS access keys 
2. Least Privilege: Menu can't access S3, Check can't access SQS, etc. 
3. Working Services: All microservices deploy and run successfully 
4. Clean Lifecycle: okteto destroy removes all IAM resources 
5. Main end to end workflow works as expected
