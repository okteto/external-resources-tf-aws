FROM node:20-slim

WORKDIR /usr/src/app

ADD package.json .
RUN yarn install
COPY public public
COPY views views
COPY index.js .

EXPOSE 3000

CMD yarn start