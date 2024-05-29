# app

Things to do before deploying for production:

- In the file `.env.prod`,
    - Need to update DJANGO_ALLOWED_HOSTS with the deployment IP,
    - Need to update SECRET_KEY for security.

## Commands

- Docker up
    - Production: `docker compose up --build -d`,
    - Dev: `docker compose -f docker-compose.dev.yml up --build -d`,
- Docker down: `docker compose down`.
