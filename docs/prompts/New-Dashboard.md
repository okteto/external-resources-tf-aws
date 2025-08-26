# Prompt
Implement a dashboard in the check service to provide  better visibility into order data. 
## Context 
- **Environment**: Okteto-based Kubernetes development environment 
- **Application**: 3-microservice architecture (menu, kitchen, check services) 
- **Current State**: Check information is stored in memory
- **Goal**: Every check is stored in a SQL database, and there's a dashboard that shows information

## Requirements
1. Store the data on a PostgreSQL instance running on kubernetes deployed using Helm
2. Build a web dashboard showing real-time order statistics, the most popular food items, and a paginated view of all the stored orders sorted by date
3. Implement smart item normalization to clean up messy order data:  Extract quantities from text, handle case variations, normalize plurar forms, group similar items together (e.g., 'taco', 'tacos', 'TACOS' all count as 'taco')
4. Keep the same theme, colors, and fonts than the current version of the check service
5. Include database migrations and proper connection handling 
6. Update documentation with the new dashboard access instructions 
7. Add tests to validate the functionality

## Validation Criteria
1. Orders are stored on the database
2. The dashboard loads all the orders sorted by order date
3. The most popular items are correctly displayed
4. Every order placed updates the dashboard and database
5. Main end to end workflow works as expected


