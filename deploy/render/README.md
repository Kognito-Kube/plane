# Render Deployment Guide for Plane v1.3.1

This guide walks you through deploying Plane on Render.com using the Blueprint method.

## Prerequisites

- Render.com account with billing enabled
- GitHub repository (your fork of makeplane/plane)
- Domain name (optional, can use Render's `.onrender.com` subdomain)

## Quick Start

### 1. Generate Credentials

Generate secure passwords for all services:

```bash
# PostgreSQL password
openssl rand -base64 32

# RabbitMQ password
openssl rand -base64 32

# MinIO access key (20 chars)
openssl rand -hex 10

# MinIO secret key (40 chars)
openssl rand -hex 20
```

### 2. Deploy Using Blueprint

1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub account and select your forked Plane repository
4. Select the `render-deployment` branch
5. Render will parse `render.yaml` and show all services to be created
6. Click "Apply" to start deployment

### 3. Configure Environment Variables

After services are created, update environment variables in Render Dashboard:

**For plane-db:**
- `POSTGRES_USER`: plane
- `POSTGRES_PASSWORD`: <your-generated-password>

**For plane-mq:**
- `RABBITMQ_DEFAULT_USER`: plane
- `RABBITMQ_DEFAULT_PASS`: <your-generated-password>

**For plane-minio:**
- `MINIO_ROOT_USER`: <your-generated-access-key>
- `MINIO_ROOT_PASSWORD`: <your-generated-secret-key>

**For plane-api:**
- `WEB_URL`: https://plane-web-<your-subdomain>.onrender.com
- `ADMIN_BASE_URL`: https://plane-admin-<your-subdomain>.onrender.com
- `SPACE_BASE_URL`: https://plane-space-<your-subdomain>.onrender.com
- `LIVE_BASE_URL`: https://plane-live-<your-subdomain>.onrender.com
- `CORS_ALLOWED_ORIGINS`: https://plane-web-<your-subdomain>.onrender.com,https://plane-admin-<your-subdomain>.onrender.com,https://plane-space-<your-subdomain>.onrender.com

**For plane-web, plane-admin, plane-space:**
- `VITE_API_BASE_URL`: https://plane-api-<your-subdomain>.onrender.com

### 4. Run Database Migrations

1. In Render Dashboard, go to "plane-migrator" job
2. Click "Manual Deploy" → "Deploy latest commit"
3. Wait for job to complete (should exit with code 0)

### 5. Initialize MinIO Storage

1. Access MinIO console at: https://plane-minio-<your-subdomain>.onrender.com:9090
2. Login with your MinIO credentials
3. Create bucket named "uploads"

### 6. Create Admin User

1. Open https://plane-admin-<your-subdomain>.onrender.com/god-mode
2. Follow the setup wizard to create your admin account
3. Configure instance settings

### 7. Access Your Plane Instance

Open https://plane-web-<your-subdomain>.onrender.com and start using Plane!

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┬────────────┬────────────┐
    │            │            │            │            │
┌───▼───┐  ┌────▼────┐  ┌───▼───┐  ┌────▼────┐  ┌───▼───┐
│  web  │  │  admin  │  │ space │  │  live   │  │  api  │
│ :3000 │  │  :3001  │  │ :3002 │  │  :3100  │  │ :8000 │
└───┬───┘  └────┬────┘  └───┬───┘  └────┬────┘  └───┬───┘
    │           │            │            │            │
    └───────────┴────────────┴────────────┴────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
    │   db    │   │   redis   │  │   mq    │
    │ :5432   │   │   :6379   │  │  :5672  │
    └─────────┘   └───────────┘  └─────────┘
                        │
                   ┌────▼────┐
                   │  minio  │
                   │  :9000  │
                   └─────────┘
```

## Services List

| Service | Type | Port | Description |
|---------|------|------|-------------|
| plane-db | Private Service | 5432 | PostgreSQL database |
| plane-redis | Managed Redis | 6379 | Cache and message queue |
| plane-mq | Private Service | 5672 | RabbitMQ message broker |
| plane-minio | Private Service | 9000/9090 | S3-compatible storage |
| plane-api | Web Service | 8000 | Django REST API |
| plane-worker | Background Worker | - | Celery background tasks |
| plane-beat-worker | Background Worker | - | Celery scheduler |
| plane-migrator | Job (manual) | - | Database migrations |
| plane-web | Web Service | 3000 | Main frontend |
| plane-admin | Web Service | 3001 | Admin panel |
| plane-space | Web Service | 3002 | Public spaces |
| plane-live | Web Service | 3100 | Real-time collaboration |

## Estimated Cost

**~$75/month** for a complete deployment:
- PostgreSQL (10GB disk): $7/month
- Redis (256MB): $5/month
- RabbitMQ (Starter): $7/month
- MinIO (Starter): $7/month
- API (Starter): $7/month
- Worker (Starter): $7/month
- Beat Worker (Starter): $7/month
- Web (Starter): $7/month
- Admin (Starter): $7/month
- Space (Starter): $7/month
- Live (Starter): $7/month

## Troubleshooting

### Services fail to start
- Check logs for environment variable errors
- Verify all service URLs are correct
- Ensure database is fully initialized before API starts

### CORS errors
- Update `CORS_ALLOWED_ORIGINS` with exact frontend URLs
- Include both `https://` and `http://` variants if needed
- Redeploy API service after changes

### File uploads fail
- Verify MinIO bucket "uploads" exists
- Check MinIO credentials in API environment
- Verify `AWS_S3_ENDPOINT_URL` is correct

### Database migration fails
- Run migrator job manually
- Check migration logs for errors
- Verify database credentials

## Maintenance

### Regular Tasks

**Weekly:**
- Check service logs for errors
- Monitor resource usage
- Review backup status

**Monthly:**
- Update to latest Plane version
- Review and rotate credentials
- Test backup restore procedure

### Backups

- PostgreSQL: Automatic daily backups (Render managed)
- MinIO: Configure manual backup script
- Redis: Ephemeral cache, no backup needed

## Support

- Plane Documentation: https://docs.plane.so/
- Plane GitHub: https://github.com/makeplane/plane
- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com