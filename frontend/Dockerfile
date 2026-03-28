# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build output from stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80 (standard for web servers and ECS config)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
 
