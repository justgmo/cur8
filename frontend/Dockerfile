FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
EXPOSE 5173

# VITE_API_URL must be the URL the *browser* uses to reach the backend (e.g. http://localhost:8000)
CMD ["npm", "run", "dev"]
