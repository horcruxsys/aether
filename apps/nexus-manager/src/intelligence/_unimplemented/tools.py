"""
UNIMPLEMENTED: LangChain tools module

This module is a placeholder for Phase 2 autonomous intelligence work.
It contains only stub/canned logic and requires langchain dependencies
that are not currently installed.

To enable this in the future:
1. Fix pyproject.toml langchain dependency versions
2. Regenerate uv.lock with `uv lock`
3. Run `uv sync` to install dependencies
4. Implement real tool execution logic
"""

raise NotImplementedError(
    "LangChain tools are not yet implemented. "
    "This is planned for Phase 2: Autonomous Intelligence."
)

# Below is the original (non-functional) code preserved for reference:
# from langchain.tools import tool
# import logging
#
# logger = logging.getLogger(__name__)
#
# @tool
# def delete_tombstone_vector(vector_id: str) -> str:
#     """
#     Deletes a stale or hallucinated vector embedding from the Qdrant backend permanently.
#     Use this strictly when semantic drift is detected or an entry is flagged as Tombstone.
#     """
#     logger.warning(f"ACTION REQUIRED: Executing semantic tombstone drop for {vector_id}")
#     # Conceptual Qdrant logic injected here
#     return f"Successfully pruned vector {vector_id} from physical memory."
#
# @tool
# def trigger_legacy_resync(urn: str) -> str:
#     """
#     Alerts the Rust refinery-core node to immediately run a bulk extraction CDC pipeline
#     against the target relational database (URN).
#     """
#     logger.info(f"ACTION REQUIRED: Signaling Rust gRPC for upstream extraction: {urn}")
#     return f"Bulk CDC resync triggered for {urn}."
