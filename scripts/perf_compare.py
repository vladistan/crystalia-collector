"""Time every method on one dataset; print a markdown table.

Usage: perf_compare.py SOURCE OUTDIR [METHOD ...]
"""

import re
import subprocess
import sys
from pathlib import Path

from crystalia_collector.method import _METHODS

RSS = re.compile(r"(\d+)\s+maximum resident set size")
REAL = re.compile(r"([\d.]+)\s+real")


def measure(source: str, method: str, out: Path) -> tuple[str, float, int, int, int]:
    """Run one method under /usr/bin/time -l; return rc, wall s, peak RSS, output bytes."""
    cmd = ["/usr/bin/time", "-l", "crystalia-collector", "run", source, "-m", method, "-o", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    rss = RSS.search(proc.stderr)
    real = REAL.search(proc.stderr)
    size = out.stat().st_size if out.exists() else 0
    return method, float(real[1]) if real else -1.0, int(rss[1]) if rss else -1, size, proc.returncode


def main() -> None:
    source, outdir, *methods = sys.argv[1:]
    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)
    print("| Method | Wall (s) | Peak RSS (MB) | Output (KB) | rc |")
    print("|---|---|---|---|---|")
    for method in methods or sorted(_METHODS):
        m, wall, rss, size, rc = measure(source, method, out_path / f"{method}.ttl")
        print(f"| {m} | {wall:.2f} | {rss / 1e6:.0f} | {size / 1e3:.0f} | {rc} |", flush=True)


if __name__ == "__main__":
    main()
