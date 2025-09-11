# syntax=docker/dockerfile:1

FROM node:20-alpine AS base

WORKDIR /app

# Install production deps from root package.json (server deps live there)
COPY package.json package-lock.json ./
RUN npm ci --only=production || npm install --only=production

# Add curl for container healthchecks
RUN apk add --no-cache curl

# Copy server source
COPY server ./server

EXPOSE 5000

CMD ["node", "server/index.js"]

