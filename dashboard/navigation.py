"""Native page groups and presentation-only product direction."""

PAGE_GROUPS = {
    "": (("pages/overview.py", "Overview"),),
    "Workflows": (
        ("pages/soc_investigation.py", "SOC Investigation"),
        ("pages/ai_system_risk_review.py", "AI System Risk Review"),
    ),
    "Platform": (
        ("pages/platform_evaluation.py", "Platform Evaluation"),
        ("pages/knowledge_workspace.py", "Knowledge Workspace"),
        ("pages/activity.py", "Activity"),
        ("pages/about.py", "About"),
    ),
}

# The old WORKFLOW_MAP remains import-compatible for downstream presentation tools.
# Primary product copy uses these three pillars instead of the historical quadrants.
PILLARS = (
    {
        "title": "SOC",
        "workflow": "SOC Investigation",
        "status": "Active",
        "description": "Supplied telemetry investigation, observations and hypotheses, evidence gaps, conditional response and human approval. Microsoft JSON/CSV files are experimental inputs; no live connector.",
        "page": "pages/soc_investigation.py",
    },
    {
        "title": "AI Security",
        "workflow": "AI Security Assessment",
        "status": "Planned",
        "description": "Future technical assessment: prompt injection, retrieval poisoning, tool permission boundaries, data leakage and adversarial control tests. This sprint tests the shared knowledge pipeline; there is no separate runnable analyzer.",
    },
    {
        "title": "AI Safety, Assurance & Policy",
        "workflow": "AI System Risk Review",
        "status": "Active",
        "description": "AI-system risk, reliability and policy applicability, missing implementation evidence, human oversight and residual risk. A policy requirement does not prove implementation or model correctness.",
        "page": "pages/ai_system_risk_review.py",
    },
)

WORKFLOW_MAP = (
    {
        "domain": "Security Operations",
        "technical": {
            "title": "SOC Investigation",
            "status": "Active",
            "description": "Analyze security telemetry, separate observed evidence from analyst inference, identify evidence gaps, and prepare investigation and conditional response guidance.",
            "page": "pages/soc_investigation.py",
        },
        "governance": {
            "title": "SOC Policy & Governance Review",
            "status": "Planned",
            "description": "Policy and procedural constraints, escalation, approval boundaries, documentation, evidence retention, mission constraints and audit reporting.",
        },
    },
    {
        "domain": "AI Security",
        "technical": {
            "title": "AI Security Assessment",
            "status": "Planned",
            "description": "AI attack surface, prompt injection, retrieval poisoning, tool and agent authorization, trust boundaries, technical controls and security evaluation planning.",
        },
        "governance": {
            "title": "AI System Risk Review",
            "status": "Active",
            "description": "Assess an AI system or proposed AI use case for governance, security, privacy and operational risk, including controls, human oversight and missing evidence.",
            "page": "pages/ai_system_risk_review.py",
        },
    },
)
