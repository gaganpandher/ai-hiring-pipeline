FROM node:20-alpine

WORKDIR /app

# Copy only package files for dependency installation
COPY package.json ./
COPY package-lock.json* ./

# Install dependencies
RUN npm install

# Verify tools work
RUN node --version && npm --version && npx vite --version

EXPOSE 3000

# Source files are mounted via docker-compose volumes at runtime
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3000"]