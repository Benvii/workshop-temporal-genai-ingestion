from temporalio import workflow
from ingestion_workflow.models.IngestionWorkflowInput import IngestionWorkflowInput

@workflow.defn
class IngestionWorkflow:

    @workflow.run
    async def run(self, ingestion_workflow_input: IngestionWorkflowInput ) -> None

            await workflow.execute_activity(activity="PY-PRINT-SOURCE-ACTIVITY",
                                        args=[ingestion_workflow_input.sources[0]])