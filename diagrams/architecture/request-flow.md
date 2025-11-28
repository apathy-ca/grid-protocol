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