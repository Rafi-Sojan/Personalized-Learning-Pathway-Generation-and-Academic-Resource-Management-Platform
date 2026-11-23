FROM node:24.22.1-alpine AS build
WORKDIR /app

ARG VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_API_URL=${VITE_API_URL}

COPY package*.json ./
RUN npm install --global npm@11.21.1 && npm ci

COPY . .
RUN npm run build

# Production Nginx image
FROM nginx:1.31.9-alpine@sha256:fb4658584bd9a916ffb6f6e365f97c25cfdb2923801f551ea08356e695f14ff7

# Upgrade vulnerable Alpine libxslt package
RUN apk upgrade --no-cache libxslt

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
