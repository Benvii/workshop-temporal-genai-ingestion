# Utility to split sources by error
from typing import List

from avelbot_ingestion.models.Source import Source


def split_sources_by_error(sources: List[Source]) -> tuple[list[Source], list[Source]]:
    """
    Split a list of Source objects into two lists based on the presence of an error.

    Args:
        sources (List[Source]): List of Source objects to inspect.

    Returns:
        tuple[list[Source], list[Source]]: A tuple containing:
            - The first list with all sources that have no error.
            - The second list with all sources that have an `error` attribute set.
    """
    ok = []
    errors = []
    for s in sources:
        if getattr(s, "error", None):
            errors.append(s)
        else:
            ok.append(s)
    return ok, errors