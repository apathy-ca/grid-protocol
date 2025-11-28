sequenceDiagram
    participant PA as Principal (Org A)
    participant GA as GRID Node A
    participant GB as GRID Node B
    participant RB as Resource (Org B)

    PA->>GA: Request to access Resource B
    GA->>GB: Evaluate policy for Principal A
    GB->>GB: Evaluate Policy
    GB-->>GA: Allow
    GA->>RB: Forward Request
    RB-->>GA: Response
    GA-->>PA: Response