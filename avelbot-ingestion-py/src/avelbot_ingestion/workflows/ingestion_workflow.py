import asyncio
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

        # -- Démarrage d'un pool d'activitées en parallèle sur toutes les sources --
        printing_tasks = [
            # NE PAS AWAIT ICI
            workflow.execute_activity(
                activity="PY-PRINT-SOURCE-ACTIVITY",
                task_queue="PY_WORKER_TASK_QUEUE",
                args=[source],
                start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
            )
            for source in ingestion_workflow_input.sources
        ]
        printing_results_sources = await asyncio.gather(*printing_tasks) # Exécute toutes les tâches en parallèle sur chaques sources

        return f"Handeled {len(printing_results_sources)} sources"
