"""
Définition de l'état du SuperAgent (SuperAgentState).
Gère l'état transmis et enrichi au fil des boucles de rétroaction et du checkpointing.
"""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field
import datetime


@dataclass
class SuperAgentState:
    user_id: int
    task: str
    job_id: str = ""
    query_current: str = ""
    last_completed_node: str = "START"  # "START", "ECLAIREUR", "ANALYSTE", "QA_TESTS", "CODEUR", "REDACTEUR", "DISTILLATEUR"
    eclaireur_report: Dict[str, Any] = field(default_factory=dict)
    analyste_verdict: Dict[str, Any] = field(default_factory=dict)
    qa_test_suite: Dict[str, Any] = field(default_factory=dict)
    dev_implementation: Dict[str, Any] = field(default_factory=dict)
    sandbox_results: Dict[str, Any] = field(default_factory=dict)
    redacteur_report: Dict[str, Any] = field(default_factory=dict)
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2
    status: str = "IN_PROGRESS"

    def __post_init__(self):
        if not self.query_current:
            self.query_current = self.task

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "task": self.task,
            "job_id": self.job_id,
            "query_current": self.query_current,
            "last_completed_node": self.last_completed_node,
            "eclaireur_report": self.eclaireur_report,
            "analyste_verdict": self.analyste_verdict,
            "qa_test_suite": self.qa_test_suite,
            "dev_implementation": self.dev_implementation,
            "sandbox_results": self.sandbox_results,
            "redacteur_report": self.redacteur_report,
            "feedback_history": self.feedback_history,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuperAgentState":
        return cls(
            user_id=data.get("user_id", 0),
            task=data.get("task", ""),
            job_id=data.get("job_id", ""),
            query_current=data.get("query_current", ""),
            last_completed_node=data.get("last_completed_node", "START"),
            eclaireur_report=data.get("eclaireur_report", {}),
            analyste_verdict=data.get("analyste_verdict", {}),
            qa_test_suite=data.get("qa_test_suite", {}),
            dev_implementation=data.get("dev_implementation", {}),
            sandbox_results=data.get("sandbox_results", {}),
            redacteur_report=data.get("redacteur_report", {}),
            feedback_history=data.get("feedback_history", []),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 2),
            status=data.get("status", "IN_PROGRESS"),
        )
