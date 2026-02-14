FROM node:20-alpine

RUN apk add --no-cache git
RUN git config --system safe.directory /repo
RUN addgroup -g 1001 app && adduser -u 1001 -G app -D app

WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .

# Ensure /data is writable by the app user for conversation persistence
RUN mkdir -p /data && chown app:app /data

USER app
EXPOSE 3000
CMD ["node", "server.js"]
