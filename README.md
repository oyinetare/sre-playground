# sre-playground

School management system, demonstrating end-to-end SRE best practices with features such as SLO Dashboard, Infrastructure as Code (Terraform), comprehensive monitoring (Prometheus & Grafana), fault-tolerant architecture, messaging systems and distributed asynchronous workloads using Python, LocalStack, and AWS services.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Full Demo Guide](#full-demo-guide)
- [Access Points](#access-points)
- [Troubleshooting](#troubleshooting)
- [📊 Project Implementation Steps](#-project-implementation-steps)
  - [Architecture](#architecture)
  - [Project Structure](#project-structure)
  - [Technical Stack](#technical-stack)
  - [SRE Principles Demonstrated](#sre-principles-demonstrated)
  - [STEP 1 - Project Foundation](#step-1---project-foundation)
  - [STEP 2 - Monitoring & Basic IaC](#step-2---monitoring--basic-iac)
  - [STEP 3 - Messaging & Basic Resilience](#step-3---messaging--basic-resilience)
  - [Future Enhancements](#future-enhancements)
- [Key Commands Reference](#key-commands-reference)

---

## Features

- FastAPI-based REST API with async support
- Health check endpoints (liveness, readiness, comprehensive)
- Prometheus metrics integration
- Grafana dashboards for visualization
- PostgreSQL database with SQLAlchemy ORM
- Redis caching layer
- AWS services via LocalStack (SQS, DynamoDB)
- Circuit breaker pattern for resilience
- Rate limiting for API protection
- Structured JSON logging
- Docker containerization
- Infrastructure as Code with Terraform
- Kubernetes-ready manifests

---

## Prerequisites

- **Docker Desktop** (v20.10+): [Download](https://www.docker.com/products/docker-desktop)
- **Docker Compose** (v2.0+): Usually included with Docker Desktop
- **Terraform** (v1.0+): [Download](https://www.terraform.io/downloads)
- **Git**: [Download](https://git-scm.com/downloads)
- **AWS CLI** (for testing): `brew install awscli` or [Download](https://aws.amazon.com/cli/)
- **Python 3.10+** (optional, for local development): [Download](https://www.python.org/downloads/)

Verify installations:

```bash
docker --version
docker-compose --version
terraform --version
git --version
aws --version
```

---

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/oyinetare/sre-playground.git
cd sre-playground

# 2. Create environment file
cp .env.example .env

# 3. Start all services
docker-compose up -d --build

# 4. Wait for services to initialize
echo "⏳ Waiting for services to start..."
sleep 30

# 5. Initialize infrastructure
cd infrastructure/terraform
terraform init && terraform apply -auto-approve
cd ../..

# 6. Make scripts executable
chmod +x scripts/*.py

# 7. Verify health
curl http://localhost:8000/health
echo "✅ You should see 'healthy' status"

# 8. View API documentation
open http://localhost:8000/docs
```

---

## Full Demo Guide

After completing the Quick Start, run these tests to see all features:

```bash
# 1. Create test data
echo "📚 Creating test students..."
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/students \
    -H "Content-Type: application/json" \
    -d '{"first_name": "Student'$i'", "last_name": "Test", "grade": '$((i + 5))'}'
done

# 2. Test circuit breaker (will fail after 3 attempts)
echo -e "\n🔌 Testing circuit breaker..."
for i in {1..10}; do
  echo "Attempt $i:"
  curl http://localhost:8000/api/v1/students/STU-123/grades
  echo
  sleep 1
done

# 3. Test rate limiting (10 requests/minute limit)
echo -e "\n🚦 Testing rate limiting..."
for i in {1..15}; do
  echo -n "Request $i: "
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/api/v1/students \
    -H "Content-Type: application/json" \
    -d '{"first_name": "RateTest", "last_name": "User", "grade": 10}'
done
echo "✅ Requests 11-15 should return 429 (Rate Limit Exceeded)"

# 4. Run load test
./scripts/load_test.py

# 5. Check SQS messages
echo -e "\n📬 Checking SQS messages..."
aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://localhost:4566/000000000000/student-events \
  --max-number-of-messages 5

# 6. Run tests
echo -e "\n🧪 Running tests..."
docker exec sre-playground-app bash -c "cd /app && python -m pytest tests/unit/test_health.py -v"
```

---

## Access Points

| Service           | URL                                   | Credentials |
| ----------------- | ------------------------------------- | ----------- |
| API Documentation | http://localhost:8000/docs            | -           |
| Grafana Dashboard | http://localhost:3000                 | admin/admin |
| Prometheus        | http://localhost:9090                 | -           |
| Root Endpoint     | http://localhost:8000                 | -           |
| Health Check      | http://localhost:8000/health          | -           |
| Liveness Probe    | http://localhost:8000/health/live     | -           |
| Readiness Probe   | http://localhost:8000/health/ready    | -           |
| Metrics           | http://localhost:8000/metrics         | -           |
| Student API       | http://localhost:8000/api/v1/students | -           |

---

## Troubleshooting

### Common Issues

1. **LocalStack failing with "Device or resource busy"**

   - Remove the volume mount from docker-compose.yml under localstack service
   - Run `docker-compose down -v` and start again

2. **SQS not receiving messages**

   - LocalStack might take time to initialize. Wait 60 seconds after startup
   - Verify queue exists: `aws --endpoint-url=http://localhost:4566 sqs list-queues`

3. **Tests not found**

   ```bash
   # Use proper Python path
   docker exec sre-playground-app bash -c "cd /app && python -m pytest tests/ -v"
   ```

4. **Port conflicts**
   ```bash
   # Check ports in use
   lsof -i :8000
   lsof -i :3000
   lsof -i :9090
   ```

### Useful Commands

```bash
# View logs
docker-compose logs -f app

# Restart everything
docker-compose down -v
docker-compose up -d --build

# Check service status
docker-compose ps
```

### Cleanup

```bash
# Stop services (keeps data)
docker-compose stop

# Remove everything
docker-compose down -v
```

---

## 📊 Project Implementation Steps

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FastAPI    │────▶│ PostgreSQL  │     │    Redis    │
│   (API)     │     └─────────────┘     │   (Cache)   │
└──────┬──────┘                         └─────────────┘
       │
       ├────▶ SQS (Event Queue)
       ├────▶ DynamoDB (Audit Logs)
       └────▶ Prometheus/Grafana (Metrics)

                           ┌─────────────────┐
                           │   Client/User   │
                           └────────┬────────┘
                                    │
                           ┌────────▼────────┐
                           │  Rate Limiter   │
                           │   Middleware    │
                           └────────┬────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │         FastAPI App           │
                    │  ┌─────────────────────────┐  │
                    │  │   Health Endpoints      │  │
                    │  │ /health, /live, /ready  │  │
                    │  └─────────────────────────┘  │
                    │  ┌─────────────────────────┐  │
                    │  │   Student API           │  │
                    │  │ CRUD Operations         │  │
                    │  └──────────┬──────────────┘  │
                    └─────────────┬─────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
      ┌─────────▼────────┐ ┌──────▼──────┐ ┌──────▼──────┐
      │   PostgreSQL     │ │    Redis    │ │  Monitoring │
      │   (Students)     │ │   (Cache)   │ │ Prometheus  │
      └─────────┬────────┘ └─────────────┘ └──────┬──────┘
                │                                   │
      ┌─────────▼────────┐                ┌───────▼───────┐
      │   LocalStack     │                │    Grafana    │
      │  ┌────────────┐  │                │  Dashboards   │
      │  │    SQS     │  │                └───────────────┘
      │  │  (Events)  │  │
      │  ├────────────┤  │
      │  │  DynamoDB  │  │
      │  │  (Audit)   │  │
      │  └────────────┘  │
      └──────────────────┘

External Service Mock
      ┌──────────────────┐
      │  Grade Service   │
      │ (Circuit Breaker)│
      └──────────────────┘
```

---

### Project Structure

```
sre-playground/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── students.py
│   │   └── admin.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── metrics.py
│   │   └── rate_limits.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── student.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sqs_service.py
│   │   ├── audit_service.py
│   │   ├── cache_service.py
│   │   ├── circuit_breaker.py
│   │   └── slo_service.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── rate_limiter.py
│   └── monitoring/
│       ├── __init__.py
│       └── health.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_health.py
│   │   ├── test_students.py
│   │   ├── test_circuit_breaker.py
│   │   └── test_services.py
│   └── integration/
│       ├── test_api_flow.py
│       └── test_monitoring.py
├── infrastructure/
│   └── terraform/
│       ├── main.tf
│       └── versions.tf
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       └── provisioning/
├── k8s/
│   └── deployment.yaml
├── scripts/
│   ├── health_check.py
│   └── load_test.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── Makefile
├── .env.example
└── README.md
```

---

### Technical Stack

✅ **Python FastAPI** with async support
✅ **PostgreSQL** for relational data
✅ **DynamoDB** for audit logs
✅ **Redis** for caching
✅ **SQS** for message queuing
✅ **Prometheus + Grafana** monitoring
✅ **Terraform** infrastructure as code
✅ **Docker** containerization
✅ **Kubernetes-ready** deployment

---

### SRE Principles Demonstrated

#### 1. **Observability**

- Metrics collection with Prometheus
- Visualization with Grafana dashboards
- Structured JSON logging
- Health check endpoints

#### 2. **Reliability & Resilience**

- Circuit breakers prevent cascading failures
- Graceful degradation with fallbacks
- Health-based routing readiness
- Error budget tracking

#### 3. **Scalability**

- Stateless application design
- Horizontal scaling ready
- Redis caching layer
- Async message processing

#### 4. **Automation**

- Infrastructure as Code (Terraform)
- Automated testing suite
- CI/CD ready structure
- Self-healing capabilities

#### 5. **Security**

- Rate limiting protection
- Comprehensive audit logging
- Non-root containers
- Environment-based secrets

---

### STEP 1 - Project Foundation

#### Objectives

- Set up project structure and Git repository
- Create Python FastAPI application with health endpoints
- Configure PostgreSQL database with SQLAlchemy
- Implement Docker containerization
- Set up LocalStack for AWS services

#### Implementation Checklist

- [ ] Project structure creation
- [ ] Virtual environment and dependencies
- [ ] Basic FastAPI application with:
  - [ ] Configuration management (pydantic-settings)
  - [ ] Health check endpoints (`/health`, `/health/live`, `/health/ready`)
  - [ ] Prometheus metrics endpoint (`/metrics`)
  - [ ] Structured JSON logging
  - [ ] Student CRUD endpoints
- [ ] PostgreSQL integration with SQLAlchemy
- [ ] Docker setup with health checks
- [ ] Docker Compose with PostgreSQL and LocalStack
- [ ] Testing scripts for verification

#### Validation

- Health endpoint returns proper status
- Database connection works
- Student CRUD operations functional
- Docker containers communicate properly

---

### STEP 2 - Monitoring & Basic IaC

#### Objectives

- Add Prometheus and Grafana monitoring stack
- Implement comprehensive application metrics
- Create Terraform infrastructure setup
- Add database migrations with Alembic

#### Implementation Checklist

- [ ] Prometheus configuration and setup
- [ ] Grafana with auto-provisioning
- [ ] Enhanced metrics:
  - [ ] Request count and duration
  - [ ] Active connections gauge
  - [ ] Business metrics (students created)
- [ ] Basic Terraform configuration:
  - [ ] AWS provider for LocalStack
  - [ ] SQS queue creation
  - [ ] DynamoDB table setup
- [ ] Database migrations with Alembic
- [ ] Load testing script
- [ ] Grafana dashboards creation

#### Validation

- Prometheus scrapes metrics successfully
- Grafana displays real-time data
- Terraform creates resources in LocalStack
- Load tests generate visible metrics

---

### STEP 3 - Messaging & Basic Resilience

#### Objectives

- Implement async messaging with SQS
- Add resilience patterns (circuit breaker)
- Set up audit logging with DynamoDB
- Implement caching and rate limiting

#### Implementation Checklist

- [ ] SQS integration:
  - [ ] Message publishing on student creation
  - [ ] Queue initialization in LocalStack
- [ ] DynamoDB audit logging:
  - [ ] Audit service implementation
  - [ ] Automatic table creation
- [ ] Circuit breaker pattern:
  - [ ] Three states (CLOSED, OPEN, HALF_OPEN)
  - [ ] Mock external service for testing
- [ ] Redis caching:
  - [ ] Cache service implementation
  - [ ] Student data caching
- [ ] Rate limiting:
  - [ ] Redis-backed token bucket
  - [ ] Configurable limits per endpoint
- [ ] SLO monitoring and dashboards
- [ ] Graceful shutdown handling
- [ ] Unit and integration tests

#### Validation

- Messages appear in SQS queue
- Circuit breaker opens after failures
- Rate limiting returns 429 after threshold
- Cache improves response times

---

### Future Enhancements

- **AWS API Gateway**: Request transformation, API keys, usage plans
- **Lambda Functions**: Event processing, scheduled tasks
- **Step Functions**: Complex workflow orchestration
- **X-Ray**: Distributed tracing implementation
- **Service Mesh**: Istio/Linkerd for traffic management
- **Multi-Region**: Global distribution setup
- **Chaos Engineering**: Failure injection testing
- **Correlation IDs**: Request tracing across services
- **Feature Flags**: Progressive feature rollout
- **Authentication**: JWT/OAuth implementation
- **CI/CD Pipeline**: Automated deployment
- **Advanced Terraform Modules**: Multi-environment setup

---

## Key Commands Reference

### Docker Commands

```bash
docker-compose up -d              # Start services
docker-compose logs -f app        # View logs
docker-compose down -v            # Clean restart
docker-compose ps                 # Check status
docker exec -it sre-playground-app bash  # Enter container
```

### Terraform Commands

```bash
cd infrastructure/terraform
terraform init                    # Initialize
terraform plan                    # Preview changes
terraform apply -auto-approve     # Apply changes
terraform destroy -auto-approve   # Cleanup
```

### Testing Commands

```bash
# Unit tests
docker exec sre-playground-app bash -c "cd /app && python -m pytest tests/unit -v"

# Integration tests
docker exec sre-playground-app bash -c "cd /app && python -m pytest tests/integration -v"

# Coverage report
docker exec sre-playground-app bash -c "cd /app && python -m pytest --cov=app --cov-report=html"
```

### Monitoring Access

```bash
open http://localhost:8000/docs   # API documentation
open http://localhost:3000        # Grafana dashboard
open http://localhost:9090        # Prometheus
```

### Create Test Data

```bash
# Single student
curl -X POST http://localhost:8000/api/v1/students \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Test", "last_name": "Student", "grade": 10}'

# Multiple students
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/students \
    -H "Content-Type: application/json" \
    -d '{"first_name": "Test'$i'", "last_name": "Student", "grade": '$((i % 12 + 1))'}'
done
```

### Environment File (.env.example)

```env
ENVIRONMENT=development
DATABASE_URL=postgresql://admin:password@postgres:5432/sredb
AWS_ENDPOINT_URL=http://localstack:4566
REDIS_URL=redis://redis:6379
ENABLE_SQS=true
ENABLE_DYNAMODB=true
```
