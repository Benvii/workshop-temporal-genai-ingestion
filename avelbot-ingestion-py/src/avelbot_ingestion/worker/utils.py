import os
from typing import Optional, List

from temporalio.worker import WorkflowRunner
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)


def build_sandbox_worker_runner_vscode_debug_compatible(
    additional_passthrough_modules: Optional[List[str]] = None,
) -> WorkflowRunner:
    """
    Build the workflow runner with small patch for VSCode debug compatibility.
    See https://github.com/temporalio/sdk-python/issues/238#issuecomment-1370835726
    Args:
        additional_passthrough_modules: Pass though modules names.

    Returns:
        The runner with the correct pass though modules.
    """
    if additional_passthrough_modules is None:
        additional_passthrough_modules = []

    passthrough_modules: List[str] = additional_passthrough_modules

    # Required for VSCode debugging only
    # See https://github.com/temporalio/sdk-python/issues/238#issuecomment-1370835726
    if os.getenv('DEV_USE_UNSANDBOXED_WORKFLOW_RUNNER'):
        passthrough_modules.append("_pydevd_bundle")

    workflow_runner = SandboxedWorkflowRunner(
        restrictions=SandboxRestrictions.default.with_passthrough_modules(*passthrough_modules)
    )

    return workflow_runner