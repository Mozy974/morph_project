from orchestrator.celery_app import celery_app
from orchestrator.agents.eclaireur import AgentEclaireur
from orchestrator.agents.analyste import AgentAnalyste
from orchestrator.agents.redacteur import AgentRedacteur
from orchestrator.graph_runner import SuperAgentGraphRunner


@celery_app.task(name="agents.run_super_agent_graph", bind=True)
def task_run_super_agent_graph(self, user_id: int = 1, task: str = "", job_id: str = "", max_retries: int = 2):
    """
    Exécute ou reprend le SuperAgent sous forme de graphe d'état dynamique avec checkpointing Redis.
    """
    effective_job_id = job_id or self.request.id
    runner = SuperAgentGraphRunner(user_id=user_id, job_id=effective_job_id, task=task, max_retries=max_retries)
    return runner.execute()


@celery_app.task(name="agents.run_eclaireur")
def task_run_eclaireur(user_id: int, task: str):
    agent = AgentEclaireur(user_id=user_id)
    return agent.analyser_sujet(task)


@celery_app.task(name="agents.run_analyste")
def task_run_analyste(rapport_precedent: dict):
    agent = AgentAnalyste()
    return agent.evaluer_rapport(rapport_precedent)


@celery_app.task(name="agents.run_redacteur")
def task_run_redacteur(verdict: dict):
    agent = AgentRedacteur()
    return agent.rediger_rapport(verdict)
