FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Install additional dependencies
RUN npm install -D tailwindcss postcss autoprefixer

# Build application
RUN npm run build

# Expose port
EXPOSE 5173

# Run application
CMD ["npm", "run", "preview"]
