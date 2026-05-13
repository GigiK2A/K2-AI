FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Build kbot Next.js static export
FROM node:20-alpine AS kbot-build

WORKDIR /kbot

COPY kbot/package*.json ./
RUN npm ci

COPY kbot/ .
RUN npm run build

FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

RUN apk add --no-cache \
    ca-certificates \
    chromium \
    freetype \
    harfbuzz \
    nss \
    ttf-freefont

COPY package*.json ./
RUN npm ci --omit=dev

COPY --from=build /app/dist ./dist
COPY --from=kbot-build /kbot/out ./dist/app
COPY server.js ./server.js
COPY lib ./lib

EXPOSE 4173

CMD ["node", "server.js"]
