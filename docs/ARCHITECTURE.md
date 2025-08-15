# HappyRobot FDE System Architecture

## Executive Summary
The HappyRobot FDE platform implements a hexagonal architecture pattern for the backend services, ensuring clean separation of concerns, testability, and maintainability. The system is designed for cloud-native deployment on AWS using ECS Fargate, RDS PostgreSQL, and Application Load Balancer with HTTPS termination.

## Architecture Principles

### 1. Hexagonal Architecture (Ports & Adapters)
- **Domain-Driven Design**: Business logic isolated in the core domain
- **Dependency Inversion**: Core depends on abstractions, not implementations
- **Testability**: Easy to test with mock adapters
- **Flexibility**: Swap implementations without changing business logic

### 2. Cloud-Native Design
- **Containerized**: All services run in Docker containers
- **Stateless**: Application servers hold no state
- **Horizontally Scalable**: Add more containers to handle load
- **12-Factor App**: Following cloud-native best practices

### 3. Security First
- **Zero Trust**: Authenticate every request
- **Defense in Depth**: Multiple security layers
- **Least Privilege**: Minimal permissions for each component
- **Encryption**: Data encrypted in transit and at rest

---

## System Components

### Component Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    CloudFront CDN     │
                    │   (Static Assets)     │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Route 53 DNS       │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Application Load     │
                    │  Balancer (ALB)       │
                    │  - HTTPS (ACM Cert)  │
                    │  - Path-based routing│
                    └───────────────────────┘
                        │               │
                        ▼               ▼
            ┌───────────────────┐ ┌───────────────────┐
            │   Target Group 1  │ │   Target Group 2  │
            └───────────────────┘ └───────────────────┘
                        │               │
                        ▼               ▼
            ┌───────────────────┐ ┌───────────────────┐
            │  ECS Service API  │ │ ECS Service Web   │
            │  (Fargate Tasks)  │ │ (Fargate Tasks)   │
            └───────────────────┘ └───────────────────┘
                        │               │
            ┌───────────────────────────────────────┐
            │          VPC (10.0.0.0/16)            │
            │  ┌─────────────────────────────────┐  │
            │  │   Private Subnets               │  │
            │  │   - 10.0.1.0/24 (AZ-1)         │  │
            │  │   - 10.0.2.0/24 (AZ-2)         │  │
            │  └─────────────────────────────────┘  │
            │  ┌─────────────────────────────────┐  │
            │  │   Public Subnets                │  │
            │  │   - 10.0.101.0/24 (AZ-1)       │  │
            │  │   - 10.0.102.0/24 (AZ-2)       │  │
            │  └─────────────────────────────────┘  │
            └───────────────────────────────────────┘
                                │
                    ┌───────────────────────┐
                    │   RDS PostgreSQL      │
                    │   - Multi-AZ          │
                    │   - Encrypted         │
                    │   - Automated Backups │
                    └───────────────────────┘
                                │
                    ┌───────────────────────┐
                    │   AWS Secrets Manager │
                    │   - API Keys          │
                    │   - DB Credentials    │
                    └───────────────────────┘
```

### Layer Architecture
```
┌──────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Next.js Frontend (React + TypeScript)         │ │
│  │  - Server-side rendering                               │ │
│  │  - React Query for data fetching                       │ │
│  │  - Shadcn/UI components                                │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     Interface Layer                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              FastAPI REST API (v1)                     │ │
│  │  - OpenAPI documentation                               │ │
│  │  - Request validation (Pydantic)                       │ │
│  │  - API key authentication                              │ │
│  │  - Rate limiting                                       │ │
│  │  - CORS handling                                       │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Use Cases                           │ │
│  │  - VerifyCarrierUseCase                               │ │
│  │  - SearchLoadsUseCase                                 │ │
│  │  - EvaluateNegotiationUseCase                         │ │
│  │  - HandoffCallUseCase                                 │ │
│  │  - FinalizeCallUseCase                                │ │
│  │  - GetMetricsUseCase                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │               Application Services                     │ │
│  │  - NegotiationService                                 │ │
│  │  - CarrierEligibilityService                          │ │
│  │  - LoadMatchingService                                │ │
│  │  - MetricsAggregationService                          │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                     Entities                           │ │
│  │  - Carrier                                             │ │
│  │  - Load                                                │ │
│  │  - Call                                                │ │
│  │  - Negotiation                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  Value Objects                         │ │
│  │  - MCNumber                                            │ │
│  │  - Rate                                                │ │
│  │  - Location                                            │ │
│  │  - DateRange                                           │ │
│  │  - EquipmentType                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                 Domain Services                        │ │
│  │  - PricingStrategy                                     │ │
│  │  - EligibilityRules                                    │ │
│  │  - NegotiationRules                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                Domain Exceptions                       │ │
│  │  - InvalidMCNumberException                            │ │
│  │  - NegotiationLimitExceededException                   │ │
│  │  - LoadNotAvailableException                           │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                       Ports Layer                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                Repository Interfaces                   │ │
│  │  - ICarrierRepository                                  │ │
│  │  - ILoadRepository                                     │ │
│  │  - ICallRepository                                     │ │
│  │  - INegotiationRepository                              │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                 Service Interfaces                     │ │
│  │  - IFMCSAService                                       │ │
│  │  - INotificationService                                │ │
│  │  - ISentimentAnalysisService                           │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Database Adapters (PostgreSQL)            │ │
│  │  - PostgresCarrierRepository                           │ │
│  │  - PostgresLoadRepository                              │ │
│  │  - PostgresCallRepository                              │ │
│  │  - PostgresNegotiationRepository                       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                 External Services                      │ │
│  │  - FMCSAApiService                                     │ │
│  │  - TwilioNotificationService                           │ │
│  │  - AWSComprehendSentimentService                       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    ORM Models                          │ │
│  │  - SQLAlchemy Models                                   │ │
│  │  - Alembic Migrations                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Carrier Verification Flow
```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│HappyRobot│     │  FastAPI │     │  UseCase │     │   FMCSA  │
│  Agent   │     │ Endpoint │     │  Layer   │     │  Service │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                 │                 │                 │
     │ POST /verify    │                 │                 │
     │ {mc_number}     │                 │                 │
     ├────────────────►│                 │                 │
     │                 │                 │                 │
     │                 │ Validate Request│                 │
     │                 ├────────────────►│                 │
     │                 │                 │                 │
     │                 │                 │ Check FMCSA API│
     │                 │                 ├────────────────►│
     │                 │                 │                 │
     │                 │                 │◄────────────────┤
     │                 │                 │ Carrier Data    │
     │                 │                 │                 │
     │                 │                 ├──┐              │
     │                 │                 │  │ Apply        │
     │                 │                 │  │ Eligibility  │
     │                 │                 │  │ Rules        │
     │                 │                 │◄─┘              │
     │                 │                 │                 │
     │                 │                 ├──┐              │
     │                 │                 │  │ Store in     │
     │                 │                 │  │ Database     │
     │                 │                 │◄─┘              │
     │                 │                 │                 │
     │                 │◄────────────────┤                 │
     │                 │ Eligibility     │                 │
     │                 │                 │                 │
     │◄────────────────┤                 │                 │
     │ Response        │                 │                 │
     │                 │                 │                 │
```

### 2. Load Search and Matching Flow
```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│HappyRobot│     │  FastAPI │     │  UseCase │     │PostgreSQL│
│  Agent   │     │ Endpoint │     │  Layer   │     │ Database │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                 │                 │                 │
     │ POST /search    │                 │                 │
     │ {criteria}      │                 │                 │
     ├────────────────►│                 │                 │
     │                 │                 │                 │
     │                 │ Parse Criteria  │                 │
     │                 ├────────────────►│                 │
     │                 │                 │                 │
     │                 │                 │ Build Query    │
     │                 │                 ├────────────────►│
     │                 │                 │                 │
     │                 │                 │◄────────────────┤
     │                 │                 │ Load Results    │
     │                 │                 │                 │
     │                 │                 ├──┐              │
     │                 │                 │  │ Apply        │
     │                 │                 │  │ Ranking      │
     │                 │                 │  │ Algorithm    │
     │                 │                 │◄─┘              │
     │                 │                 │                 │
     │                 │                 ├──┐              │
     │                 │                 │  │ Filter by    │
     │                 │                 │  │ Business     │
     │                 │                 │  │ Rules        │
     │                 │                 │◄─┘              │
     │                 │                 │                 │
     │                 │◄────────────────┤                 │
     │                 │ Matched Loads   │                 │
     │                 │                 │                 │
     │◄────────────────┤                 │                 │
     │ Load Options    │                 │                 │
     │                 │                 │                 │
```

### 3. Negotiation State Machine
```
                    ┌─────────────┐
                    │   START     │
                    └─────┬───────┘
                          │
                          ▼
                    ┌─────────────┐
                    │  ROUND 1    │
                    │  Carrier    │
                    │   Offer     │
                    └─────┬───────┘
                          │
                ┌─────────┴──────────┐
                │                    │
                ▼                    ▼
          ┌──────────┐        ┌──────────┐
          │ ACCEPTED │        │ EVALUATE │
          └──────────┘        └────┬─────┘
                                   │
                     ┌─────────────┴──────────┐
                     │                        │
                     ▼                        ▼
              ┌──────────┐            ┌──────────┐
              │ REJECTED │            │ COUNTER  │
              └──────────┘            │  OFFER   │
                                      └────┬─────┘
                                           │
                                           ▼
                                     ┌─────────────┐
                                     │  ROUND 2    │
                                     │  Carrier    │
                                     │  Response   │
                                     └─────┬───────┘
                                           │
                                 ┌─────────┴──────────┐
                                 │                    │
                                 ▼                    ▼
                           ┌──────────┐        ┌──────────┐
                           │ ACCEPTED │        │ EVALUATE │
                           └──────────┘        └────┬─────┘
                                                    │
                                      ┌─────────────┴──────────┐
                                      │                        │
                                      ▼                        ▼
                               ┌──────────┐            ┌──────────┐
                               │ REJECTED │            │ COUNTER  │
                               └──────────┘            │  OFFER   │
                                                       └────┬─────┘
                                                            │
                                                            ▼
                                                      ┌─────────────┐
                                                      │  ROUND 3    │
                                                      │   (FINAL)   │
                                                      └─────┬───────┘
                                                            │
                                                  ┌─────────┴──────────┐
                                                  │                    │
                                                  ▼                    ▼
                                            ┌──────────┐        ┌──────────┐
                                            │ ACCEPTED │        │ REJECTED │
                                            └──────────┘        └──────────┘
```

### 4. Call Handoff Process
```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│HappyRobot│     │  FastAPI │     │  UseCase │     │Sales Rep │
│  Agent   │     │ Endpoint │     │  Layer   │     │  System  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                 │                 │                 │
     │ POST /handoff   │                 │                 │
     │ {context}       │                 │                 │
     ├────────────────►│                 │                 │
     │                 │                 │                 │
     │                 │ Validate Deal   │                 │
     │                 ├────────────────►│                 │
     │                 │                 │                 │
     │                 │                 ├──┐              │
     │                 │                 │  │ Generate     │
     │                 │                 │  │ Summary      │
     │                 │                 │◄─┘              │
     │                 │                 │                 │
     │                 │                 │ Find Available │
     │                 │                 │ Rep           │
     │                 │                 ├────────────────►│
     │                 │                 │                 │
     │                 │                 │◄────────────────┤
     │                 │                 │ Rep Assignment  │
     │                 │                 │                 │
     │                 │                 ├──┐              │
     │                 │                 │  │ Create       │
     │                 │                 │  │ Transfer     │
     │                 │                 │  │ Token        │
     │                 │                 │◄─┘              │
     │                 │                 │                 │
     │                 │◄────────────────┤                 │
     │                 │ Transfer Info   │                 │
     │                 │                 │                 │
     │◄────────────────┤                 │                 │
     │ Bridge Details  │                 │                 │
     │                 │                 │                 │
```

---

## Security Architecture

### Authentication & Authorization
```
┌────────────────────────────────────────────────────────────┐
│                     API Gateway (ALB)                      │
│  - TLS 1.3 termination                                     │
│  - WAF rules                                               │
│  - DDoS protection                                         │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                  API Key Middleware                        │
│  - Header extraction (X-API-Key or Authorization)         │
│  - Key validation against hash                             │
│  - Rate limiting per key                                   │
│  - Scope verification                                      │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                    Request Context                         │
│  - Inject authenticated client info                        │
│  - Add request ID for tracing                              │
│  - Set audit context                                       │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                   Business Logic                           │
│  - Domain validation                                       │
│  - Business rule enforcement                               │
│  - Data access control                                     │
└────────────────────────────────────────────────────────────┘
```

### Data Security Layers
1. **Network Security**
   - VPC isolation with private subnets
   - Security groups with least privilege
   - NACLs for subnet-level control
   - VPC Flow Logs for monitoring

2. **Application Security**
   - Input validation (Pydantic)
   - SQL injection prevention (SQLAlchemy ORM)
   - XSS protection (template escaping)
   - CSRF tokens for state-changing operations

3. **Data Security**
   - Encryption at rest (RDS encryption)
   - Encryption in transit (TLS 1.3)
   - Secrets management (AWS Secrets Manager)
   - PII masking in logs

4. **Audit & Compliance**
   - Comprehensive audit logging
   - CloudTrail for AWS API calls
   - Application-level audit trail
   - GDPR compliance considerations

---

## Integration Architecture

### HappyRobot Platform Integration
```
┌─────────────────────────────────────────────────────────────┐
│                   HappyRobot Platform                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Voice Agent                        │   │
│  │  - Speech recognition                               │   │
│  │  - Natural language understanding                   │   │
│  │  - Conversation management                          │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                       │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │              Web Call Triggers                      │   │
│  │  - HTTP POST actions                                │   │
│  │  - Response parsing                                 │   │
│  │  - Conditional branching                            │   │
│  └──────────────────┬──────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                    HappyRobot FDE API                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Webhook Endpoints                   │   │
│  │  - /api/v1/fmcsa/verify                            │   │
│  │  - /api/v1/loads/search                            │   │
│  │  - /api/v1/negotiations/evaluate                   │   │
│  │  - /api/v1/calls/handoff                           │   │
│  │  - /api/v1/calls/finalize                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### External Service Integrations
1. **FMCSA API**
   - REST API for carrier verification
   - Cached responses for performance
   - Fallback to manual verification

2. **AWS Services**
   - Secrets Manager: Credential storage
   - CloudWatch: Logging and metrics
   - S3: Call recording storage (future)
   - Comprehend: Sentiment analysis (future)

3. **Communication Services (Future)**
   - Twilio: SMS notifications
   - SendGrid: Email confirmations
   - Slack: Internal notifications

---

## Deployment Architecture

### AWS Infrastructure
```
┌──────────────────────────────────────────────────────────┐
│                     AWS Account                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │                  Region: us-east-1                 │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │              ECS Cluster                     │  │  │
│  │  │  ┌────────────────────────────────────────┐  │  │  │
│  │  │  │         API Service (Fargate)          │  │  │  │
│  │  │  │  - Task Definition                     │  │  │  │
│  │  │  │  - Auto-scaling (2-10 tasks)           │  │  │  │
│  │  │  │  - Health checks                       │  │  │  │
│  │  │  └────────────────────────────────────────┘  │  │  │
│  │  │  ┌────────────────────────────────────────┐  │  │  │
│  │  │  │         Web Service (Fargate)          │  │  │  │
│  │  │  │  - Task Definition                     │  │  │  │
│  │  │  │  - Auto-scaling (1-5 tasks)            │  │  │  │
│  │  │  │  - Health checks                       │  │  │  │
│  │  │  └────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │           RDS PostgreSQL                     │  │  │
│  │  │  - db.t3.medium (burstable)                  │  │  │
│  │  │  - Multi-AZ deployment                       │  │  │
│  │  │  - Automated backups (7 days)                │  │  │
│  │  │  - Encrypted storage                         │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │              ECR Repositories                │  │  │
│  │  │  - happyrobot-api:latest                     │  │  │
│  │  │  - happyrobot-web:latest                     │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline
```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  GitHub  │────►│  GitHub  │────►│   Build  │────►│  Deploy  │
│  Push    │     │  Actions │     │  Docker  │     │   ECS    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                       │                 │                 │
                       ▼                 ▼                 ▼
                 ┌──────────┐     ┌──────────┐     ┌──────────┐
                 │   Tests  │     │   Push   │     │  Update  │
                 │  - Unit  │     │   ECR    │     │ Service  │
                 │  - Integ │     └──────────┘     └──────────┘
                 └──────────┘
```

### Infrastructure as Code (Pulumi)
```typescript
// Example Pulumi component structure
export class HappyRobotInfrastructure extends pulumi.ComponentResource {
    public readonly vpc: aws.ec2.Vpc;
    public readonly cluster: aws.ecs.Cluster;
    public readonly database: aws.rds.Instance;
    public readonly loadBalancer: aws.lb.LoadBalancer;

    constructor(name: string, args: HappyRobotArgs, opts?: pulumi.ComponentResourceOptions) {
        super("happyrobot:infrastructure", name, {}, opts);

        // Create VPC
        this.vpc = new NetworkComponent("network", {
            cidrBlock: "10.0.0.0/16",
            availabilityZones: ["us-east-1a", "us-east-1b"],
        }, { parent: this });

        // Create RDS Database
        this.database = new DatabaseComponent("database", {
            engine: "postgres",
            instanceClass: "db.t3.medium",
            allocatedStorage: 100,
            multiAz: true,
        }, { parent: this });

        // Create ECS Cluster
        this.cluster = new ComputeComponent("compute", {
            vpc: this.vpc,
            database: this.database,
        }, { parent: this });

        // Create Load Balancer
        this.loadBalancer = new LoadBalancerComponent("alb", {
            vpc: this.vpc,
            cluster: this.cluster,
        }, { parent: this });
    }
}
```

---

## Performance Architecture

### Caching Strategy
1. **Application-Level Caching**
   - In-memory cache for frequent lookups
   - TTL-based expiration
   - Cache invalidation on updates

2. **Database Query Optimization**
   - Prepared statements
   - Connection pooling
   - Query result caching

3. **CDN for Static Assets**
   - CloudFront distribution
   - Edge caching for CSS/JS
   - Image optimization

### Scaling Strategy
```
┌─────────────────────────────────────────────────────────┐
│                  Auto-Scaling Rules                     │
├─────────────────────────────────────────────────────────┤
│ API Service:                                            │
│ - Target CPU: 70%                                       │
│ - Min tasks: 2                                          │
│ - Max tasks: 10                                         │
│ - Scale out: +2 tasks if CPU > 70% for 2 min           │
│ - Scale in: -1 task if CPU < 30% for 10 min            │
├─────────────────────────────────────────────────────────┤
│ Web Service:                                            │
│ - Target CPU: 60%                                       │
│ - Min tasks: 1                                          │
│ - Max tasks: 5                                          │
│ - Scale out: +1 task if CPU > 60% for 3 min            │
│ - Scale in: -1 task if CPU < 20% for 15 min            │
├─────────────────────────────────────────────────────────┤
│ Database:                                               │
│ - Read replicas: Add if CPU > 80%                      │
│ - Storage auto-scaling: 100GB - 1TB                    │
│ - IOPS: 3000 baseline, 10000 burst                     │
└─────────────────────────────────────────────────────────┘
```

---

## Monitoring & Observability

### Metrics Collection
```
┌─────────────────────────────────────────────────────────┐
│                   Application Metrics                   │
├─────────────────────────────────────────────────────────┤
│ Business Metrics:                                       │
│ - Calls per hour/day                                    │
│ - Conversion rate                                       │
│ - Average negotiation rounds                            │
│ - Revenue per call                                      │
├─────────────────────────────────────────────────────────┤
│ Technical Metrics:                                      │
│ - API response time (p50, p95, p99)                    │
│ - Error rate by endpoint                               │
│ - Database query performance                            │
│ - Cache hit ratio                                       │
├─────────────────────────────────────────────────────────┤
│ Infrastructure Metrics:                                 │
│ - CPU/Memory utilization                                │
│ - Network throughput                                    │
│ - Disk I/O                                             │
│ - Container health                                      │
└─────────────────────────────────────────────────────────┘
```

### Logging Architecture
```
Application Logs ──┐
                   │
System Logs ───────┼───► CloudWatch Logs ───► Log Insights
                   │            │
Audit Logs ────────┘            │
                                ▼
                         ElasticSearch
                         (Future: Advanced
                          log analytics)
```

### Distributed Tracing
```
Request Flow with Correlation IDs:

Client Request
    │
    ├── X-Request-ID: abc-123
    │
    ▼
API Gateway ──► API Service ──► Database
    │              │              │
    │              │              │
    └──────────────┴──────────────┴──► Trace: abc-123
                                        Spans: gateway, api, db
```

---

## Disaster Recovery

### Backup Strategy
1. **Database Backups**
   - Automated daily snapshots
   - Point-in-time recovery (last 7 days)
   - Cross-region backup replication

2. **Code Backups**
   - Git repository (GitHub)
   - Docker images in ECR
   - Infrastructure code in version control

3. **Configuration Backups**
   - Secrets in AWS Secrets Manager
   - Parameter Store for config
   - Terraform state in S3 with versioning

### Recovery Procedures
```
┌─────────────────────────────────────────────────────────┐
│                   RTO/RPO Targets                       │
├─────────────────────────────────────────────────────────┤
│ Component          │ RTO        │ RPO                  │
├────────────────────┼────────────┼──────────────────────┤
│ API Service        │ 5 minutes  │ 0 (stateless)        │
│ Web Service        │ 5 minutes  │ 0 (stateless)        │
│ Database           │ 30 minutes │ 1 hour               │
│ Load Balancer      │ 10 minutes │ 0 (config in code)   │
└────────────────────┴────────────┴──────────────────────┘
```

---

## Cost Optimization

### Resource Optimization
1. **Compute**
   - Fargate Spot for non-critical workloads
   - Right-sizing based on metrics
   - Scheduled scaling for predictable patterns

2. **Database**
   - Reserved instances for production
   - Automated storage scaling
   - Query optimization to reduce I/O

3. **Network**
   - VPC endpoints to avoid NAT charges
   - CloudFront for static content
   - Compress API responses

### Cost Monitoring
```
Budget Alerts:
- Daily spend > $50
- Monthly spend > $1000
- Unusual activity detected

Cost Allocation Tags:
- Environment: dev/staging/prod
- Service: api/web/database
- Team: engineering/operations
- Project: happyrobot-fde
```

---

## Future Enhancements

### Phase 2 Features
1. **WebSocket Support**
   - Real-time updates
   - Live negotiation status
   - Push notifications

2. **Advanced Analytics**
   - Machine learning for price optimization
   - Predictive load matching
   - Carrier behavior analysis

3. **Multi-Region Deployment**
   - Geographic distribution
   - Reduced latency
   - Disaster recovery

### Phase 3 Features
1. **Microservices Architecture**
   - Service mesh (Istio)
   - Event-driven architecture
   - CQRS pattern

2. **Advanced Integrations**
   - ELD integration
   - Load board APIs
   - TMS systems

3. **Mobile Applications**
   - iOS/Android apps
   - Offline capability
   - Push notifications
