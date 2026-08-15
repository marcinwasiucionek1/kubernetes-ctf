"""Regenerate chart JSON from the runtime CSV."""

import csv
import json
import os
import tempfile
from pathlib import Path

from filelock import FileLock

CSV_PATH = Path(os.environ.get("CHART_RUNTIME_CSV", "/var/run/chart-app/data.csv"))
JSON_PATH = Path(os.environ.get("CHART_JSON_PATH", "/var/run/chart-app/chart.json"))
LOCK_PATH = Path(os.environ.get("CHART_LOCK_PATH", f"{CSV_PATH}.lock"))


def build_chart() -> dict[str, list[dict[str, object]]]:
    series: dict[tuple[str, str | None], list[dict[str, float | int]]] = {}
    with FileLock(LOCK_PATH):
        with CSV_PATH.open(newline="", encoding="utf-8") as source:
            for row in csv.DictReader(source):
                key = (row["Entity"], row["Code"] or None)
                series.setdefault(key, []).append(
                    {
                        "year": int(row["Year"]),
                        "share": float(
                            row["Share of total electricity demand coming from data centers"]
                        ),
                    }
                )

        payload = {
            "series": [
                {"entity": entity, "code": code, "points": sorted(points, key=lambda p: p["year"])}
                for (entity, code), points in series.items()
            ]
        }
        JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=JSON_PATH.parent, prefix=f".{JSON_PATH.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                json.dump(payload, output, allow_nan=False, separators=(",", ":"))
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, JSON_PATH)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
    return payload


if __name__ == "__main__":
    build_chart()
