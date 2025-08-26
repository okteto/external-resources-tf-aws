# Prompt
You are tasked with adding a nav bar to all the microservices that allows a user to quickly navigate from one microservice to the other microservices. 

## Context 
- **Environment**: Okteto-based Kubernetes development environment 
- **Application**: 3-microservice architecture (menu, kitchen, check services) 
- **Goal**: Each service displays the same navigation bar, allowing a user to click on a link to go to the other microservices

## Requirements
1. Update each service's html to include navigation bar to all the microservices
2. Use the existing look and feel
3. URLs are not hardcoded, use relative links so the application is portable across Kubernetes namespaces

## Validation Criteria
1. Ensure that all services display the same navigation bar
2. All the elements work
3. Clicking on each element of the navigation bar takes you to the other services on the same Kubernetes namespace