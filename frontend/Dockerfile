FROM node:24.22.1-alpine AS build
WORKDIR /app
ARG VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_API_URL=${VITE_API_URL}
COPY package*.json ./
RUN npm install --global npm@11.21.1 && npm ci
COPY . .
RUN npm run build

FROM nginx:1.29.2-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
