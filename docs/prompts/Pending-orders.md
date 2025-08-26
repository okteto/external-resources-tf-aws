# Prompt
When the kitchen frontend conects to the /orders endpoint, always send all PendingOrders that are not ready and then send the PendingOrders coming from the channel

## Context 
- **Environment**: Okteto-based Kubernetes development environment 
- **Application**: 3-microservice architecture (menu, kitchen, check services) 
- **Goal**: When a user opens the frontend of the kitchen service, it always lists all the pending orders, even if they were created before the page was active

## Requirements
1. **Functionality**: When the frontend connects to the kitchen service, it alwasy gets all the pending orders that are not ready
2. **Functionality**: The frontend shouldn't assume that each pendingorder is unique (e.g. in case of reconnection) so it should filter accordingly

## Validation Criteria
1. Ensure that when an order is placed via the menu service, it is always displayed on the order service
2. Ensure that when the order service is reloaded, it gets all the existing orders that are not ready, and then, if a new order is placed on the menu service, it is displayed
3. Rest of the functionality works as expected 