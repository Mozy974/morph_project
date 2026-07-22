import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from celery.result import AsyncResult

from orchestrator.tasks import task_run_super_agent_graph
from orchestrator.celery_app import celery_app
from orchestrator.memory.checkpoint_store import RedisCheckpointSaver
from orchestrator.memory.event_bus import subscribe_events_async
from orchestrator.metrics import setup_metrics_route, TASKS_TOTAL, ACTIVE_JOBS
from orchestrator.memory.skill_store import (
    lister_skills_pending,
    approuver_skill,
    rejeter_skill,
    nettoyer_et_dedoublonner_skills
)

app = FastAPI(title="API Orchestrateur SuperAgent Enterprise (HITL & Observabilité)")
checkpointer = RedisCheckpointSaver()
setup_metrics_route(app)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class TaskRequest(BaseModel):
    user_id: int
    task: str
    max_retries: int = Field(default=2, ge=0, le=5, description="Nombre maximal de boucles de rétroaction")


@app.get("/")
def read_root():
    """
    Page d'accueil de l'API / Redirection vers le Dashboard Live.
    """
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "OK",
        "message": "L'API Enterprise SuperAgent (HITL + Prometheus + True TDD + Checkpointing) est en ligne !"
    }


@app.get("/app")
def get_dashboard():
    """
    Sert l'interface Web Dashboard Live pour le streaming en temps réel et la modération HITL.
    """
    index_file = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_file)


@app.post("/delegate_task")
def delegate_task(request: TaskRequest):
    """
    Déclenche l'exécution du SuperAgent sous forme de Graphe d'État dynamique avec True TDD, Checkpointing & Event Streaming.
    """
    TASKS_TOTAL.labels(status="ACCEPTED").inc()
    ACTIVE_JOBS.inc()

    task_result = task_run_super_agent_graph.delay(
        user_id=request.user_id,
        task=request.task,
        job_id="",
        max_retries=request.max_retries
    )
    
    return {
        "status": "SuperAgent Enterprise démarré (HITL + Prometheus + True TDD + Checkpointing)",
        "job_id": task_result.id,
        "user_id": request.user_id,
        "max_retries": request.max_retries
    }


@app.get("/stream/{job_id}")
async def stream_job_events(job_id: str):
    """
    Endpoint Server-Sent Events (SSE) : streame en temps réel les événements Pub/Sub de Redis
    vers le client web ou l'application front-end.
    """
    return StreamingResponse(
        subscribe_events_async(job_id),
        media_type="text/event-stream"
    )


@app.post("/resume_task/{job_id}")
def resume_task(job_id: str):
    """
    Reprend un job SuperAgent interrompu depuis son dernier checkpoint Redis.
    """
    has_cp = checkpointer.has_checkpoint(job_id)
    if not has_cp:
        return {
            "status": "Erreur",
            "message": f"Aucun checkpoint trouvé pour le job '{job_id}'."
        }

    TASKS_TOTAL.labels(status="RESUMED").inc()

    task_result = task_run_super_agent_graph.delay(
        user_id=1,
        task="",
        job_id=job_id
    )

    return {
        "status": "Reprise du SuperAgent initiée à partir du dernier Checkpoint validé",
        "job_id": job_id,
        "celery_task_id": task_result.id
    }


@app.get("/status/{job_id}")
def get_task_status(job_id: str):
    task_result = AsyncResult(job_id, app=celery_app)
    
    cp_state = checkpointer.get_checkpoint(job_id)
    checkpoint_info = None
    if cp_state:
        checkpoint_info = {
            "last_completed_node": cp_state.last_completed_node,
            "retry_count": cp_state.retry_count,
            "status": cp_state.status
        }

    response = {
        "job_id": job_id,
        "status": task_result.status,
        "checkpoint": checkpoint_info
    }
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.info)
    return response


# ---------------------------------------------------------
# ENDPOINTS HUMAN-IN-THE-LOOP (HITL) & DÉDOUBLONNAGE
# ---------------------------------------------------------

@app.get("/skills/pending")
def get_pending_skills():
    """
    Retourne la liste des skills distillés en attente de modération HITL.
    """
    return {
        "status": "success",
        "pending_skills": lister_skills_pending()
    }


@app.post("/skills/approve/{skill_id}")
def approve_skill_endpoint(skill_id: str):
    """
    Valide un skill en attente et l'injecte dans la mémoire active du SuperAgent.
    """
    success = approuver_skill(skill_id)
    if not success:
        return {"status": "error", "message": f"Skill '{skill_id}' introuvable ou déjà traité."}
    return {"status": "success", "message": f"Skill '{skill_id}' approuvé et activé dans la mémoire active !"}


@app.post("/skills/reject/{skill_id}")
def reject_skill_endpoint(skill_id: str):
    """
    Rejette un skill en attente.
    """
    success = rejeter_skill(skill_id)
    if not success:
        return {"status": "error", "message": f"Skill '{skill_id}' introuvable ou déjà traité."}
    return {"status": "success", "message": f"Skill '{skill_id}' rejeté."}


@app.post("/skills/clean")
def clean_skills_endpoint():
    """
    Déclenche l'Agent Nettoyeur IA pour dédoublonner et éliminer les contradictions sémantiques.
    """
    result = nettoyer_et_dedoublonner_skills()
    return result


# ---------------------------------------------------------
# ENDPOINTS RAPPORTS
# ---------------------------------------------------------

@app.get("/reports")
def list_reports():
    """
    Liste les rapports terminés (jobs SUCCESS avec un rapport markdown).
    """
    from orchestrator.database import SessionLocal
    from orchestrator.models import Job, Checkpoint
    from sqlalchemy import desc

    db = SessionLocal()
    try:
        jobs = (
            db.query(Job)
            .filter(Job.status == "SUCCESS")
            .order_by(desc(Job.completed_at))
            .limit(20)
            .all()
        )

        reports = []
        for job in jobs:
            cp = db.query(Checkpoint).filter(Checkpoint.job_id == job.job_id).first()
            report_data = None
            if cp and cp.state_blob:
                report_data = cp.state_blob.get("redacteur_report", {})

            reports.append({
                "job_id": str(job.job_id),
                "task": job.task_text[:100],
                "status": job.status,
                "last_node": job.last_node,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "has_report": bool(report_data and report_data.get("rapport_markdown")),
            })

        return {"reports": reports, "count": len(reports)}
    finally:
        db.close()


@app.get("/report/{job_id}")
def get_report(job_id: str):
    """
    Retourne le rapport markdown d'un job terminé.
    """
    from orchestrator.database import SessionLocal
    from orchestrator.models import Job, Checkpoint

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            return {"status": "error", "message": "Job introuvable."}

        cp = db.query(Checkpoint).filter(Checkpoint.job_id == job.job_id).first()
        report_data = {}
        if cp and cp.state_blob:
            report_data = cp.state_blob.get("redacteur_report", {})

        return {
            "job_id": job_id,
            "task": job.task_text,
            "status": job.status,
            "last_node": job.last_node,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "report": report_data,
        }
    finally:
        db.close()
