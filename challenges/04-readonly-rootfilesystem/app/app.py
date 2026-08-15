"""Electricity-demand chart application."""

import csv
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from filelock import FileLock
from flask import Flask, Response, jsonify, render_template, request

CSV_HEADER = [
    "Entity",
    "Code",
    "Year",
    "Share of total electricity demand coming from data centers",
]
MAX_SCRIPT_BYTES = 65_536


class RefreshScheduler:
    def __init__(self, app: Flask) -> None:
        self.app = app
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def invoke(self) -> None:
        environment = os.environ.copy()
        environment.update(
            {
                "CHART_RUNTIME_CSV": str(self.app.config["RUNTIME_CSV"]),
                "CHART_JSON_PATH": str(self.app.config["CHART_JSON"]),
                "CHART_LOCK_PATH": str(self.app.config["LOCK_PATH"]),
            }
        )
        try:
            subprocess.run(
                [sys.executable, str(self.app.config["REFRESH_SCRIPT"])],
                check=False,
                shell=False,
                env=environment,
                capture_output=True,
                timeout=self.app.config["REFRESH_TIMEOUT"],
            )
        except (OSError, subprocess.SubprocessError):
            self.app.logger.error("Chart refresh failed")

    def start(self) -> None:
        self.invoke()
        self.thread = threading.Thread(target=self._run, name="chart-refresh", daemon=True)
        self.thread.start()

    def _run(self) -> None:
        interval = self.app.config["REFRESH_INTERVAL"]
        while not self.stop_event.wait(interval):
            self.invoke()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2)


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=f".{destination.name}.")
    try:
        with source.open("rb") as source_file, os.fdopen(fd, "wb") as output:
            shutil.copyfileobj(source_file, output)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _validate_record(value: object) -> list[object]:
    if not isinstance(value, dict):
        raise ValueError("Each record must be an object")
    entity = value.get("entity")
    code = value.get("code")
    year = value.get("year")
    share = value.get("share")
    if not isinstance(entity, str) or not entity.strip():
        raise ValueError("entity must be a non-empty string")
    if code is not None and not isinstance(code, str):
        raise ValueError("code must be null or a string")
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError("year must be an integer")
    if isinstance(share, bool) or not isinstance(share, (int, float)) or not math.isfinite(share):
        raise ValueError("share must be a finite number")
    return [entity, "" if code is None else code, year, share]


def _append_rows(path: Path, lock_path: Path, rows: list[list[object]]) -> None:
    with FileLock(lock_path):
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with (
                path.open("r", newline="", encoding="utf-8") as source,
                os.fdopen(fd, "w", newline="", encoding="utf-8") as output,
            ):
                shutil.copyfileobj(source, output)
                writer = csv.writer(output, lineterminator="\n")
                writer.writerows(rows)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise


def _replace_script(path: Path, source: bytes) -> None:
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(source)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def create_app(config: dict[str, object] | None = None, *, start_scheduler: bool = True) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        RUNTIME_CSV=Path(os.environ.get("CHART_RUNTIME_CSV", "/var/run/chart-app/data.csv")),
        CHART_JSON=Path(os.environ.get("CHART_JSON_PATH", "/var/run/chart-app/chart.json")),
        SEED_CSV=Path(os.environ.get("CHART_SEED_CSV", Path(__file__).with_name("seed.csv"))),
        REFRESH_SCRIPT=Path(
            os.environ.get("CHART_REFRESH_SCRIPT", "/opt/chart-app/bin/refresh.py")
        ),
        LOCK_PATH=Path(os.environ.get("CHART_LOCK_PATH", "/var/run/chart-app/data.csv.lock")),
        REFRESH_INTERVAL=float(os.environ.get("CHART_REFRESH_INTERVAL", "15")),
        REFRESH_TIMEOUT=float(os.environ.get("CHART_REFRESH_TIMEOUT", "10")),
    )
    if config:
        app.config.update(config)

    runtime_csv = Path(app.config["RUNTIME_CSV"])
    with FileLock(app.config["LOCK_PATH"]):
        if not runtime_csv.exists():
            _atomic_copy(Path(app.config["SEED_CSV"]), runtime_csv)

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/chart-data")
    def chart_data() -> Response:
        try:
            return Response(
                Path(app.config["CHART_JSON"]).read_bytes(), mimetype="application/json"
            )
        except OSError:
            return jsonify(error="Chart data is unavailable"), 503

    @app.post("/api/data")
    def append_data() -> Response:
        try:
            value = request.get_json(force=False, silent=False)
        except Exception:
            return jsonify(error="Invalid JSON"), 400
        values = value if isinstance(value, list) else [value]
        if not values or not isinstance(value, (dict, list)):
            return jsonify(error="Expected a record or non-empty array"), 400
        try:
            rows = [_validate_record(item) for item in values]
            _append_rows(runtime_csv, Path(app.config["LOCK_PATH"]), rows)
        except ValueError as error:
            return jsonify(error=str(error)), 400
        except OSError:
            return jsonify(error="Unable to update chart data"), 500
        return jsonify(appended=len(rows)), 201

    @app.put("/api/admin/refresh-script")
    def replace_refresh_script() -> Response:
        if request.mimetype != "text/plain":
            return jsonify(error="Unsupported media type"), 415
        if request.content_length is not None and request.content_length > MAX_SCRIPT_BYTES:
            return jsonify(error="Payload too large"), 413
        source = request.stream.read(MAX_SCRIPT_BYTES + 1)
        if len(source) > MAX_SCRIPT_BYTES:
            return jsonify(error="Payload too large"), 413
        try:
            _replace_script(Path(app.config["REFRESH_SCRIPT"]), source)
        except OSError:
            return jsonify(error="Unable to replace refresh script"), 500
        return Response(status=204)

    scheduler = RefreshScheduler(app)
    app.extensions["refresh_scheduler"] = scheduler
    if start_scheduler:
        scheduler.start()
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8080)
