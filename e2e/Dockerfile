FROM mcr.microsoft.com/playwright:v1.49.0-noble

RUN corepack enable yarn

COPY package.json yarn.lock ./
RUN yarn install
COPY . .