#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
import requests

def download_proxy_list(url: str) -> str:
    """Download proxy list from a remote URL and return raw text."""
    try:
        print(f"Downloading proxy list from {url} ...")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[ERROR] Failed to download proxy list: {e}")
        sys.exit(1)

def load_local_file(path: Path) -> str:
    """Load proxy list from local file."""
    if not path.exists():
        print(f"[ERROR] Local file not found: {path}")
        sys.exit(1)
    return path.read_text()

def parse_proxies(raw_text: str):
    """
    Parse lines formatted like:
        host:port:user:password
    Returns list of tuples.
    """
    proxies = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) != 4:
            print(f"[WARN] Skipping invalid line: {line}")
            continue
        host, port, user, pwd = parts
        proxies.append((host, port, user, pwd))
    return proxies

def write_squid_peers(proxies, output: Path):
    """Generate Squid 'cache_peer' directives."""
    lines = []
    for (host, port, user, pwd) in proxies:
        lines.append(
            f"cache_peer {host} parent {port} 0 no-query round-robin login={user}:{pwd}"
        )

    output.write_text("\n".join(lines) + "\n")
    print(f"Generated {len(proxies)} peers in {output}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate squid_peers.conf from a proxy list URL or file."
    )
    parser.add_argument(
        "source",
        help="URL to download proxies from OR path to local file"
    )
    parser.add_argument(
        "--output",
        default="squid_peers.conf",
        help="Output file (default: squid_peers.conf)"
    )

    args = parser.parse_args()
    output_path = Path(args.output)

    # URL or local file ?
    if args.source.startswith("http://") or args.source.startswith("https://"):
        raw = download_proxy_list(args.source)
    else:
        raw = load_local_file(Path(args.source))

    proxies = parse_proxies(raw)

    if not proxies:
        print("[ERROR] No valid proxies found. Check your input.")
        sys.exit(1)

    write_squid_peers(proxies, output_path)


if __name__ == "__main__":
    main()
