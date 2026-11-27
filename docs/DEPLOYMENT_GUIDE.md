# K² FRS — Production Deployment & Secrets Configuration Guide

## 1. Overview
This document specifies the exact environment variables, GitHub Actions secrets, and hosting architectures required to deploy **K² FRS** into institutional production at Kakatiya University College of Engineering & Technology (KUCET).

---

## 2. GitHub Actions Deployment Secrets Setup

To enable fully automated CD deployments to cloud / on-premise servers and signed Android APK releases, configure the following secrets under **GitHub Repository Settings -> Secrets and variables -> Actions**:

### A. Android Release APK Production Signing
| Secret Name | Description | Mandatory for Production |
| :--- | :--- | :--- |
| `KEYSTORE_BASE64` | Base64-encoded binary content of the institutional `.jks` file | Yes |
| `KEYSTORE_PASSWORD` | Passphrase encrypting the Java KeyStore | Yes |
| `KEY_ALIAS` | Key alias (e.g., `k2_frs_release_key`) | Yes |
| `KEY_PASSWORD` | Passphrase protecting the private key | Yes |
| `STRICT_RELEASE_SIGNING`| Set to `true` to fail the build if official keystore is missing | Recommended |

*(For instructions on generating the institutional 4096-bit RSA keystore, refer to [RELEASE_SIGNING_SETUP.md](file:///d:/k%5E2/docs/operations/RELEASE_SIGNING_SETUP.md).)*

### B. Live Host & Container Stack Deployment
The `.github/workflows/deploy.yml` pipeline supports two production deployment mechanisms:

#### Option 1: Automated Target Host Webhook (Recommended for Cloud Run / Render / Portainer)
| Secret Name | Description |
| :--- | :--- |
| `DEPLOY_WEBHOOK_URL` | HTTPS webhook URL triggered via POST to redeploy updated container images from GHCR |

#### Option 2: Remote SSH Docker Compose Rollout (On-Premise Server)
| Secret Name | Description |
| :--- | :--- |
| `HOST_SSH_IP` | Static IPv4 / FQDN of the institutional on-premise server |
| `HOST_SSH_USER` | Deploy user with Docker permissions (e.g., `deploy`) |
| `HOST_SSH_KEY` | Ed25519 or RSA private key for passwordless SSH deployment |

When neither secret is configured, the CD pipeline builds and pushes images to GHCR and verifies the release APK build, but safely skips live host rollout until secrets are provisioned.

---

## 3. Production Environment Variables (`.env`)

For on-premise Docker Compose deployments (`docker-compose.prod.yml`), configure:

```bash
# Database
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_USER=kucet_frs
POSTGRES_PASSWORD=institutional_secure_db_password
POSTGRES_DB=kucet_frs_production

# JWT Authentication
SECRET_KEY=institutional_cryptographic_secret_minimum_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Receipt Verification
RECEIPT_SIGNING_KEY=institutional_hmac_sha256_signing_key_hex

# Vision Models
YUNET_MODEL_PATH=/app/models/face_detection_yunet_2023mar.onnx
SFACE_MODEL_PATH=/app/models/face_recognition_sface_2021dec.onnx

# Data Retention Policy
EPHEMERAL_SWEEP_RETENTION_DAYS=7
```

---

## 4. Verification & Health Monitoring

Once deployed:
1. **API Health Endpoint:** `GET /health` returns status of database connection and model artifact digests.
2. **Database Migration Status:** The `pre-deploy-migration-gate` container ensures all Alembic migrations are applied before the API accepts live traffic.
3. **Outbox Event Dispatcher:** Periodically calls `dispatch_pending_outbox_events()` to guarantee at-least-once SSE delivery across container restarts.
