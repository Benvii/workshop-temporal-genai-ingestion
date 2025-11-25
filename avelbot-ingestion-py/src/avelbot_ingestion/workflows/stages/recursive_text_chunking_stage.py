import os
import asyncio
from datetime import timedelta
from typing import List

from temporalio import workflow

from avelbot_ingestion.models.RecursiveChunkingStageConfiguration import RecursiveChunkingStageConfiguration
from avelbot_ingestion.models.Source import Source

# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from avelbot_ingestion.activities.recursive_text_chunking_source_activity import recursive_text_chunking_source_activity

WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT= int(os.getenv("WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT", 300)) # Default 300s, 5min

async def recursive_text_chunking_stage(sources: List[Source], recursive_chunking_stage_config: RecursiveChunkingStageConfiguration) -> List[Source]:
    """
    Run recursive text chunking on all sources.

    :param sources: List of sources to be chunked.
    :param recursive_chunking_stage_config: Chunking stage configuration.
    """

    chunking_tasks = [
        workflow.execute_activity(
            activity=recursive_text_chunking_source_activity,
            task_queue="PY_WORKER_TASK_QUEUE",
            args=[source, recursive_chunking_stage_config],
            start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        )
        for source in sources
    ]
    sources = await asyncio.gather(*chunking_tasks)
    return sources