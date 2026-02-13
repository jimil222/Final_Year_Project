# Docker Setup Guide

This project uses Docker and Docker Compose to containerize and orchestrate all services.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Project Structure

```
Recommend/
├── docker-compose.yml          # Main orchestration file
├── Backend/
│   ├── Dockerfile             # Backend container definition
│   └── .dockerignore          # Files to exclude from build
└── Libra_Automated_Library/
    ├── Dockerfile             # Frontend container definition
    └── .dockerignore          # Files to exclude from build
```

## Services

1. **Backend API** (port 8000)
   - FastAPI application
   - Connects to external cloud MySQL database
   - Auto-runs Prisma migrations on startup
   - API Documentation: http://localhost:8000/docs

2. **Frontend** (port 5173)
   - React + Vite application
   - Served via Nginx
   - Accessible at: http://localhost:5173

**Note**: This setup uses an external cloud MySQL database. The `DATABASE_URL` environment variable must be provided.

## Quick Start

### 1. Set Environment Variables

Create a `.env` file in the project root (or export environment variables):

```bash
# Required: Cloud MySQL database connection string
DATABASE_URL=mysql://user:password@host:port/database

# Optional: JWT and other settings (defaults provided)
SECRET_KEY=your_super_secret_key_change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MIN_RETURN_TIME_SECONDS=10
VITE_API_URL=http://localhost:8000
```

### 2. Build and Start All Services

```bash
docker-compose up --build
```

This will:
- Build all Docker images
- Start Backend API (waits for cloud database connection)
- Start Frontend (waits for backend to be ready)

### 2. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MySQL**: localhost:3306

### 3. Stop All Services

```bash
docker-compose down
```

To also remove volumes (database data):

```bash
docker-compose down -v
```

## Development Mode

For development with hot-reload, uncomment the volumes section in `docker-compose.yml` for the backend service:

```yaml
volumes:
  - ./Backend:/app
  - /app/venv
```

Then rebuild:

```bash
docker-compose up --build
```

**Note**: Hot-reload requires uvicorn's `--reload` flag. You may need to modify the Dockerfile CMD for development.

## Environment Variables

### Required Environment Variables

**`DATABASE_URL`** (Required): MySQL connection string for your cloud database
- Format: `mysql://user:password@host:port/database`
- Example: `mysql://admin:password@mysql.example.com:3306/libra_db`
- Can be set via `.env` file or environment variable

### Optional Environment Variables

**Backend:**
- `SECRET_KEY`: JWT secret key (default: `your_super_secret_key_change_this_in_production`)
- `ALGORITHM`: JWT algorithm (default: `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: `1440`)
- `MIN_RETURN_TIME_SECONDS`: Minimum time before book can be returned (default: `10`)

**Frontend:**
- `VITE_API_URL`: Backend API URL (default: `http://localhost:8000`)

### Setting Environment Variables

**Option 1: Using .env file** (Recommended)
Create a `.env` file in the project root:
```bash
DATABASE_URL=mysql://user:password@host:port/database
SECRET_KEY=your_secret_key
```

**Option 2: Export before running**
```bash
export DATABASE_URL=mysql://user:password@host:port/database
docker-compose up
```

**Option 3: Inline with docker-compose**
```bash
DATABASE_URL=mysql://user:password@host:port/database docker-compose up
```

## Database Management

Since this setup uses a cloud MySQL database, manage it through your cloud provider's tools or connect directly:

### Connect to Cloud Database

Use your cloud provider's connection method or MySQL client:

```bash
mysql -h your-cloud-host -u your-user -p your-database
```

### Run Migrations Manually

If needed, you can run Prisma migrations manually:

```bash
docker-compose exec backend python -m prisma db push
```

### Backup Database

Use your cloud provider's backup tools or:

```bash
mysqldump -h your-cloud-host -u your-user -p your-database > backup.sql
```

## Troubleshooting

### Backend fails to start

1. Verify `DATABASE_URL` is set correctly:
   ```bash
   echo $DATABASE_URL
   ```

2. Check backend logs for database connection errors:
   ```bash
   docker-compose logs backend
   ```

3. Ensure your cloud database is accessible from the Docker container:
   - Check firewall rules
   - Verify network connectivity
   - Confirm database credentials are correct

### Frontend can't connect to backend

1. Ensure backend is running:
   ```bash
   docker-compose ps
   ```

2. Check if `VITE_API_URL` in docker-compose.yml matches your setup

3. Check browser console for CORS errors (backend CORS config may need updating)

### Database connection issues

1. Verify `DATABASE_URL` environment variable is set:
   ```bash
   docker-compose exec backend env | grep DATABASE_URL
   ```

2. Test database connectivity from the backend container:
   ```bash
   docker-compose exec backend python -c "from app.db import connect_db; import asyncio; asyncio.run(connect_db())"
   ```

3. Check cloud database:
   - Verify database is running and accessible
   - Check firewall/security group rules allow connections
   - Confirm credentials are correct
   - Ensure SSL/TLS settings match your connection string

### Rebuild Everything

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

**Note**: Since we're using a cloud database, there's no local volume to remove.

## Production Considerations

1. **Change SECRET_KEY**: Update `SECRET_KEY` in `docker-compose.yml` with a strong random value

2. **Use Environment Files**: Create `.env` files and reference them in docker-compose.yml:
   ```yaml
   env_file:
     - .env.backend
   ```

3. **Remove Volume Mounts**: Don't use volume mounts in production (already commented out)

4. **Database**: Already using cloud database - ensure proper security and backups

5. **Add Reverse Proxy**: Use Traefik or Nginx as reverse proxy in front of services

6. **Enable HTTPS**: Configure SSL certificates

7. **Resource Limits**: Add resource limits to services:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 512M
   ```

## Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Restart a service
docker-compose restart backend

# Execute command in container
docker-compose exec backend python seed_books.py

# Scale services (if needed)
docker-compose up --scale backend=2

# Clean up everything
docker-compose down -v --rmi all
```
