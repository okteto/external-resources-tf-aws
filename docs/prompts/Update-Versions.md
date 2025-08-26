# Prompt
You are tasked with updating all microservices in a cloud-native application to their latest runtime versions and addressing high/critical CVEs in dependencies. This includes updating Docker base images, language runtimes, and all associated dependencies while ensuring full functionality.

## Context 
- **Environment**: Okteto-based Kubernetes development environment 
- **Application**: 3-microservice architecture (menu, kitchen, check services) 
- **Goal**: Each service is built with the latest version of their runtime and their dependencies

## Requirements
1. Update each service to the latest stable version of their framework
2. Update all dependencies to the latest available version if they have a high or critical CVE

## Validation Criteria
1. Ensure that all  the services start and don't log errors
2. Main end to end workflow works as expected
3. All tests pass
4. None of the services  have any high or critical CVEs