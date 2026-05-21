from __future__ import annotations

from cloakbridge.detection.pipeline import DetectionPipeline


class LeakageDetected(RuntimeError):
    pass


class LeakageGuard:
    def __init__(self, detection_pipeline: DetectionPipeline) -> None:
        self.detection_pipeline = detection_pipeline

    def assert_safe(self, outbound_text: str) -> None:
        findings = self.detection_pipeline.detect(outbound_text)
        if findings:
            preview = ", ".join(f"{finding.entity_type}:{finding.text}" for finding in findings[:5])
            raise LeakageDetected(f"Outbound request contains raw sensitive content: {preview}")
