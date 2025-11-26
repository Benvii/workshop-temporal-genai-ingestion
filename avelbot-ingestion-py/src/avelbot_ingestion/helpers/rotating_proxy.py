import os
from typing import Dict


def get_rotating_proxy() -> Dict[str, str]:
    """
    Get
    """
    rotating_proxy_url = os.environ.get("ROTATING_PROXY_URL", None)

    if rotating_proxy_url:
        return {
            "http": rotating_proxy_url,
            "https": rotating_proxy_url,
        }

    return None