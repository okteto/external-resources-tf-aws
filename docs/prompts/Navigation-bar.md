# Prompt
You are tasked with adding a nav bar to all the microservices that allows a user to quickly navigate from one microservice to the other microservices. 

## Context 
- **Environment**: Okteto-based Kubernetes development environment 
- **Application**: 3-microservice architecture (menu, kitchen, check services) 
- **Goal**: Each service displays the same navigation bar, allowing a user to click on a link to go to the other microservices

## Requirements
1. **Design**: Rectangular navigation bar matching the page-container styling and width
2. **Content**: Clean text links "MENU", "KITCHEN", "CHECK" (no emojis), uppercase, centered
3. **Positioning**: Fixed at top (1em from top), ensure logo has highest z-index (200) and is never blocked
4. **Spacing**: Increase padding to create proper clearance between nav and page content
5. **URLs**: Use relative/dynamic URLs that work across different Kubernetes namespaces
6. **Functionality**: Highlight current page in yellow, hover effects in pink
7. **Consistency**: Apply identical styling and functionality to all three services

## Validation Criteria
1. Ensure that all services display the same navigation bar
2. All the elements work
3. Clicking on each element of the navigation bar takes you to the other services on the same Kubernetes namespace