# FreeMobilaChat - Architecture Complète

## Diagramme d'Architecture du Système

```mermaid
graph TB
    subgraph "1. CAPTURE DES DONNÉES"
        A[Twitter/X API] -->|Streaming tweets @Free| B[Tweet Collector]
        B -->|Stockage brut| C[(Base de Données<br/>Tweets Bruts)]
    end
    
    subgraph "2. SYSTÈME DE CLASSIFICATION - DÉVELOPPÉ"
        C -->|Extraction| D[Nettoyage & Preprocessing]
        D -->|Tweets nettoyés| E[Classification Engine]
        
        E -->|Multi-modèles| E1[BERT Classifier]
        E -->|Multi-modèles| E2[Mistral LLM]
        E -->|Multi-modèles| E3[Rule-Based Classifier]
        
        E1 & E2 & E3 -->|Résultats| F[Agrégateur de Scores]
        F -->|Classification finale| G{Est une<br/>Réclamation?}
    end
    
    subgraph "3. GÉNÉRATION DE RÉPONSES"
        G -->|OUI| H[Générateur de Réponse]
        H -->|LLM| I[Template Personnalisé]
        I -->|Contient lien| J[Publication Commentaire<br/>avec Lien Chatbot]
        J -->|API Twitter| A
    end
    
    subgraph "4. CHATBOT CONVERSATIONNEL - À DÉVELOPPER"
        J -->|Client clique| K[Interface Chatbot Web]
        K -->|Dialogue| L[Chatbot Engine]
        
        L -->|Demande info| M{Infos complètes?<br/>Nom, Prénom,<br/>Problème}
        M -->|NON| K
        M -->|OUI| N[Création Ticket<br/>Automatique]
    end
    
    subgraph "5. BASE DE CONNAISSANCES"
        O[(Knowledge Base)]
        O -->|FAQ Free| O1[FAQ Officielle]
        O -->|Assistant| O2[Assistant Free]
        O -->|Procédures| O3[Procédures Internes]
        
        O1 & O2 & O3 -->|RAG| L
    end
    
    subgraph "6. RÉSOLUTION INTELLIGENTE"
        N -->|Ticket créé| P[Tentative de Résolution<br/>par Bot]
        P -->|Recherche KB| O
        P -->|Dialogue assisté| L
        
        P -->|Solution trouvée| Q{Problème<br/>Résolu?}
        Q -->|OUI| R[Clôture Automatique<br/>du Ticket]
        Q -->|NON après N essais| S[Escalade vers<br/>Agent Humain]
    end
    
    subgraph "7. INTERFACE INTERNE DE GESTION"
        N & R & S -->|Historique| T[(Base de Données<br/>Tickets)]
        T -->|Lecture| U[Interface Agents]
        
        U -->|Vue tickets| U1[Liste Tickets]
        U -->|Historique| U2[Détails Conversation]
        U -->|Action| U3[Reprise Manuelle]
        
        S -->|Notification| U
        U3 -->|Résolution| R
    end
    
    subgraph "8. TABLEAU DE BORD KPIs"
        T -->|Analytics| V[Dashboard KPIs]
        
        V -->|Métrique 1| V1[Taux de Résolution<br/>Automatique]
        V -->|Métrique 2| V2[Délai Moyen<br/>de Réponse]
        V -->|Métrique 3| V3[Taux d'Escalade<br/>Agent Humain]
        V -->|Métrique 4| V4[Satisfaction Client]
        V -->|Métrique 5| V5[Volume Tweets<br/>par Thème]
        
        V1 & V2 & V3 & V4 & V5 -->|Visualisations| W[Rapports & Alertes]
    end
    
    subgraph "9. STOCKAGE & MONITORING"
        X[(Data Warehouse)]
        C & T -->|ETL| X
        X -->|BI| V
        
        Y[Monitoring System]
        E & L & P -->|Logs| Y
        Y -->|Alertes| Z[Notifications Ops]
    end
    
    G -->|NON| AA[Archivage Tweet<br/>Non-Réclamation]
    AA -->|Statistiques| V
    
    style E fill:#1E3A5F,stroke:#2E86DE,color:#fff
    style L fill:#1E3A5F,stroke:#2E86DE,color:#fff
    style V fill:#10AC84,stroke:#0FB870,color:#fff
    style G fill:#F39C12,stroke:#E67E22,color:#fff
    style Q fill:#F39C12,stroke:#E67E22,color:#fff
    style M fill:#F39C12,stroke:#E67E22,color:#fff
```

## Flux de Données Détaillé

```mermaid
sequenceDiagram
    participant TW as Twitter/X
    participant COL as Collecteur
    participant CLS as Classificateur
    participant GEN as Générateur
    participant BOT as Chatbot
    participant KB as Knowledge Base
    participant TKT as Système Tickets
    participant AGT as Agent Humain
    participant KPI as Dashboard KPIs
    
    TW->>COL: Stream tweets @Free
    COL->>CLS: Tweet brut
    CLS->>CLS: Nettoyage + Classification
    
    alt Tweet = Réclamation
        CLS->>GEN: Tweet identifié comme réclamation
        GEN->>GEN: Génération réponse personnalisée
        GEN->>TW: Publication commentaire + lien chatbot
        
        TW->>BOT: Client clique sur lien
        BOT->>BOT: Demande Nom, Prénom, Problème
        
        loop Collecte informations
            BOT->>BOT: Validation données
        end
        
        BOT->>TKT: Création ticket automatique
        
        loop Tentatives de résolution
            BOT->>KB: Recherche solution
            KB->>BOT: Réponse KB
            BOT->>BOT: Proposition solution
            
            alt Solution acceptée
                BOT->>TKT: Clôture ticket (résolu)
                TKT->>KPI: Mise à jour métriques
            else Solution refusée
                BOT->>BOT: Nouvelle tentative
            end
        end
        
        alt Échec après N essais
            BOT->>TKT: Escalade ticket
            TKT->>AGT: Notification agent
            AGT->>AGT: Prise en charge manuelle
            AGT->>TKT: Résolution + clôture
            TKT->>KPI: Mise à jour métriques
        end
    else Tweet = Non-réclamation
        CLS->>TKT: Archivage statistique
        TKT->>KPI: Mise à jour volume
    end
    
    KPI->>KPI: Calcul KPIs en temps réel
```

## Architecture Technique par Composant

```mermaid
graph TB
    subgraph "CURRENT DEPLOYMENT - Streamlit Cloud"
        direction TB
        SC[Streamlit Cloud Runtime]
        SC --> SC1[Python 3.10 Environment]
        SC --> SC2[Git Auto-Deploy]
        SC --> SC3[HTTPS/SSL Termination]
    end
    
    subgraph "APPLICATION LAYER"
        direction TB
        A1[Streamlit App]
        A1 --> A1a[Home.py]
        A1 --> A1b[Classification_Mistral.py]
        A1 --> A1c[Classification_Mistral.py]
    end
    
    subgraph "ML/AI PROCESSING"
        direction TB
        B1[BERT Classifier]
        B2[Mistral LLM]
        B3[Rule Engine]
        B4[Batch Processor]
        
        B1 --> B1a[CamemBERT-base]
        B2 --> B2a[Mistral-7B via API]
        B3 --> B3a[Regex Patterns]
        B4 --> B4a[Parallel Processing]
    end
    
    subgraph "DATA PROCESSING"
        direction TB
        D1[Tweet Cleaner]
        D2[Validators]
        D3[KPI Calculator]
        
        D1 --> D1a[Emoji Conversion]
        D1 --> D1b[URL Removal]
        D2 --> D2a[CSV Validation]
        D3 --> D3a[Metrics Aggregation]
    end
    
    subgraph "STORAGE - Academic Mode"
        direction TB
        S1[CSV Files]
        S2[Session State]
        S3[Cache]
        
        S1 --> S1a[Upload Storage]
        S2 --> S2a[In-Memory State]
        S3 --> S3a[LRU Cache]
    end
    
    subgraph "EXTERNAL APIs"
        direction TB
        E1[Hugging Face API]
        E2[Mistral API Optional]
        E3[GitHub Auto-Deploy]
    end
    
    A1 --> B1 & B2 & B3 & B4
    B1 & B2 & B3 --> D3
    A1 --> D1 & D2
    A1 --> S1 & S2 & S3
    B1 --> E1
    B2 -.->|Optional| E2
    SC2 --> E3
    
    style SC fill:#3498DB,stroke:#2980B9,color:#fff
    style A1 fill:#1E3A5F,stroke:#2E86DE,color:#fff
    style B1 fill:#E74C3C,stroke:#C0392B,color:#fff
    style B2 fill:#E74C3C,stroke:#C0392B,color:#fff
    style D3 fill:#10AC84,stroke:#0FB870,color:#fff
```

## Infrastructure Déploiement Production (Planifié)

```mermaid
graph TB
    subgraph "LOAD BALANCING & INGRESS"
        LB[Load Balancer]
        LB --> ING[Nginx Ingress Controller]
        ING --> SSL[SSL/TLS Termination]
    end
    
    subgraph "KUBERNETES CLUSTER"
        direction TB
        
        subgraph "Frontend Namespace"
            ST1[Streamlit Pod 1]
            ST2[Streamlit Pod 2]
            ST3[Streamlit Pod 3]
            STS[Streamlit Service]
            STS --> ST1 & ST2 & ST3
        end
        
        subgraph "ML Inference Namespace"
            ML1[BERT Inference Pod]
            ML2[Mistral Inference Pod]
            ML3[Rule Engine Pod]
            MLS[ML Service]
            MLS --> ML1 & ML2 & ML3
        end
        
        subgraph "Chatbot Namespace - Future"
            CB1[Chatbot Pod 1]
            CB2[Chatbot Pod 2]
            CBS[Chatbot Service]
            CBS --> CB1 & CB2
        end
        
        subgraph "Backend Namespace - Future"
            API1[FastAPI Pod 1]
            API2[FastAPI Pod 2]
            APIS[API Service]
            APIS --> API1 & API2
            
            WK1[Celery Worker 1]
            WK2[Celery Worker 2]
            WK3[Celery Worker 3]
        end
    end
    
    subgraph "DATA LAYER"
        direction TB
        
        PG[(PostgreSQL<br/>Tickets & Users)]
        MONGO[(MongoDB<br/>Tweets Archive)]
        REDIS[(Redis<br/>Cache & Queue)]
        VDB[(Vector DB<br/>Knowledge Base)]
        S3[S3 Storage<br/>Models & Data]
    end
    
    subgraph "MONITORING & OBSERVABILITY"
        PROM[Prometheus]
        GRAF[Grafana]
        LOKI[Loki Logs]
        JAEG[Jaeger Tracing]
    end
    
    SSL --> STS
    STS --> MLS
    STS -.Future.-> CBS
    CBS -.Future.-> APIS
    
    APIS -.-> PG & MONGO & REDIS
    ML1 & ML2 --> VDB
    MLS --> S3
    
    WK1 & WK2 & WK3 --> REDIS
    APIS --> REDIS
    
    ST1 & ST2 & ST3 --> PROM
    ML1 & ML2 & ML3 --> PROM
    PROM --> GRAF
    ST1 & ST2 & ST3 --> LOKI
    APIS -.-> JAEG
    
    style LB fill:#3498DB,stroke:#2980B9,color:#fff
    style STS fill:#1E3A5F,stroke:#2E86DE,color:#fff
    style MLS fill:#E74C3C,stroke:#C0392B,color:#fff
    style PG fill:#F39C12,stroke:#E67E22,color:#fff
    style REDIS fill:#E74C3C,stroke:#C0392B,color:#fff
```

## Container Architecture (Docker)

```mermaid
graph LR
    subgraph "Docker Compose Stack"
        direction TB
        
        subgraph "Application Containers"
            D1[streamlit-app:latest]
            D2[ml-inference:latest]
            D3[chatbot-service:latest]
            D4[api-backend:latest]
        end
        
        subgraph "Database Containers"
            D5[postgres:15-alpine]
            D6[mongo:6.0]
            D7[redis:7-alpine]
            D8[qdrant:latest]
        end
        
        subgraph "Infrastructure Containers"
            D9[nginx:alpine]
            D10[prometheus:latest]
            D11[grafana:latest]
        end
        
        D1 --> D2
        D3 --> D4
        D4 --> D5 & D6 & D7 & D8
        D2 --> D8
        
        D9 --> D1 & D3
        D1 & D2 & D3 & D4 --> D10
        D10 --> D11
    end
    
    subgraph "Volumes"
        V1[pg-data]
        V2[mongo-data]
        V3[redis-data]
        V4[models-cache]
        V5[grafana-data]
    end
    
    D5 -.-> V1
    D6 -.-> V2
    D7 -.-> V3
    D2 -.-> V4
    D11 -.-> V5
    
    subgraph "Networks"
        N1[frontend-network]
        N2[backend-network]
        N3[monitoring-network]
    end
    
    D1 & D3 --- N1
    D4 & D5 & D6 & D7 & D8 --- N2
    D10 & D11 --- N3
    D2 --- N1 & N2
    
    style D1 fill:#3498DB,stroke:#2980B9,color:#fff
    style D2 fill:#E74C3C,stroke:#C0392B,color:#fff
    style D5 fill:#F39C12,stroke:#E67E22,color:#fff
```

## Network Architecture

```mermaid
graph TB
    subgraph "Internet"
        U1[End Users]
        U2[Twitter API]
        U3[External APIs]
    end
    
    subgraph "CDN Layer"
        CF[CloudFlare]
        CF --> CF1[DDoS Protection]
        CF --> CF2[Static Caching]
        CF --> CF3[WAF]
    end
    
    subgraph "Application Load Balancer"
        ALB[AWS ALB / GCP Load Balancer]
        ALB --> H1[Health Checks]
        ALB --> H2[SSL Termination]
        ALB --> H3[Auto-scaling Groups]
    end
    
    subgraph "VPC - Application Tier"
        direction TB
        
        subgraph "Public Subnet"
            NAT[NAT Gateway]
            BAS[Bastion Host]
        end
        
        subgraph "Private Subnet - Web"
            WEB1[Streamlit Instance 1]
            WEB2[Streamlit Instance 2]
            WEB3[Streamlit Instance 3]
        end
        
        subgraph "Private Subnet - ML"
            ML1[ML Inference 1]
            ML2[ML Inference 2]
        end
    end
    
    subgraph "VPC - Data Tier"
        direction TB
        
        subgraph "Private Subnet - Database"
            RDS[RDS PostgreSQL Multi-AZ]
            DOC[DocumentDB MongoDB]
            ELAS[ElastiCache Redis]
        end
        
        subgraph "Private Subnet - Storage"
            S3P[S3 Private Bucket]
            EFS[EFS Shared Storage]
        end
    end
    
    subgraph "Monitoring VPC"
        CW[CloudWatch / Stackdriver]
        XR[X-Ray / Cloud Trace]
    end
    
    U1 --> CF
    CF --> ALB
    U2 & U3 --> NAT
    
    ALB --> WEB1 & WEB2 & WEB3
    WEB1 & WEB2 & WEB3 --> ML1 & ML2
    WEB1 & WEB2 & WEB3 --> RDS & DOC & ELAS
    ML1 & ML2 --> S3P & EFS
    
    WEB1 & WEB2 & WEB3 --> CW & XR
    ML1 & ML2 --> CW & XR
    
    style CF fill:#F39C12,stroke:#E67E22,color:#fff
    style ALB fill:#3498DB,stroke:#2980B9,color:#fff
    style RDS fill:#E74C3C,stroke:#C0392B,color:#fff
```

## Légende des Composants

### 🟦 Développé (Production Ready)
- **Système de Classification**: BERT + Mistral + Rules
- **Dashboard Streamlit**: Interface d'analyse et visualisation
- **Preprocessing Pipeline**: Nettoyage et normalisation des tweets
- **KPI Analytics**: Calcul et affichage des métriques

### 🟨 En Développement
- **Tweet Collector**: Capture automatique via Twitter API
- **Response Generator**: Génération de réponses personnalisées

### 🟥 À Développer
- **Chatbot Conversationnel**: Interface de dialogue client
- **Knowledge Base Integration**: Connexion FAQ/Assistant Free
- **Ticket Management System**: Création et suivi des tickets
- **Agent Interface**: Interface pour agents humains
- **Escalation Logic**: Logique de transfert automatique

## Métriques KPIs Principales

| KPI | Description | Objectif |
|-----|-------------|----------|
| **Taux de Classification** | % tweets correctement classifiés | > 90% |
| **Précision Réclamations** | Precision sur détection réclamations | > 85% |
| **Taux Résolution Auto** | % tickets résolus par bot | > 60% |
| **Délai Moyen Réponse** | Temps moyen première réponse | < 5 min |
| **Taux Escalade** | % tickets transmis agents | < 30% |
| **Satisfaction Client** | Score satisfaction post-résolution | > 4/5 |
| **Temps Résolution** | Durée moyenne clôture ticket | < 2h |

## Technologies Utilisées

### Current Stack (Academic/Production)
- **Application**: Streamlit 1.28.1 (Pure Python web framework)
- **ML Frameworks**: PyTorch 2.1.0, Transformers 4.35.0, Scikit-learn 1.3.1
- **Models**: CamemBERT-base, Mistral-7B (API)
- **Visualization**: Plotly 5.17.0, Pandas 2.1.1
- **Data Processing**: NumPy 1.25.2, Emoji 2.8.0
- **Testing**: Pytest 7.4.3, Pytest-cov 4.1.0
- **Deployment**: Streamlit Cloud (GitHub auto-deploy)
- **Storage**: CSV files (academic), Session State (runtime)
- **Version Control**: Git, GitHub, DVC 3.30.1

### Future Production Stack
- **Backend**: FastAPI 0.104.1, Celery, Uvicorn
- **Databases**: PostgreSQL 15 (tickets), MongoDB 6.0 (tweets), Redis 7 (cache/queue)
- **Vector DB**: Qdrant or Pinecone (knowledge base embeddings)
- **Container**: Docker, Docker Compose
- **Orchestration**: Kubernetes (K8s), Helm Charts
- **Cloud**: AWS (RDS, S3, ECS) or GCP (Cloud Run, GCS)
- **Monitoring**: Prometheus, Grafana, CloudWatch
- **Tracing**: Jaeger or AWS X-Ray
- **CI/CD**: GitHub Actions, ArgoCD
- **CDN**: CloudFlare
- **Load Balancer**: AWS ALB or GCP Load Balancer

## Current Deployment Architecture (Streamlit Cloud)

```mermaid
graph TB
    subgraph "Developer Workflow"
        DEV[Developer]
        DEV -->|git push| GH[GitHub Repository]
    end
    
    subgraph "Streamlit Cloud Platform"
        direction TB
        GH -->|Webhook trigger| SC[Streamlit Cloud]
        
        SC --> SC1[Build Environment]
        SC1 -->|pip install| SC2[Install Dependencies]
        SC2 -->|requirements-academic.txt| SC3[35 Packages]
        
        SC3 --> SC4[Launch Streamlit Server]
        SC4 --> SC5[Health Check]
        
        SC5 -->|Pass| SC6[Deploy to Production]
        SC5 -->|Fail| SC7[Rollback to Previous]
    end
    
    subgraph "Runtime Environment"
        SC6 --> RT[Python 3.10 Runtime]
        RT --> RT1[Streamlit Process]
        RT --> RT2[Session State Memory]
        RT --> RT3[File Upload Storage]
    end
    
    subgraph "External Services"
        API1[Hugging Face API]
        API2[GitHub Secrets]
    end
    
    RT1 --> API1
    SC --> API2
    
    subgraph "End Users"
        U1[Web Browser]
        U1 -->|HTTPS| SC6
    end
    
    style GH fill:#333,stroke:#000,color:#fff
    style SC fill:#FF4B4B,stroke:#FF0000,color:#fff
    style RT1 fill:#1E3A5F,stroke:#2E86DE,color:#fff
```

## CI/CD Pipeline (GitHub Actions)

```mermaid
graph LR
    subgraph "Source Control"
        GIT[Git Push]
    end
    
    subgraph "GitHub Actions Workflow"
        direction TB
        
        T1[Trigger: Push to main]
        T1 --> J1[Job 1: Lint]
        
        J1 --> J1a[Black Formatter]
        J1 --> J1b[Flake8 Linter]
        J1 --> J1c[isort Import Sort]
        
        J1 --> J2[Job 2: Test]
        J2 --> J2a[Unit Tests]
        J2 --> J2b[Integration Tests]
        J2 --> J2c[Coverage Report]
        
        J2 --> J3[Job 3: Security]
        J3 --> J3a[Bandit Scan]
        J3 --> J3b[Safety Check]
        J3 --> J3c[Dependency Audit]
        
        J3 --> J4[Job 4: Build]
        J4 --> J4a[Docker Build]
        J4 --> J4b[Tag Image]
        J4 --> J4c[Push to Registry]
        
        J4 --> J5{Deploy?}
        J5 -->|Staging| J6[Deploy Staging]
        J5 -->|Production| J7[Deploy Production]
        
        J6 --> J8[Smoke Tests]
        J8 -->|Pass| J9[Promote to Prod]
        J8 -->|Fail| J10[Rollback]
        
        J7 --> J11[Health Check]
        J11 --> J12[Notify Team]
    end
    
    GIT --> T1
    
    style T1 fill:#F39C12,stroke:#E67E22,color:#fff
    style J5 fill:#E74C3C,stroke:#C0392B,color:#fff
    style J9 fill:#10AC84,stroke:#0FB870,color:#fff
```

## Workflow de Déploiement

```mermaid
graph LR
    A[Code Push GitHub] --> B[CI/CD Pipeline]
    B --> C{Tests Pass?}
    C -->|OUI| D[Build Docker Image]
    C -->|NON| E[Notification Erreur]
    D --> F[Deploy Staging]
    F --> G{Validation?}
    G -->|OUI| H[Deploy Production]
    G -->|NON| I[Rollback]
    H --> J[Monitoring Actif]
    J --> K[Alertes si Anomalie]
    
    style C fill:#F39C12,stroke:#E67E22,color:#fff
    style G fill:#F39C12,stroke:#E67E22,color:#fff
    style H fill:#10AC84,stroke:#0FB870,color:#fff
```

## Évolutivité et Performance

### Architecture Haute Disponibilité (HA)

```mermaid
graph TB
    subgraph "Multi-Region Deployment"
        direction LR
        
        subgraph "Region 1 - Primary (us-east-1)"
            R1LB[Load Balancer]
            R1LB --> R1A[AZ-1a]
            R1LB --> R1B[AZ-1b]
            R1LB --> R1C[AZ-1c]
            
            R1A --> R1DB[(RDS Primary)]
            R1B --> R1DB
            R1C --> R1DB
        end
        
        subgraph "Region 2 - Standby (eu-west-1)"
            R2LB[Load Balancer]
            R2LB --> R2A[AZ-1a]
            R2LB --> R2B[AZ-1b]
            
            R2A --> R2DB[(RDS Replica)]
            R2B --> R2DB
        end
        
        DNS[Route 53 / Cloud DNS]
        DNS -->|Active| R1LB
        DNS -.->|Failover| R2LB
        
        R1DB -->|Async Replication| R2DB
    end
    
    subgraph "Global CDN"
        CF[CloudFlare Edge Nodes]
        CF -->|Geo-routing| DNS
    end
    
    USER[Global Users] --> CF
    
    style R1DB fill:#E74C3C,stroke:#C0392B,color:#fff
    style R2DB fill:#F39C12,stroke:#E67E22,color:#fff
    style DNS fill:#3498DB,stroke:#2980B9,color:#fff
```

### Auto-Scaling Configuration

```mermaid
graph LR
    subgraph "Horizontal Pod Autoscaler (HPA)"
        HPA[HPA Controller]
        
        HPA -->|Monitor| M1[CPU Utilization]
        HPA -->|Monitor| M2[Memory Usage]
        HPA -->|Monitor| M3[Request Rate]
        HPA -->|Monitor| M4[Custom Metrics]
        
        M1 & M2 & M3 & M4 --> DEC{Scale Decision}
        
        DEC -->|CPU > 70%| UP[Scale Up]
        DEC -->|CPU < 30%| DOWN[Scale Down]
        
        UP --> ADD[Add Pod]
        DOWN --> REM[Remove Pod]
    end
    
    subgraph "Pod Configuration"
        MIN[Min Replicas: 2]
        MAX[Max Replicas: 10]
        TARGET[Target CPU: 70%]
    end
    
    ADD --> MAX
    REM --> MIN
    
    style DEC fill:#F39C12,stroke:#E67E22,color:#fff
    style UP fill:#10AC84,stroke:#0FB870,color:#fff
    style DOWN fill:#E74C3C,stroke:#C0392B,color:#fff
```

### Data Backup & Disaster Recovery

```mermaid
graph TB
    subgraph "Production Data"
        PROD[(Production DB)]
        FILES[File Storage]
        MODELS[ML Models]
    end
    
    subgraph "Backup Strategy"
        direction TB
        
        PROD -->|Continuous| WAL[WAL Archiving]
        PROD -->|Daily 2AM| FULL[Full Backup]
        PROD -->|Hourly| INCR[Incremental Backup]
        
        FILES -->|Real-time| S3REP[S3 Replication]
        MODELS -->|Versioned| REGISTRY[Model Registry]
    end
    
    subgraph "Backup Storage"
        VAULT[Backup Vault]
        VAULT --> V1[7 Daily Backups]
        VAULT --> V2[4 Weekly Backups]
        VAULT --> V3[12 Monthly Backups]
        VAULT --> V4[Cross-Region Copy]
    end
    
    subgraph "Recovery Options"
        RTO[RTO: < 15 min]
        RPO[RPO: < 5 min]
        PITR[Point-in-Time Recovery]
    end
    
    WAL & FULL & INCR --> VAULT
    S3REP --> V4
    REGISTRY --> V4
    
    VAULT -.->|Restore| REC[Recovery Process]
    REC --> PITR
    
    style PROD fill:#E74C3C,stroke:#C0392B,color:#fff
    style VAULT fill:#F39C12,stroke:#E67E22,color:#fff
    style REC fill:#10AC84,stroke:#0FB870,color:#fff
```

### Caching Strategy

```mermaid
graph TB
    subgraph "Multi-Layer Caching"
        direction TB
        
        L1[L1: Browser Cache]
        L2[L2: CDN Cache]
        L3[L3: Application Cache]
        L4[L4: Database Cache]
        
        L1 -->|Miss| L2
        L2 -->|Miss| L3
        L3 -->|Miss| L4
        L4 -->|Miss| DB[(Database)]
    end
    
    subgraph "Cache Policies"
        direction TB
        
        P1[Static Assets: 1 year]
        P2[ML Predictions: 1 hour]
        P3[KPI Data: 5 minutes]
        P4[User Session: Session]
    end
    
    subgraph "Invalidation Strategy"
        I1[Time-based TTL]
        I2[Event-based Purge]
        I3[LRU Eviction]
    end
    
    L1 -.-> P1
    L2 -.-> P1 & P2
    L3 -.-> P2 & P3
    L4 -.-> P3 & P4
    
    L2 & L3 & L4 --> I1 & I2 & I3
    
    style L3 fill:#1E3A5F,stroke:#2E86DE,color:#fff
    style DB fill:#E74C3C,stroke:#C0392B,color:#fff
```

### Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        direction TB
        
        subgraph "Network Security"
            WAF[Web Application Firewall]
            DDOS[DDoS Protection]
            VPN[VPN Gateway]
            
            WAF --> DDOS --> VPN
        end
        
        subgraph "Application Security"
            AUTH[Authentication]
            AUTHZ[Authorization]
            ENCRYPT[Encryption at Rest]
            TLS[TLS 1.3 in Transit]
            
            AUTH --> AUTHZ
            ENCRYPT --- TLS
        end
        
        subgraph "Data Security"
            MASK[Data Masking]
            AUDIT[Audit Logs]
            VAULT[Secrets Vault]
            
            MASK --> AUDIT --> VAULT
        end
        
        subgraph "Compliance"
            GDPR[GDPR Compliance]
            SOC2[SOC 2 Controls]
            ISO[ISO 27001]
        end
    end
    
    subgraph "Monitoring & Alerts"
        SIEM[SIEM System]
        IDS[Intrusion Detection]
        VULN[Vulnerability Scan]
        
        SIEM --> ALERT[Security Alerts]
        IDS --> ALERT
        VULN --> ALERT
    end
    
    WAF & DDOS --> SIEM
    AUTH & AUTHZ --> AUDIT
    ENCRYPT & TLS --> GDPR
    
    style WAF fill:#E74C3C,stroke:#C0392B,color:#fff
    style AUTH fill:#F39C12,stroke:#E67E22,color:#fff
    style VAULT fill:#1E3A5F,stroke:#2E86DE,color:#fff
```

### Scalabilité Horizontale
- **Tweet Collector**: Multi-threading pour capture en temps réel (5000+ tweets/sec)
- **Classification**: Batch processing parallèle (200 tweets/sec par worker)
- **Chatbot**: Load balancing sur plusieurs instances (10000+ sessions simultanées)
- **Database**: Sharding pour haute volumétrie (10M+ tweets)

### Optimisations Performance
- **Cache Redis**: Réponses fréquentes pré-calculées (90% hit rate)
- **Vector Database**: Recherche sémantique rapide dans KB (< 100ms)
- **Model Serving**: Quantization + ONNX Runtime (3x speedup)
- **CDN**: Assets statiques chatbot (99% cache hit)
- **Connection Pooling**: PostgreSQL (max 100 connections)
- **Async Processing**: Celery workers pour tâches longues

---

**Version**: 1.0  
**Date**: 2024-01-10  
**Auteur**: FreeMobilaChat Team  
**Statut**: Architecture de Référence
