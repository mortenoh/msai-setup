# Development Stacks

Ready-to-use Docker Compose configurations for local development.

## Overview

Pre-configured stacks for common development scenarios:

- **Databases** - PostgreSQL, Redis, MongoDB with admin UIs
- **Full-stack templates** - Application + database + cache
- **Hot reload** - Development configurations with live reload

## PostgreSQL + pgAdmin

### Basic Setup

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: myapp
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev -d myapp"]
      interval: 5s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@local.dev
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: "False"
    ports:
      - "5050:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      - postgres

volumes:
  postgres_data:
  pgadmin_data:
```

### With Initialization Script

Create `init.sql`:

```sql
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create tables
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert seed data
INSERT INTO users (email) VALUES ('test@example.com');
```

### Connection Info

| Service | URL |
|---------|-----|
| PostgreSQL | `postgres://dev:devpassword@localhost:5432/myapp` |
| pgAdmin | http://localhost:5050 |

## Redis + RedisInsight

### Basic Setup

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  redisinsight:
    image: redis/redisinsight:latest
    ports:
      - "5540:5540"
    volumes:
      - redisinsight_data:/data
    depends_on:
      - redis

volumes:
  redis_data:
  redisinsight_data:
```

### With Password

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-devpassword}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

Connection: `redis://:devpassword@localhost:6379`

### Redis Stack (with modules)

```yaml
services:
  redis:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
      - "8001:8001"  # RedisInsight built-in
    volumes:
      - redis_data:/data
    environment:
      - REDIS_ARGS=--appendonly yes

volumes:
  redis_data:
```

## MongoDB + Mongo Express

### Basic Setup

```yaml
services:
  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: rootpassword
      MONGO_INITDB_DATABASE: myapp
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongo-express:
    image: mongo-express:latest
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: root
      ME_CONFIG_MONGODB_ADMINPASSWORD: rootpassword
      ME_CONFIG_MONGODB_URL: mongodb://root:rootpassword@mongodb:27017/
      ME_CONFIG_BASICAUTH: "false"
    ports:
      - "8081:8081"
    depends_on:
      mongodb:
        condition: service_healthy

volumes:
  mongodb_data:
```

### Initialization Script

Create `mongo-init.js`:

```javascript
db = db.getSiblingDB('myapp');

db.createUser({
  user: 'appuser',
  pwd: 'apppassword',
  roles: [{ role: 'readWrite', db: 'myapp' }]
});

db.createCollection('users');
db.users.insertOne({
  email: 'test@example.com',
  createdAt: new Date()
});
```

## Full-Stack: Node.js + PostgreSQL + Redis

### Project Structure

```
project/
├── docker-compose.yml
├── docker-compose.override.yml
├── .env
├── api/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
└── web/
    ├── Dockerfile
    ├── package.json
    └── src/
```

### docker-compose.yml

```yaml
services:
  api:
    build: ./api
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://dev:${DB_PASSWORD}@postgres:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - backend

  web:
    build: ./web
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api:8080
    depends_on:
      - api
    networks:
      - frontend
      - backend

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev -d myapp"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
    networks:
      - backend

networks:
  frontend:
  backend:

volumes:
  postgres_data:
  redis_data:
```

### Development Override

`docker-compose.override.yml`:

```yaml
services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api/src:/app/src
      - /app/node_modules
    ports:
      - "8080:8080"
      - "9229:9229"  # Debug port
    environment:
      - NODE_ENV=development
    command: npm run dev

  web:
    build:
      context: ./web
      target: development
    volumes:
      - ./web/src:/app/src
      - /app/node_modules
    environment:
      - NODE_ENV=development
    command: npm run dev

  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@local.dev
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: "False"
    ports:
      - "5050:80"
    networks:
      - backend
```

### API Dockerfile

```dockerfile
# api/Dockerfile
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./

FROM base AS development
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]

FROM base AS production
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["node", "dist/main.js"]
```

## Full-Stack: Python + PostgreSQL

### docker-compose.yml

```yaml
services:
  api:
    build: ./api
    environment:
      - DATABASE_URL=postgresql://dev:${DB_PASSWORD}@postgres:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - backend

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    networks:
      - backend

networks:
  backend:

volumes:
  postgres_data:
```

### Development Override

```yaml
services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api:/app
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Python Dockerfile

```dockerfile
# api/Dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
RUN pip install uv

FROM base AS development
COPY pyproject.toml uv.lock ./
RUN uv sync
COPY . .
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--reload"]

FROM base AS production
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

## Hot Reload Configurations

### Node.js with nodemon

```yaml
services:
  api:
    volumes:
      - ./src:/app/src
      - /app/node_modules
    command: npx nodemon --watch src src/index.js
```

### Python with uvicorn

```yaml
services:
  api:
    volumes:
      - ./app:/app
    command: uvicorn main:app --host 0.0.0.0 --reload --reload-dir /app
```

### React/Vite

```yaml
services:
  web:
    volumes:
      - ./src:/app/src
      - /app/node_modules
    environment:
      - CHOKIDAR_USEPOLLING=true
      - WATCHPACK_POLLING=true
    command: npm run dev -- --host 0.0.0.0
```

## Message Queue Stacks

### RabbitMQ

```yaml
services:
  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    ports:
      - "5672:5672"
      - "15672:15672"  # Management UI
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  rabbitmq_data:
```

### Kafka

```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
```

## Search Engines

### Elasticsearch + Kibana

```yaml
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

### Meilisearch

```yaml
services:
  meilisearch:
    image: getmeili/meilisearch:latest
    environment:
      MEILI_ENV: development
      MEILI_MASTER_KEY: devkey123
    ports:
      - "7700:7700"
    volumes:
      - meilisearch_data:/meili_data

volumes:
  meilisearch_data:
```

## Useful Commands

```bash
# Start development stack
docker compose up -d

# View logs
docker compose logs -f api

# Rebuild specific service
docker compose up -d --build api

# Reset database
docker compose down -v postgres
docker compose up -d postgres

# Shell into container
docker compose exec api sh

# Run migrations
docker compose exec api npm run migrate
```

## See Also

- [Docker Compose](compose.md) - Compose reference
- [Ollama Stack](ollama-stack.md) - Local AI setup
- [Monitoring](monitoring.md) - Container monitoring
