import csv
import json
import threading
from pathlib import Path

import pytest

from app import CSV_HEADER, MAX_SCRIPT_BYTES, RefreshScheduler, create_app


@pytest.fixture
def configured(tmp_path: Path):
    seed = tmp_path / "seed.csv"
    seed.write_text(",".join(CSV_HEADER) + "\nAfrica (IEA),,2020,0.12848516\n", encoding="utf-8")
    script = tmp_path / "refresh.py"
    script.write_text(
        Path(__file__).parents[1].joinpath("refresh.py").read_text(), encoding="utf-8"
    )
    return {
        "TESTING": True,
        "RUNTIME_CSV": tmp_path / "run" / "data.csv",
        "CHART_JSON": tmp_path / "run" / "chart.json",
        "SEED_CSV": seed,
        "REFRESH_SCRIPT": script,
        "LOCK_PATH": tmp_path / "run" / "data.csv.lock",
        "REFRESH_INTERVAL": 0.02,
        "REFRESH_TIMEOUT": 2,
    }


@pytest.fixture
def app(configured):
    return create_app(configured, start_scheduler=False)


def test_seed_initialization_and_existing_data_preserved(configured):
    first = create_app(configured, start_scheduler=False)
    runtime = configured["RUNTIME_CSV"]
    assert runtime.read_bytes() == configured["SEED_CSV"].read_bytes()
    runtime.write_text("existing\n", encoding="utf-8")
    second = create_app(configured, start_scheduler=False)
    assert runtime.read_text(encoding="utf-8") == "existing\n"
    assert first and second


def test_environment_can_override_every_path_and_interval(tmp_path, monkeypatch):
    seed = tmp_path / "input.csv"
    seed.write_text(",".join(CSV_HEADER) + "\nExample,,2020,1\n", encoding="utf-8")
    script = tmp_path / "bin" / "refresh.py"
    script.parent.mkdir()
    script.write_text("pass\n", encoding="utf-8")
    values = {
        "CHART_RUNTIME_CSV": tmp_path / "state" / "custom.csv",
        "CHART_JSON_PATH": tmp_path / "state" / "custom.json",
        "CHART_SEED_CSV": seed,
        "CHART_REFRESH_SCRIPT": script,
        "CHART_LOCK_PATH": tmp_path / "state" / "custom.lock",
        "CHART_REFRESH_INTERVAL": "0.5",
        "CHART_REFRESH_TIMEOUT": "0.25",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, str(value))
    app = create_app(start_scheduler=False)
    assert app.config["RUNTIME_CSV"] == values["CHART_RUNTIME_CSV"]
    assert app.config["CHART_JSON"] == values["CHART_JSON_PATH"]
    assert app.config["REFRESH_SCRIPT"] == values["CHART_REFRESH_SCRIPT"]
    assert app.config["REFRESH_INTERVAL"] == 0.5
    assert app.config["REFRESH_TIMEOUT"] == 0.25
    assert values["CHART_RUNTIME_CSV"].read_bytes() == seed.read_bytes()


def test_initial_refresh_and_chart_response(configured):
    app = create_app(configured, start_scheduler=True)
    app.extensions["refresh_scheduler"].stop()
    response = app.test_client().get("/api/chart-data")
    assert response.status_code == 200
    assert response.get_json() == {
        "series": [
            {
                "entity": "Africa (IEA)",
                "code": None,
                "points": [{"year": 2020, "share": 0.12848516}],
            }
        ]
    }


def test_scheduler_uses_controllable_interval_and_rereads_script(configured, tmp_path):
    marker = tmp_path / "marker"
    configured["REFRESH_SCRIPT"].write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('first')\n", encoding="utf-8"
    )
    app = create_app(configured, start_scheduler=False)
    scheduler: RefreshScheduler = app.extensions["refresh_scheduler"]
    scheduler.invoke()
    configured["REFRESH_SCRIPT"].write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('second')\n", encoding="utf-8"
    )

    class ControlledStop:
        calls = 0

        def wait(self, interval):
            assert interval == configured["REFRESH_INTERVAL"]
            self.calls += 1
            return self.calls > 1

    scheduler.stop_event = ControlledStop()
    scheduler._run()
    assert marker.read_text() == "second"


def test_single_array_validation_and_csv_round_trip(app, configured):
    client = app.test_client()
    special = {"entity": 'A, "quoted"\nregion', "code": None, "year": 2024, "share": 1.25}
    assert client.post("/api/data", json=special).status_code == 201
    assert (
        client.post(
            "/api/data", json=[{"entity": "B", "code": "BB", "year": 2025, "share": 2}]
        ).status_code
        == 201
    )
    with configured["RUNTIME_CSV"].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[-2]["Entity"] == special["entity"]
    assert rows[-2]["Code"] == ""
    assert rows[-1]["Code"] == "BB"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        "bad",
        3,
        {},
        {"entity": "", "code": None, "year": 1, "share": 1},
        {"entity": "x", "code": 4, "year": 1, "share": 1},
        {"entity": "x", "code": None, "year": True, "share": 1},
        {"entity": "x", "code": None, "year": 1.0, "share": 1},
        {"entity": "x", "code": None, "year": 1, "share": True},
        {"entity": "x", "code": None, "year": 1, "share": float("inf")},
    ],
)
def test_invalid_records_are_controlled_and_atomic(app, configured, payload):
    before = configured["RUNTIME_CSV"].read_bytes()
    response = app.test_client().post("/api/data", json=payload)
    assert response.status_code == 400
    assert configured["RUNTIME_CSV"].read_bytes() == before
    assert b"Traceback" not in response.data


def test_malformed_json_is_controlled(app):
    response = app.test_client().post(
        "/api/data", data=b'{"entity":', content_type="application/json"
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid JSON"}


def test_invalid_array_rejects_all_rows(app, configured):
    before = configured["RUNTIME_CSV"].read_bytes()
    response = app.test_client().post(
        "/api/data",
        json=[
            {"entity": "valid", "code": None, "year": 2020, "share": 1},
            {"entity": "", "code": None, "year": 2020, "share": 1},
        ],
    )
    assert response.status_code == 400
    assert configured["RUNTIME_CSV"].read_bytes() == before


def test_concurrent_writes_produce_valid_csv(app, configured):
    def append(index):
        with app.test_client() as client:
            assert (
                client.post(
                    "/api/data",
                    json={"entity": f"E{index}", "code": None, "year": 2020, "share": index},
                ).status_code
                == 201
            )

    threads = [threading.Thread(target=append, args=(index,)) for index in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    with configured["RUNTIME_CSV"].open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 11


def test_concurrent_writes_and_refreshes_publish_complete_files(app, configured):
    scheduler = app.extensions["refresh_scheduler"]

    def append(index):
        with app.test_client() as client:
            response = client.post(
                "/api/data",
                json={"entity": f"E{index}", "code": None, "year": 2020, "share": index},
            )
            assert response.status_code == 201

    writers = [threading.Thread(target=append, args=(index,)) for index in range(6)]
    refreshers = [threading.Thread(target=scheduler.invoke) for _ in range(6)]
    for thread in writers + refreshers:
        thread.start()
    for thread in writers + refreshers:
        thread.join()
    scheduler.invoke()

    with configured["RUNTIME_CSV"].open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 7
    payload = json.loads(configured["CHART_JSON"].read_text(encoding="utf-8"))
    assert len(payload["series"]) == 7


def test_refresh_script_replacement_is_fixed_and_not_executed(app, configured, tmp_path):
    marker = tmp_path / "not-executed"
    source = f"from pathlib import Path\nPath({str(marker)!r}).touch()\n".encode()
    response = app.test_client().put(
        "/api/admin/refresh-script?path=elsewhere",
        data=source,
        content_type="text/plain; charset=utf-8",
        headers={"X-Destination": str(tmp_path / "other")},
    )
    assert response.status_code == 204 and response.data == b""
    assert configured["REFRESH_SCRIPT"].read_bytes() == source
    assert not marker.exists() and not (tmp_path / "other").exists()


def test_refresh_script_limits_and_content_type(app, configured):
    original = configured["REFRESH_SCRIPT"].read_bytes()
    assert (
        app.test_client()
        .put("/api/admin/refresh-script", data=b"x", content_type="application/json")
        .status_code
        == 415
    )
    assert (
        app.test_client()
        .put(
            "/api/admin/refresh-script",
            data=b"x" * (MAX_SCRIPT_BYTES + 1),
            content_type="text/plain",
        )
        .status_code
        == 413
    )
    assert configured["REFRESH_SCRIPT"].read_bytes() == original


def test_non_writable_script_location_is_generic(app, configured, tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("sensitive/path")

    monkeypatch.setattr("app.tempfile.mkstemp", denied)
    response = app.test_client().put(
        "/api/admin/refresh-script", data=b"pass\n", content_type="text/plain"
    )
    assert response.status_code == 500
    assert b"sensitive" not in response.data and b"Traceback" not in response.data


def test_frontend_is_offline_and_has_attribution(app):
    page = app.test_client().get("/").get_data(as_text=True)
    assert (
        "International Energy Agency (2025); International Energy Agency (2026); Ember (2026) – with major processing by Our World in Data"
        in page
    )
    assert "http://" not in page and "https://" not in page
    assert "chart.js" in page and "style.css" in page
