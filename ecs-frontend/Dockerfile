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
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
