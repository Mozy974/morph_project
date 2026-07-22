"""
Module Tracing Distribué OpenTelemetry / Grafana Tempo avec Sampling Adaptatif & Spans Personnalisés (orchestrator/tracing.py).
"""

import os
import logging
from typing import Optional

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

logger = logging.getLogger("superagent.tracing")


def setup_telemetry(service_name: str = "superagent-orchestrator", endpoint: Optional[str] = None, sample_rate: float = 0.1):
    """Initialise le TracerProvider OpenTelemetry avec Sampling Adaptatif (ratio 10%)."""
    if not HAS_OTEL:
        print("[Tracing] ⚠️ OpenTelemetry SDK non disponible. Tracing désactivé.")
        return None

    target_endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    try:
        # Sampling Adaptatif : 10% par défaut en production pour réduire les coûts
        sampler = ParentBased(root=TraceIdRatioBased(sample_rate))
        provider = TracerProvider(sampler=sampler)
        
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=target_endpoint, insecure=True))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        print(f"[Tracing] 📡 Tracing OpenTelemetry actif vers {target_endpoint} (Sampling adaptatif: {sample_rate*100}%)")
        return trace.get_tracer(service_name)
    except Exception as e:
        print(f"[Tracing] ⚠️ Impossible d'initialiser OpenTelemetry : {e}")
        return trace.get_tracer(service_name)


def get_tracer(module_name: str = "orchestrator"):
    if HAS_OTEL:
        return trace.get_tracer(module_name)
    return None


def get_current_trace_id() -> str:
    """Retourne l'ID de la trace courante pour corréler avec les logs SRE."""
    if HAS_OTEL:
        span = trace.get_current_span()
        if span and span.get_span_context():
            return f"{span.get_span_context().trace_id:032x}"
    return "00000000000000000000000000000000"


def trace_rag_query(query: str, db_system: str = "chromadb"):
    """Génère un span personnalisé pour une requête RAG vectorielle."""
    tracer = get_tracer("rag")
    if tracer:
        return tracer.start_as_current_span(
            "rag_query",
            attributes={
                "db.system": db_system,
                "db.query": "similarity_search",
                "rag.input_length": len(query)
            }
        )
    return None
