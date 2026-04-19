from typing import List

class TenantIsolator:
    """
    Acts as a rigid software-defined boundary preventing cross-tenant vector hallucinations 
    deep inside the Qdrant indexing cores.
    """
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def inject_boundary_filters(self, original_query_filters: dict) -> dict:
        """
        Dynamically merges the tenant UUID onto raw LLM vector projection filters,
        preventing any Agent from scraping context beyond its authorized SaaS boundaries.
        """
        isolated_filter = original_query_filters.copy()
        isolated_filter["tenant_id"] = self.tenant_id
        return isolated_filter

    def assert_validity(self, vector_payloads: List[dict]):
        for payload in vector_payloads:
            if payload.get("tenant_id") != self.tenant_id:
                raise PermissionError("SEVERE ISOLATION FAULT: Cross-tenant payload detected.")
