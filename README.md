# Rwanda Digital Health Backend

A production-ready national digital health infrastructure built with Django, PostgreSQL, Redis, and Celery. Connects patients, doctors, laboratories, pharmacies, and public health authorities through a secure, scalable REST API.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Local Development Setup](#local-development-setup)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Authentication](#authentication)
- [User Roles & Permissions](#user-roles--permissions)
- [Background Tasks](#background-tasks)
- [CI/CD Pipeline](#cicd-pipeline)
- [Production Deployment](#production-deployment)
- [Running Tests](#running-tests)
- [All 8 Requirements Checklist](#all-8-requirements-checklist)

---

## Overview

This system is a centralized digital health platform for Rwanda that enables:

- Patient registration with unique Rwanda health IDs (format: `RW-YYYY-XXXXXXXX`)
- Electronic Health Records with SOAP clinical notes, diagnoses, and prescriptions
- Appointment booking with automatic conflict detection and queue management
- Laboratory test requests, result uploads, and critical result alerts
- Pharmacy inventory management and prescription dispensing
- Public health analytics with real-time outbreak detection
- Emergency services with GPS-based hospital routing
- Background notifications via Celery — emails, reminders, and alerts

---

## Architecture

```
Clients (Patients, Doctors, Pharmacists, Lab Techs, Admins)
                          |
              API Gateway (Django REST Framework)
              JWT Auth | RBAC | Pagination | Filtering
                          |
    ┌─────────────────────┼──────────────────────┐
    │                     │                      │
 Django Apps           Background            Infrastructure
 ─────────────         ──────────────        ──────────────
 users/                Celery Worker         PostgreSQL 15
 patients/             Celery Beat           Redis 7
 appointments/         Scheduled tasks       Docker / Nginx
 records/
 pharmacy/
 labs/
 analytics/
 emergency/
 common/
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 6 + Django REST Framework |
| Database | PostgreSQL 15 |
| Cache & broker | Redis 7 |
| Background tasks | Celery 5 + django-celery-beat |
| Authentication | JWT via djangorestframework-simplejwt |
| Containerization | Docker + Docker Compose |
| Production server | Gunicorn + Nginx |
| Environment | python-decouple |

---

## Project Structure

```
rwanda-health-backend/
├── health/                     # Project config (settings, urls, celery)
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── users/                      # Custom user model, JWT auth, RBAC
├── patients/                   # Patient profiles, health IDs, medical history
├── appointments/               # Booking, conflict detection, queue management
├── records/                    # EHR — clinical notes, diagnoses, prescriptions
├── pharmacy/                   # Medication inventory, dispensing
├── labs/                       # Lab test requests, result uploads
├── analytics/                  # Disease reporting, outbreak detection, dashboards
├── emergency/                  # Hospital registry, emergency requests, GPS routing
├── common/                     # Shared utilities, email helpers
├── Dockerfile
├── docker-compose.yml          # Development
├── docker-compose.prod.yml     # Production (Gunicorn + Nginx)
├── nginx.conf
├── entrypoint.sh
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Prerequisites

- Docker Desktop installed and running
- Git

That is all you need. PostgreSQL and Redis run inside Docker — nothing to install locally.

---

## Quick Start with Docker

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/rwanda-health-backend.git
cd rwanda-health-backend
```

**2. Create your environment file**

```bash
cp .env.example .env
```

Open `.env` and set your values — especially `SECRET_KEY` and `DB_PASSWORD`.

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**3. Build and start all containers**

```bash
docker-compose up --build
```

This starts 5 containers:
- `rwanda_health_db` — PostgreSQL 15
- `rwanda_health_redis` — Redis 7
- `rwanda_health_web` — Django development server
- `rwanda_health_celery` — Celery worker
- `rwanda_health_beat` — Celery beat scheduler

Migrations run automatically on first start.

**4. Create a superuser**

```bash
docker-compose exec web python manage.py createsuperuser
```

**5. Verify everything is running**

```
http://localhost:8000/admin/          Django admin
http://localhost:8000/api/auth/       Auth endpoints
http://localhost:8000/api/patients/   Patient endpoints
```

---

## Local Development Setup

If you prefer to run without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up .env with DB_HOST=localhost and your local PostgreSQL port
cp .env.example .env

# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE rwanda_health_db;"

# Run migrations
python manage.py migrate

# Start Django
python manage.py runserver

# In a second terminal — start Celery worker
celery -A health worker --loglevel=info --pool=solo

# In a third terminal — start Celery beat
celery -A health beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

> **Note:** On Windows, PostgreSQL may run on port 5000 instead of 5432 depending on your installation. Check with `netstat -ano | findstr :5432` and update `DB_PORT` in your `.env` accordingly.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all values.

```env
# Django core
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=rwanda_health_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=db                  # Use 'db' for Docker, 'localhost' for local
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email (console for dev, SMTP for production)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key — generate a new one for production |
| `DEBUG` | Yes | Set to `False` in production |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `DB_HOST` | Yes | `db` in Docker, `localhost` in local dev |
| `REDIS_URL` | Yes | Redis connection URL |

---

## API Reference

All endpoints are prefixed with `/api/`.

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/auth/register/` | Register new user | Public |
| POST | `/api/auth/login/` | Login, get JWT tokens | Public |
| POST | `/api/auth/logout/` | Blacklist refresh token | Required |
| POST | `/api/auth/token/refresh/` | Refresh access token | Required |
| GET/PATCH | `/api/auth/me/` | Get or update own profile | Required |
| POST | `/api/auth/change-password/` | Change password | Required |
| GET | `/api/auth/users/` | List all users | Admin only |

### Patients

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/patients/profile/` | Create patient profile | Patient |
| GET/PATCH | `/api/patients/profile/me/` | View or update own profile | Patient |
| GET | `/api/patients/` | List all patients | Doctor, Admin |
| GET | `/api/patients/<id>/` | Get patient detail | Doctor, Admin |
| POST | `/api/patients/<id>/history/add/` | Add medical history entry | Doctor, Admin |
| GET | `/api/patients/<id>/history/` | List medical history | Doctor, Admin, Patient (own) |

### Appointments

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/appointments/book/` | Book appointment | Patient |
| GET | `/api/appointments/` | List appointments (role-filtered) | All |
| GET | `/api/appointments/<id>/` | Get appointment detail | Owner, Doctor, Admin |
| PATCH | `/api/appointments/<id>/status/` | Update status, add notes | Doctor, Admin |
| PATCH | `/api/appointments/<id>/cancel/` | Cancel appointment | Patient |
| GET | `/api/appointments/queue/today/` | Today's queue | Doctor, Admin |

### Electronic Health Records

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/records/notes/` | Create clinical note | Doctor |
| GET | `/api/records/notes/all/` | List notes (role-filtered) | All |
| GET/PATCH | `/api/records/notes/<id>/` | Get or update note | Doctor, Admin |
| GET | `/api/records/patient/<id>/notes/` | Patient's full notes | Doctor, Admin, Patient (own) |
| GET | `/api/records/patient/<id>/prescriptions/` | Patient's prescriptions | All (own for patient) |
| GET | `/api/records/patient/<id>/diagnoses/` | Patient's diagnoses | All (own for patient) |

### Laboratory

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/labs/request/` | Request a lab test | Doctor, Admin |
| GET | `/api/labs/` | List lab tests (role-filtered) | All |
| GET/PATCH | `/api/labs/<id>/` | Get or update lab test | All |
| POST | `/api/labs/<id>/result/` | Upload test result | Lab Tech |
| GET | `/api/labs/patient/<id>/` | All tests for a patient | Doctor, Admin, Patient (own) |

### Pharmacy

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/pharmacy/medications/` | List available medications | Doctor, Admin |
| POST | `/api/pharmacy/medications/add/` | Add medication to inventory | Pharmacist |
| GET/PATCH | `/api/pharmacy/medications/<id>/` | Get or update medication | Pharmacist |
| GET | `/api/pharmacy/medications/low-stock/` | Low stock alert list | Pharmacist |
| POST | `/api/pharmacy/dispense/` | Dispense prescription | Pharmacist |
| GET | `/api/pharmacy/dispensings/` | List dispensing records | Pharmacist, Patient (own) |
| GET | `/api/pharmacy/queue/<health_id>/` | Active prescriptions by health ID | Pharmacist |

### Analytics

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/analytics/disease-reports/` | Submit disease report | Doctor, Admin |
| GET | `/api/analytics/disease-reports/all/` | List all disease reports | Doctor, Admin |
| GET | `/api/analytics/outbreaks/` | Active outbreak alerts | All authenticated |
| GET | `/api/analytics/dashboard/` | Full policymaker dashboard | Doctor, Admin |
| GET | `/api/analytics/regional/<district>/` | Regional health breakdown | Doctor, Admin |
| GET | `/api/analytics/metrics/` | Raw health metrics | Admin |

### Emergency

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/emergency/hospitals/` | List all hospitals | Public |
| POST | `/api/emergency/hospitals/add/` | Register hospital | Admin |
| GET/PATCH | `/api/emergency/hospitals/<id>/` | Hospital detail | Admin |
| GET | `/api/emergency/hospitals/nearest/<district>/` | Nearest emergency facility | Public |
| POST | `/api/emergency/request/` | Submit emergency request | Public (no auth needed) |
| GET | `/api/emergency/requests/` | List all requests | Doctor, Admin |
| GET | `/api/emergency/requests/active/` | Active emergencies only | Doctor, Admin |
| PATCH | `/api/emergency/requests/<id>/status/` | Update emergency status | Doctor, Admin |

---

## Authentication

This project uses JWT authentication via `djangorestframework-simplejwt`.

**Register and login flow:**

```bash
# 1. Register
POST /api/auth/register/
{
  "email": "doctor@health.rw",
  "username": "doctor1",
  "first_name": "Jean",
  "last_name": "Mutabazi",
  "password": "StrongPass123!",
  "password2": "StrongPass123!",
  "role": "doctor"
}

# Response includes tokens:
{
  "user": { ... },
  "tokens": {
    "access": "eyJhbGci...",   # Valid 60 minutes
    "refresh": "eyJhbGci..."   # Valid 7 days
  }
}

# 2. Use the access token on all protected endpoints
GET /api/patients/
Authorization: Bearer eyJhbGci...

# 3. Refresh the access token before it expires
POST /api/auth/token/refresh/
{ "refresh": "eyJhbGci..." }

# 4. Logout — blacklists the refresh token
POST /api/auth/logout/
Authorization: Bearer eyJhbGci...
{ "refresh": "eyJhbGci..." }
```

---

## User Roles & Permissions

| Role | Key Permissions |
|---|---|
| `admin` | Full access to everything |
| `doctor` | Create notes, request labs, view all patients, manage appointments |
| `patient` | View own records, book appointments, view own prescriptions |
| `pharmacist` | Manage inventory, dispense prescriptions, view low stock |
| `lab_tech` | View assigned tests, upload results |

Permissions are enforced at two levels — view level (who can access the endpoint) and object level (who can access specific records). A patient can never access another patient's records.

---

## Background Tasks

All tasks run via Celery workers and are never blocking to the API.

| Task | Trigger | Schedule |
|---|---|---|
| Appointment confirmation email | Doctor confirms appointment | Immediate |
| Appointment reminder | — | Every hour (checks for tomorrow's appointments) |
| Daily digest to doctors | — | Every day at 07:00 AM Kigali time |
| Lab result notification | Lab tech uploads result | Immediate |
| Critical result urgent alert | Result status is `critical` | Immediate |
| Low stock pharmacy alert | — | Every day at 08:00 AM |
| Auto-expire prescriptions | — | Every day at 01:00 AM |
| Cancel stale pending appointments | — | Every day at 00:30 AM |
| Compute daily health metrics | — | Every day at midnight |
| Outbreak detection | — | Every 6 hours |

All tasks retry up to 3 times on failure with a 60-second delay between retries.

---

## CI/CD Pipeline

This project includes a GitHub Actions CI/CD pipeline that runs on every push and pull request.

### Pipeline file: `.github/workflows/ci.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: rwanda_health_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run migrations
        env:
          SECRET_KEY: ci-test-secret-key-not-for-production
          DEBUG: True
          DB_NAME: rwanda_health_test
          DB_USER: postgres
          DB_PASSWORD: postgres
          DB_HOST: localhost
          DB_PORT: 5432
          REDIS_URL: redis://localhost:6379/0
          CELERY_BROKER_URL: redis://localhost:6379/0
          CELERY_RESULT_BACKEND: redis://localhost:6379/0
          EMAIL_BACKEND: django.core.mail.backends.console.EmailBackend
        run: python manage.py migrate

      - name: Run system checks
        env:
          SECRET_KEY: ci-test-secret-key-not-for-production
          DEBUG: True
          DB_NAME: rwanda_health_test
          DB_USER: postgres
          DB_PASSWORD: postgres
          DB_HOST: localhost
          DB_PORT: 5432
          REDIS_URL: redis://localhost:6379/0
          CELERY_BROKER_URL: redis://localhost:6379/0
          CELERY_RESULT_BACKEND: redis://localhost:6379/0
          EMAIL_BACKEND: django.core.mail.backends.console.EmailBackend
        run: python manage.py check

      - name: Run tests
        env:
          SECRET_KEY: ci-test-secret-key-not-for-production
          DEBUG: True
          DB_NAME: rwanda_health_test
          DB_USER: postgres
          DB_PASSWORD: postgres
          DB_HOST: localhost
          DB_PORT: 5432
          REDIS_URL: redis://localhost:6379/0
          CELERY_BROKER_URL: redis://localhost:6379/0
          CELERY_RESULT_BACKEND: redis://localhost:6379/0
          EMAIL_BACKEND: django.core.mail.backends.console.EmailBackend
        run: python manage.py test --verbosity=2

  docker:
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t rwanda-health-backend .

      - name: Verify image builds successfully
        run: docker image ls rwanda-health-backend
```

### Setting up CI/CD

**1. Create the workflow directory and file:**

```bash
mkdir -p .github/workflows
```

Then create `.github/workflows/ci.yml` with the content above.

**2. Push to GitHub:**

```bash
git add .github/
git commit -m "Add CI/CD pipeline"
git push
```

**3. Watch it run:**

Go to your GitHub repository → click the **Actions** tab → you will see the pipeline running automatically on every push.

### What the pipeline does

On every push to `main` or `develop`:

- Spins up PostgreSQL 15 and Redis 7 as service containers
- Installs all Python dependencies from `requirements.txt`
- Runs `python manage.py migrate` — verifies all migrations apply cleanly
- Runs `python manage.py check` — verifies Django system checks pass
- Runs the full test suite
- Builds the Docker image — verifies the `Dockerfile` is valid

If any step fails, the push is flagged and you are notified before broken code reaches production.

---

## Production Deployment

Use `docker-compose.prod.yml` which runs Gunicorn + Nginx instead of Django's development server.

**1. Set up production environment file:**

```bash
cp .env.example .env.prod
```

Edit `.env.prod`:
```env
SECRET_KEY=generate-a-strong-key-for-production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_PASSWORD=strong-production-password
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**2. Start production stack:**

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

This starts: PostgreSQL + Redis + Django/Gunicorn (4 workers) + Nginx + Celery worker + Celery beat

**3. Create superuser in production:**

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

**4. Access the system:**

```
http://yourdomain.com/admin/
http://yourdomain.com/api/
```

---

## Running Tests

```bash
# With Docker
docker-compose exec web python manage.py test

# Locally
python manage.py test

# Specific app
python manage.py test users
python manage.py test patients
python manage.py test appointments
```

---

## Useful Docker Commands

```bash
# View all running containers
docker-compose ps

# View logs from all containers
docker-compose logs -f

# View logs from one container
docker-compose logs -f web
docker-compose logs -f celery_worker

# Run any manage.py command
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py createsuperuser

# Stop all containers
docker-compose down

# Stop and delete all data (full reset)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build
```

---

## All 8 Requirements Checklist

| Requirement | Implementation |
|---|---|
| **Modular Django apps** | 9 independent apps — users, patients, appointments, records, pharmacy, labs, analytics, emergency, common |
| **DRF API layer** | `djangorestframework` with `PageNumberPagination`, `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter` configured globally |
| **Optimized queries** | Every list view uses `select_related` and `prefetch_related` — zero N+1 queries |
| **JWT + RBAC** | `djangorestframework-simplejwt` with 5 roles, token blacklisting on logout, object-level permissions |
| **Background processing** | Celery + Redis — 10 task types across 4 apps, all retrying on failure |
| **Caching** | `django-redis` as cache backend, sessions stored in Redis |
| **Docker + docker-compose** | `Dockerfile`, `docker-compose.yml` (dev), `docker-compose.prod.yml` (Gunicorn + Nginx), health checks |
| **Environment management** | `python-decouple` reads all secrets from `.env` — zero hardcoded credentials |

---

## Author

**Parfait Ndizihiwe**
Django Bootcamp Capstone Project — 2026
Rwanda Digital Health Backend
