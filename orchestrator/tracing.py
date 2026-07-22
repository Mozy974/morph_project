"""
Module Tracing Distribué OpenTelemetry / Grafana Tempo (orchestrator/tracing.py).
Permet de tracer les requêtes entre les différents composants du Swarm.
"""

import os
from typing import Optional

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False


def setup_telemetry(service_name: str = "superagent-orchestrator", endpoint: Optional[str] = None):
    """Initialise le TracerProvider OpenTelemetry connecté à Grafana Tempo."""
    if not HAS_OTEL:
        print("[Tracing] ⚠️ OpenTelemetry SDK non disponible. Tracing désactivé.")
        return None

    target_endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    try:
        provider = TracerProvider()
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=target_endpoint, insecure=True))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        print(f"[Tracing] 📡 Tracing OpenTelemetry actif vers {target_endpoint}")
        return trace.get_tracer(service_name)
    except Exception as e:
        print(f"[Tracing] ⚠️ Impossible d'initialiser OpenTelemetry : {e}")
        return trace.get_tracer(service_name)


def get_tracer(module_name: str = "orchestrator"):
    if HAS_OTEL:
        return trace.get_tracer(module_name)
    return None
