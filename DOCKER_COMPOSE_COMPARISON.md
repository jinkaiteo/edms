# Docker Compose Comparison: Local vs Production

## 📊 Quick Answer

**NO, they are DIFFERENT!**

**Current**: Using `docker-compose.yml` (development)  
**Deployment Script**: Will use `docker-compose.prod.yml` (production)

---

## 🔍 Detailed Comparison

### Container Names

| Service | Current (docker-compose.yml) | Production (docker-compose.prod.yml) |
|---------|------------------------------|--------------------------------------|
| Database | `edms_db` | `edms_prod_db` |
| Redis | `edms_redis` | `edms_prod_redis` |
| Backend | `edms_backend` | `edms_prod_backend` |
| Frontend | `edms_frontend` | `edms_prod_frontend` |
| Celery Worker | `edms_celery_worker` | `edms_prod_celery_worker` |
| Celery Beat | `edms_celery_beat` | `edms_prod_celery_beat` |

---

## 🔑 Key Differences

Let me analyze both files to show the exact differences...

