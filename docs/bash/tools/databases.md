# Databases

Quick reference for common database systems: PostgreSQL, Redis, MongoDB, MySQL, and others. Includes Docker commands, CLI usage, and connection strings.

## PostgreSQL

### Docker Quick Start

```bash
# Run PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16

# With specific database and user
docker run -d \
  --name postgres \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=mydb \
  -p 5432:5432 \
  postgres:16
```

### Docker Aliases (Multiple Versions)

```bash
# PostgreSQL version aliases
alias pg12='docker run -d --name pg12 -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:12'
alias pg13='docker run -d --name pg13 -p 5433:5432 -e POSTGRES_PASSWORD=postgres postgres:13'
alias pg14='docker run -d --name pg14 -p 5434:5432 -e POSTGRES_PASSWORD=postgres postgres:14'
alias pg15='docker run -d --name pg15 -p 5435:5432 -e POSTGRES_PASSWORD=postgres postgres:15'
alias pg16='docker run -d --name pg16 -p 5436:5432 -e POSTGRES_PASSWORD=postgres postgres:16'
alias pg17='docker run -d --name pg17 -p 5437:5432 -e POSTGRES_PASSWORD=postgres postgres:17'
```

### Connection Strings

```bash
# Standard format
postgresql://user:password@localhost:5432/dbname

# With options
postgresql://user:password@localhost:5432/dbname?sslmode=require

# Environment variable
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

### psql CLI

```bash
# Connect
psql -h localhost -U postgres -d mydb
psql postgresql://user:password@localhost:5432/dbname

# Execute command
psql -c "SELECT version();"
psql -f script.sql

# Within psql
\l              # List databases
\c dbname       # Connect to database
\dt             # List tables
\d tablename    # Describe table
\du             # List users
\dn             # List schemas
\df             # List functions
\di             # List indexes
\q              # Quit
```

### Common SQL

```sql
-- Database operations
CREATE DATABASE mydb;
DROP DATABASE mydb;

-- User operations
CREATE USER myuser WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
ALTER USER myuser WITH SUPERUSER;

-- Table operations
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_users_email ON users(email);

-- Query
SELECT * FROM users WHERE created_at > NOW() - INTERVAL '7 days';

-- Backup and restore
pg_dump mydb > backup.sql
pg_dump -Fc mydb > backup.dump
psql mydb < backup.sql
pg_restore -d mydb backup.dump
```

## Redis

### Docker Quick Start

```bash
# Run Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7

# With persistence
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redisdata:/data \
  redis:7 redis-server --appendonly yes

# With password
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7 redis-server --requirepass mypassword
```

### Docker Alias

```bash
alias redis='docker run -d --name redis -p 6379:6379 redis:7'
```

### Connection Strings

```bash
# Standard
redis://localhost:6379

# With password
redis://:password@localhost:6379

# With database number
redis://localhost:6379/0

# TLS
rediss://localhost:6379
```

### redis-cli

```bash
# Connect
redis-cli
redis-cli -h localhost -p 6379
redis-cli -a password

# Execute command
redis-cli PING
redis-cli GET mykey

# Within redis-cli
PING                    # Test connection
INFO                    # Server info
DBSIZE                  # Number of keys
KEYS *                  # List all keys (careful in production!)
SCAN 0                  # Safe key iteration
```

### Common Commands

```bash
# Strings
SET key "value"
GET key
INCR counter
EXPIRE key 3600         # TTL in seconds
TTL key                 # Check TTL

# Hashes
HSET user:1 name "John" email "john@example.com"
HGET user:1 name
HGETALL user:1

# Lists
LPUSH queue "item1"
RPOP queue
LRANGE queue 0 -1

# Sets
SADD tags "redis" "database"
SMEMBERS tags
SISMEMBER tags "redis"

# Sorted Sets
ZADD scores 100 "player1" 200 "player2"
ZRANGE scores 0 -1 WITHSCORES
ZRANK scores "player1"

# Keys
DEL key
EXISTS key
TYPE key
RENAME oldkey newkey

# Pub/Sub
SUBSCRIBE channel
PUBLISH channel "message"

# Transactions
MULTI
SET key1 "value1"
SET key2 "value2"
EXEC
```

## MongoDB

### Docker Quick Start

```bash
# Run MongoDB
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  mongo:7

# With authentication
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  -v mongodata:/data/db \
  mongo:7
```

### Docker Alias

```bash
alias mongo='docker run -d --name mongodb -p 27017:27017 mongo:7'
```

### Connection Strings

```bash
# Standard
mongodb://localhost:27017

# With authentication
mongodb://admin:password@localhost:27017

# With database
mongodb://admin:password@localhost:27017/mydb?authSource=admin

# Replica set
mongodb://host1:27017,host2:27017,host3:27017/?replicaSet=rs0
```

### mongosh CLI

```bash
# Connect
mongosh
mongosh "mongodb://localhost:27017"
mongosh --host localhost --port 27017 -u admin -p password

# Within mongosh
show dbs                # List databases
use mydb               # Switch database
show collections       # List collections
db.stats()             # Database stats
```

### Common Operations

```javascript
// Insert
db.users.insertOne({ name: "John", email: "john@example.com" });
db.users.insertMany([{ name: "Jane" }, { name: "Bob" }]);

// Find
db.users.find();
db.users.find({ name: "John" });
db.users.findOne({ _id: ObjectId("...") });
db.users.find({ age: { $gt: 18 } });
db.users.find().limit(10).sort({ name: 1 });

// Update
db.users.updateOne({ name: "John" }, { $set: { age: 30 } });
db.users.updateMany({}, { $set: { active: true } });

// Delete
db.users.deleteOne({ name: "John" });
db.users.deleteMany({ active: false });

// Index
db.users.createIndex({ email: 1 }, { unique: true });
db.users.getIndexes();

// Aggregation
db.users.aggregate([
  { $match: { active: true } },
  { $group: { _id: "$city", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
]);

// Backup (from shell)
// mongodump --db mydb --out /backup
// mongorestore --db mydb /backup/mydb
```

## MySQL

### Docker Quick Start

```bash
# Run MySQL
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=mydb \
  -e MYSQL_USER=myuser \
  -e MYSQL_PASSWORD=mypassword \
  -p 3306:3306 \
  -v mysqldata:/var/lib/mysql \
  mysql:8
```

### Docker Aliases

```bash
alias mysql8='docker run -d --name mysql8 -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql:8'
alias mysql9='docker run -d --name mysql9 -p 3307:3306 -e MYSQL_ROOT_PASSWORD=root mysql:9'
```

### Connection Strings

```bash
# Standard
mysql://user:password@localhost:3306/dbname

# JDBC
jdbc:mysql://localhost:3306/dbname

# With options
mysql://user:password@localhost:3306/dbname?useSSL=false
```

### mysql CLI

```bash
# Connect
mysql -h localhost -u root -p
mysql -h localhost -u user -p dbname

# Execute
mysql -e "SHOW DATABASES;"
mysql dbname < script.sql

# Within mysql
SHOW DATABASES;
USE dbname;
SHOW TABLES;
DESCRIBE tablename;
SHOW CREATE TABLE tablename;
```

### Common SQL

```sql
-- Database
CREATE DATABASE mydb;
USE mydb;

-- User
CREATE USER 'myuser'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON mydb.* TO 'myuser'@'%';
FLUSH PRIVILEGES;

-- Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Backup
-- mysqldump -u root -p mydb > backup.sql
-- mysql -u root -p mydb < backup.sql
```

## Elasticsearch

### Docker Quick Start

```bash
# Single node
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -v esdata:/usr/share/elasticsearch/data \
  elasticsearch:8.11.0

# With Kibana
docker run -d \
  --name kibana \
  --link elasticsearch \
  -p 5601:5601 \
  kibana:8.11.0
```

### Basic Operations

```bash
# Check cluster health
curl localhost:9200/_cluster/health?pretty

# List indices
curl localhost:9200/_cat/indices?v

# Create index
curl -X PUT localhost:9200/myindex

# Index document
curl -X POST localhost:9200/myindex/_doc -H 'Content-Type: application/json' -d '
{
  "title": "My Document",
  "content": "This is the content"
}'

# Search
curl localhost:9200/myindex/_search?pretty -H 'Content-Type: application/json' -d '
{
  "query": {
    "match": {
      "content": "content"
    }
  }
}'

# Delete index
curl -X DELETE localhost:9200/myindex
```

## Other Services

### RabbitMQ

```bash
# Docker
docker run -d \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management

# Management UI: http://localhost:15672 (guest/guest)
```

### ClickHouse

```bash
# Docker
docker run -d \
  --name clickhouse \
  -p 8123:8123 \
  -p 9000:9000 \
  clickhouse/clickhouse-server

# CLI
docker exec -it clickhouse clickhouse-client

# HTTP API
curl 'http://localhost:8123/?query=SELECT%201'
```

### Prometheus

```bash
# Docker
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# UI: http://localhost:9090
```

### Grafana

```bash
# Docker
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana

# UI: http://localhost:3000 (admin/admin)
```

## Docker Compose Example

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data

  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - "27017:27017"
    volumes:
      - mongodata:/data/db

volumes:
  pgdata:
  redisdata:
  mongodata:
```

## Connection Management

### Environment Variables

```bash
# Add to ~/.bashrc or .env
export DATABASE_URL="postgresql://user:password@localhost:5432/mydb"
export REDIS_URL="redis://localhost:6379"
export MONGODB_URL="mongodb://admin:password@localhost:27017/mydb?authSource=admin"
```

### GUI Tools

- **PostgreSQL**: pgAdmin, DBeaver, TablePlus
- **Redis**: RedisInsight, Another Redis Desktop Manager
- **MongoDB**: MongoDB Compass, Studio 3T
- **MySQL**: MySQL Workbench, DBeaver, TablePlus
- **Universal**: DBeaver (supports many databases)

## Related Tools

- [Docker](../../docker/index.md) - Container runtime
- [lazydocker](lazydocker.md) - Docker TUI
