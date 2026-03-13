PLAYBOOKS = {
    "rollback_release": {
        "risk_level": "medium",
        "blast_radius": "service scoped",
        "rollback_available": True,
        "required_role": "prod_approver",
    },
    "restart_deployment": {
        "risk_level": "low",
        "blast_radius": "pod set",
        "rollback_available": False,
        "required_role": "sre",
    },
    "retry_job": {
        "risk_level": "low",
        "blast_radius": "single workflow",
        "rollback_available": False,
        "required_role": "support",
    },
    "pause_rollout_and_notify": {
        "risk_level": "low",
        "blast_radius": "deployment pipeline",
        "rollback_available": True,
        "required_role": "sre",
    },
    "enable_safe_mode": {
        "risk_level": "medium",
        "blast_radius": "feature subset",
        "rollback_available": True,
        "required_role": "senior_sre",
    },
}
