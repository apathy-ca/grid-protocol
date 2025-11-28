sequenceDiagram
    participant S1 as Service A
    participant G as GRID Gateway
    participant S2 as Service B

    S1->>G: Request to call Service B
    G->>G: Evaluate Policy
    G-->>S1: Allow
    S1->>S2: Call Service B API
    S2-->>S1: Response