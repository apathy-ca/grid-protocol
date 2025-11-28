# GRID Specification - Quick Start

Welcome to the GRID Protocol Specification repository!

## ⚡ 5-Minute Start

**What is GRID?**
A universal governance protocol for machine-to-machine interactions. Think of it as the "BIND for DNS" – SARK is the reference implementation.

**Core Concept:**
```
Principal (human, AI, service, device)
    ↓
  Request access to Resource (tool, data, service)
    ↓
  GRID evaluates Policy (allow/deny)
    ↓
  GRID logs decision (immutable audit)
```

**5 Core Abstractions:**
1. **Principal** – Who's asking?
2. **Resource** – What are they accessing?
3. **Action** – What do they want to do?
4. **Policy** – Rules determining allow/deny
5. **Audit** – Immutable record

## 📚 Where to Start?

### I'm a...

**Decision Maker** (30 minutes)
→ Read: README.md then GRID_SPECIFICATION_SUMMARY.md

**Architect/Engineer** (2-3 hours)
→ Read: README.md → Summary → Full Specification

**Security Officer** (45 minutes)
→ Read: Summary, then Specification §6 & §7

**Protocol Implementer** (2-3 hours)
→ Read: Specification §3 & §9, then Gap Analysis

**SARK Maintainer** (3-4 hours)
→ Read: All, focus on Gap Analysis §10 (Migration Path)

## 📄 Documents at a Glance

| Document | Pages | Focus | Time |
|----------|-------|-------|------|
| **README.md** | 14K | Overview & quick links | 5 min |
| **GRID_SPECIFICATION_SUMMARY.md** | 9K | Key concepts | 10-15 min |
| **GRID_SPECIFICATION_README.md** | 11K | Navigation & FAQ | 10 min |
| **GRID_PROTOCOL_SPECIFICATION_v0.1.md** | 76K | Complete spec | 2-3 hrs |
| **GRID_GAP_ANALYSIS_AND_IMPLEMENTATION_NOTES.md** | 29K | SARK assessment | 1-2 hrs |

## 🎯 Key Numbers

- **4,104 lines** of specification and analysis
- **15 major sections** in the complete specification
- **85% compliance** of SARK with GRID v0.1
- **<5ms** policy evaluation (cache hits)
- **80-95%** cache hit rate in production

## ✨ The Essence

**GRID Principles:**
- ✅ Protocol-agnostic (works above HTTP, gRPC, MCP, custom RPC)
- ✅ Federated (no central authority)
- ✅ Zero-trust (default deny)
- ✅ Policy-first (declarative rules)
- ✅ Immutable audit (INSERT-ONLY logs)

**SARK Status:**
- ✅ 85% GRID v0.1 compliant
- ✅ Production-ready for MCP governance
- ⚠️ MCP-specific (multi-protocol v2.0)
- 🚀 Foundation for GRID v1.0 with federation

## 🚀 Next Steps

1. **Start here:** README.md
2. **Quick overview:** GRID_SPECIFICATION_SUMMARY.md
3. **Deep dive:** GRID_PROTOCOL_SPECIFICATION_v0.1.md
4. **For SARK:** GRID_GAP_ANALYSIS_AND_IMPLEMENTATION_NOTES.md
5. **See it in action:** Check out the [`examples/`](examples/) directory.

## 💡 Quick Example

```rego
# A policy in Rego (declarative, used in SARK)
package grid.authorization

default allow := false  # Zero-trust

# Developers can execute medium sensitivity tools
allow if {
    input.principal.role == "developer"
    input.resource.sensitivity_level in ["low", "medium"]
    input.action == "execute"
}

# Admins have full access
allow if {
    input.principal.role == "admin"
}
```

## 🤔 FAQ

**Q: Is GRID just for MCP/AI?**
A: No! GRID works for any machine-to-machine interaction (HTTP, gRPC, services, IoT, etc.)

**Q: Can I use this today?**
A: Yes! SARK v1.0 is production-ready for MCP governance.

**Q: What's the difference between GRID and SARK?**
A: GRID = Specification, SARK = Reference implementation

**Q: When is v1.0?**
A: GRID v1.0 planned for 2026 Q1-Q2 with federation and multi-protocol support

## 📞 Questions?

See GRID_SPECIFICATION_README.md for more FAQ and next steps.

---

**Let's govern machine-to-machine interactions! 🚀**
