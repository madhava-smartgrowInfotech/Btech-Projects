FROM node:20-alpine
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV FRONTEND_HOST=0.0.0.0 FRONTEND_PORT=5414
EXPOSE 5414
CMD ["npm", "run", "dev"]
