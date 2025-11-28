graph TD
    subgraph Threats
        A[Policy Bypass]
        B[Privilege Escalation]
        C[Audit Tampering]
        D[MITM]
        E[DoS]
        F[Token Forgery]
        G[Configuration Injection]
    end

    subgraph Mitigations
        H[Zero-Trust]
        I[Explicit Permissions]
        J[Immutable Audit]
        K[TLS]
        L[Rate Limiting]
        M[Token Signing]
        N[RBAC on Config]
    end

    A --> H
    B --> I
    C --> J
    D --> K
    E --> L
    F --> M
    G --> N