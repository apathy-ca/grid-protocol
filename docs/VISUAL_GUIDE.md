# GRID Protocol Visual Guide

This document provides a visual guide to the GRID protocol, with diagrams illustrating the core concepts, architecture, and flows.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Architecture](#architecture)
- [Flows](#flows)
- [Use Cases](#use-cases)

---

## Core Concepts

### The Five Core Abstractions

This diagram illustrates the five core abstractions of the GRID protocol and how they relate to each other.

```mermaid
graph TD
    A[Principal] -->|Requests access to| B(Resource)
    B -->|Is governed by| C{Policy}
    C -->|Results in| D[Decision]
    D -->|Is logged to| E((Audit Trail))
```

---

## Architecture

### Reference Architecture

This diagram shows the high-level reference architecture for a GRID implementation.

```mermaid
graph TD
    subgraph Principals
        A[Users]
        B[AI Agents]
        C[Services]
    end

    subgraph GRID Governance Layer
        D[Authentication] --> E[Policy Evaluation]
        E --> F[Audit Logging]
        F --> G[Enforcement]
    end

    subgraph Resource Providers
        H[MCP Servers]
        I[REST APIs]
        J[gRPC Services]
    end

    A & B & C --> D
    G --> H & I & J
```

---

## Flows

### Request Flow

This diagram illustrates the flow of a request through the GRID governance layer.

```mermaid
sequenceDiagram
    participant P as Principal
    participant G as GRID Gateway
    participant R as Resource Provider

    P->>G: Request
    G->>G: 1. Authentication
    G->>G: 2. Policy Evaluation
    G->>G: 3. Audit Logging
    alt Access Allowed
        G->>R: Forward Request
        R-->>G: Response
        G-->>P: Response
    else Access Denied
        G-->>P: 403 Forbidden
    end
```

---

## Use Cases

### AI Agent Tool Access

This diagram illustrates how GRID can be used to govern AI agent tool access.

```mermaid
sequenceDiagram
    participant U as User
    participant A as AI Agent
    participant G as GRID Gateway
    participant T as Tool

    U->>A: "Show me all bugs assigned to my team"
    A->>G: Evaluate policy for jira.search tool
    G-->>A: Allow
    A->>T: Invoke jira.search tool
    T-->>A: Tool result
    A-->>U: "Here are the bugs..."