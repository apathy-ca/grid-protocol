graph TD
    subgraph Governed Path
        A[User] --> B[SARK Gateway]
        B --> C{Policy Check}
        C --> D[Registered MCP Server]
    end

    subgraph Shadow IT Path
        E[User] --> F[Unregistered MCP Server]
        F --> G[No Policy Check]
        G --> H[No Audit Trail]
    end