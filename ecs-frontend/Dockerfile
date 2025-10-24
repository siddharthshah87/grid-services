# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json bun.lockb ./
RUN npm install
COPY . .
RUN npm run build

# Run stage
FROM nginx:1.25-alpine

# Copy our built SPA
COPY --from=build /app/dist /usr/share/nginx/html
# Replace the default Nginx config to add a health endpoint
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
