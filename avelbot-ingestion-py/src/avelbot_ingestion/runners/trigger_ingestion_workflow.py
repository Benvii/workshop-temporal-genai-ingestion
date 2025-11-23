import argparse
import asyncio
import os
from datetime import timedelta

import yaml
import uuid

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from avelbot_ingestion.helpers.logging_config import get_app_logger, configure_logging
from avelbot_ingestion.models.IngestionWorkflowInput import IngestionWorkflowInput

logger = get_app_logger(__name__)

# Adjust timeouts for debug (if you put breakpoints)
WORKFLOW_TASK_TIMEOUT=int(os.environ.get("WORKFLOW_TASK_TIMEOUT", 300)) # 300ms, 5min
WORKFLOW_RUN_TIMEOUT=int(os.environ.get("WORKFLOW_RUN_TIMEOUT", 300))

def load_workflow_input_from_yaml(yaml_path: str) -> IngestionWorkflowInput:
    # Load YAML file
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    # Validate & convert into Pydantic model
    return IngestionWorkflowInput.model_validate(data)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow-input-yaml", type=str, required=True)
    args = parser.parse_args()

    logger.info("Loading workflow input from : %s", args.workflow_input_yaml)
    workflow_input = load_workflow_input_from_yaml(args.workflow_input_yaml)

    workflow_id = str(uuid.uuid4())

    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233",
                                  namespace="workshop-ingestion",
                                  data_converter=pydantic_data_converter)

    logger.info("Starting worflow with UUID : %s", workflow_id)

    # Execute a workflow
    result = await client.execute_workflow(
        workflow="IngestionWorkflow",
        args=[workflow_input],
        task_queue="PY_WORKER_TASK_QUEUE",
        id=workflow_id,
        run_timeout=timedelta(seconds=WORKFLOW_RUN_TIMEOUT),
        task_timeout=timedelta(seconds=WORKFLOW_TASK_TIMEOUT)
    )

    logger.info("Workflow finished with the following result : %r", result)


if __name__ == "__main__":
    configure_logging(caller="trigger_ingestion_workflow")
    asyncio.run(main())