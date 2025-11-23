import logging
import os
from datetime import timedelta

from temporalio import workflow

from avelbot_ingestion.models.IngestionWorkflowInput import IngestionWorkflowInput


WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT= int(os.getenv("WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT", 300)) # Default 300s, 5min

@workflow.defn(name="IngestionWorkflow")
class IngestionWorkflow:
    @workflow.run
    async def run(self, ingestion_workflow_input: IngestionWorkflowInput) -> str:

        logging.info("IngestionWorkflow started.")

        await workflow.execute_activity(
            activity="PY-PRINT-SOURCE-ACTIVITY",
            task_queue="PY_WORKER_TASK_QUEUE",
            args=[ingestion_workflow_input.sources[0]],
            start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        )

        return "ok"
