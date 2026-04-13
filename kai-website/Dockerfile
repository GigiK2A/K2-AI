FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app

RUN npm i -g serve@14.2.4

COPY --from=build /app/dist ./dist

EXPOSE 4173

CMD ["sh", "-c", "serve dist -s -l tcp://0.0.0.0:${PORT:-4173}"]
