import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)

class SemanticDriftDetector:
    """
    Acts as an immune system mapping mathematical embeddings against ground-truth profiles 
    to proactively identify context divergence (Hallucinations) within production systems.
    """
    def __init__(self, drift_threshold: float = 0.65):
        self.drift_threshold = drift_threshold

    def compute_cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        a = np.array(vec_a)
        b = np.array(vec_b)
        if np.all(a == 0) or np.all(b == 0):
            return 0.0
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def evaluate_payload(self, baseline_vector: List[float], incoming_vector: List[float]) -> bool:
        """
        Returns True if the similarity score plummets below acceptable boundaries,
        indicating extreme semantic drift.
        """
        similarity = self.compute_cosine_similarity(baseline_vector, incoming_vector)
        is_drifting = similarity < self.drift_threshold
        
        if is_drifting:
            logger.critical(
                f"SEMANTIC DRIFT DETECTED: Score {similarity:.3f} fell below threshold {self.drift_threshold}. "
                "Triggering Agentic Orchestrator interventions."
            )
            
        return is_drifting
