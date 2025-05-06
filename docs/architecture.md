# Architecture

This document describes the architecture of the Toro AI Assistant, a serverless application built on AWS services that provides contextualized investment answers using Retrieval Augmented Generation (RAG).

## System Overview

The Toro AI Assistant is designed as an event-driven serverless application that processes user questions, retrieves relevant information from a knowledge base, and delivers contextualized responses. The system follows Clean Architecture principles with a feature-first monorepo structure.

## Architecture Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌────────────┐     ┌───────────────────┐     ┌─────────────┐
│  API Gateway│────▶│ Lambda - Ingest  │───▶│ SNS Topic  │────▶│ Lambda - Process  │────▶│ SNS Topic   │
└─────────────┘     └──────────────────┘     │ (Process)  │     └───────────────────┘     │ (Notify)    │
                           │                 └────────────┘               │               └─────────────┘
                           │                                              │                       │
                           ▼                                              ▼                       ▼
                    ┌─────────────┐                             ┌─────────────────┐      ┌───────────────┐
                    │  DynamoDB   │◀────────────────────────────│ AWS Bedrock     │      │Lambda - Notify│
                    │  Table      │                             │ Knowledge Base  │      └───────────────┘
                    └─────────────┘                             └─────────────────┘              │
                                                                                                 ▼
                                                                                         ┌───────────────┐
                                                                                         │ WebSocket API │
                                                                                         └───────────────┘
```

## Key Components

### 1. API Gateway

- **REST API** - Receives and routes HTTP requests
- **Endpoint:** `/questions` (POST) - For submitting new questions
- **WebSocket API** - For real-time notifications

### 2. Lambda Functions

#### 2.1 Ingest Function (`src/questions/ingest/`)
- **Responsibility:** Receives questions from users, validates input, stores in DynamoDB, and publishes to SNS
- **Trigger:** API Gateway POST request
- **Output:** SNS message to the Process topic

#### 2.2 Process Function (`src/questions/process/`)
- **Responsibility:** Processes questions using RAG with AWS Bedrock, updates DynamoDB with the response
- **Trigger:** SNS message from Process topic
- **Output:** SNS message to Notify topic

#### 2.3 Notify Function (`src/questions/notify/`)
- **Responsibility:** Sends notifications to users about completed responses
- **Trigger:** SNS message from Notify topic
- **Output:** WebSocket messages to connected clients

#### 2.4 WebSocket Handler (`src/websocket/`)
- **Responsibility:** Manages WebSocket connections for real-time notifications
- **Trigger:** WebSocket events ($connect, $disconnect, register)
- **Output:** Updates DynamoDB with connection information

### 3. Amazon Simple Notification Service (SNS)

#### 3.1 Process Topic
- **Purpose:** Decouples the ingest and process stages
- **Publisher:** Ingest Lambda function
- **Subscriber:** Process Lambda function

#### 3.2 Notify Topic
- **Purpose:** Decouples the process and notification stages
- **Publisher:** Process Lambda function
- **Subscriber:** Notify Lambda function

### 4. Amazon DynamoDB

#### 4.1 Questions Table (`toro-ai-assistant-questions`)
- **Primary Purpose:** Store questions and responses
- **Partition Key:** `PK` (format: "USER#{user_id}")
- **Sort Key:** `SK` (format: "QUESTION#{question_id}")
- **Attributes:** user_id, question_id, question, status, answer, created_at, updated_at, etc.

#### 4.2 Connections Table (`toro-websocket-connections`)
- **Primary Purpose:** Store WebSocket connection information
- **Partition Key:** `user_id`
- **Attributes:** connection_id, connected_at

### 5. AWS Bedrock and Knowledge Base

- **Service:** AWS Bedrock with Knowledge Base
- **Inference Model:** Amazon Nova Pro
- **Vector Store:** Amazon OpenSearch Serverless
- **RAG Implementation:** Retrieves relevant documents from the knowledge base to provide context for generating responses

## Data Flow

1. **Question Submission Flow**
   - User submits a question via the REST API
   - Ingest Lambda validates the input, stores in DynamoDB with "pending" status
   - Ingest Lambda publishes an event to the Process SNS topic
   - Process Lambda receives the event, retrieves the question from DynamoDB
   - Process Lambda uses AWS Bedrock to generate a contextual answer
   - Process Lambda updates DynamoDB with the answer and "completed" status
   - Process Lambda publishes an event to the Notify SNS topic
   - Notify Lambda receives the event and sends notifications via WebSocket

2. **Real-time Notification Flow**
   - User connects to WebSocket API
   - User registers their user_id with the connection
   - Connection information is stored in DynamoDB
   - When a question is answered, Notify Lambda sends a message via WebSocket

## Code Structure

The project follows a feature-first monorepo structure:

```
.
├── lib/                   # Shared libraries
│   ├── adapters/          # External service clients (DynamoDB, Bedrock)
│   ├── core/              # Utilities, constants, and shared functionality
│   ├── factories/         # Client creation and configuration
│   ├── models/            # Data models and validation schemas
│   └── utils/             # Utility functions
│
├── src/                   # Lambda functions
│   ├── questions/         # Question-related Lambdas
│   │   ├── ingest/        # Ingest Lambda - API Gateway entry point
│   │   ├── process/       # Process Lambda - Handles RAG execution
│   │   └── notify/        # Notify Lambda - WebSocket notifications
│   └── websocket/         # WebSocket connection management
│
├── infra/                 # Infrastructure as code
│   └── serverless-template.yaml  # AWS SAM template
│
└── tests/                 # Automated tests
    ├── lib/               # Tests for shared libraries
    └── questions/         # Tests for Lambda functions
```

The codebase takes a pragmatic approach to architecture:

- **Feature-first organization**: Code is organized by feature/domain rather than by layer
- **Shared libraries**: Common functionality extracted to a central location
- **Separation by function**: Each Lambda handles a specific part of the workflow
- **Infrastructure as code**: All AWS resources defined in the SAM template

## Infrastructure as Code

The infrastructure is defined using AWS Serverless Application Model (SAM) in the `infra/serverless-template.yaml` file. The template defines all AWS resources:

- Lambda functions
- API Gateway endpoints
- DynamoDB tables
- SNS topics
- IAM roles and policies

## Architecture Principles

### 1. Event-Driven Architecture
- Components communicate asynchronously via events (SNS messages)
- Decouples services and enables independent scaling

### 2. Serverless First
- No servers to manage
- Pay-per-use cost model
- Auto-scaling based on demand

### 3. Clean Architecture
- Separation of concerns
- Domain models and business logic are independent of external frameworks
- Dependency injection for testability

### 4. Single Responsibility Principle
- Each Lambda function has a specific responsibility
- Shared code is extracted into the `lib` directory

## Scalability

- DynamoDB auto-scaling
- Lambda concurrency scales automatically
- SNS provides reliable message delivery

For more information on deployment, see [Deployment Guide](deployment.md).
For information on clean code practices and scalability, see [Clean Code and Scalability](clean-code-scalability.md).

---

<div align="center">
  <a href="../README.md">
    <img src="https://img.shields.io/badge/⬅️_Back_to_Home-0A66C2?style=for-the-badge" alt="Back to Home"/>
  </a>
</div>
