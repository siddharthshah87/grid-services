# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json bun.lockb ./
RUN npm install
COPY . .
ARG BACKEND_API_URL
ENV VITE_BACKEND_API_URL=$BACKEND_API_URL
RUN npm run build

# Run stage
FROM nginx:1.25-alpine

# Copy our built SPA
COPY --from=build /app/dist /usr/share/nginx/html

# Add a dedicated health‐check config
RUN printf 'location = /health {\n  return 200 "OK";\n  add_header Content-Type text/plain;\n}\n' \
    > /etc/nginx/conf.d/health.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

