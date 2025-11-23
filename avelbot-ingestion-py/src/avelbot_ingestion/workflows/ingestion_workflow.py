from datetime import timedelta

from temporalio import workflow

from avelbot_ingestion.models.IngestionWorkflowInput import IngestionWorkflowInput


@workflow.defn(name="IngestionWorkflow")
class IngestionWorkflow:
    @workflow.run
    async def run(self, ingestion_workflow_input: IngestionWorkflowInput) -> str:
        await workflow.execute_activity(activity="PY-PRINT-SOURCE-ACTIVITY",
                                        task_queue="PY_WORKER_TASK_QUEUE",
                                        args=[ingestion_workflow_input.sources[0]],
                                        start_to_close_timeout=timedelta(seconds=30),
                                        )
        return "ok"
