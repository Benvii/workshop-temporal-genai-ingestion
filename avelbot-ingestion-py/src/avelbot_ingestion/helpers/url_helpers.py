from urllib.parse import urlparse
import time
import re

def url_to_file_name(url: str) -> str:
    """Convert a URL into a sanitized, filesystem-safe filename.

        It extracts the hostname, path and query from the URL, concatenates them,
        removes invalid filesystem characters, replaces slashes, trims trailing
        dashes, and enforces a maximum filename length. If the resulting filename
        exceeds the limit, a timestamp suffix is appended. If the URL is invalid,
        a fallback mechanism applies the same truncation logic to the raw URL.

        Args:
            url (str): The input URL to convert.

        Returns:
            str: A sanitized filename derived from the URL.
        """
    max_len = 240

    try:
        parsed = urlparse(url)
        file_name = (
            (parsed.hostname or "") +
            (parsed.path or "") +
            (f"?{parsed.query}" if parsed.query else "")
        )

        # Remplacements
        file_name = file_name.replace("/", "_")
        file_name = re.sub(r"-$", "", file_name)
        file_name = re.sub(r'[\\/:*?"<>|]', "", file_name)

        # Troncature si trop long
        if len(file_name) > max_len:
            suffix = str(int(time.time()))[-7:]   # équivalent à substring(7)
            file_name = file_name[:max_len] + suffix

        return file_name

    except Exception:
        # Fallback si l’URL est invalide
        if len(url) > max_len:
            suffix = str(int(time.time()))[-7:]
            return url[:max_len] + suffix
        return url