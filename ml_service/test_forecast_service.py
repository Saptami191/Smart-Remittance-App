from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_promoted_moving_average_artifact_can_be_served(monkeypatch, tmp_path):
    import ml_service.main as main

    model_path = tmp_path / "forecast_model.joblib"
    metadata_path = tmp_path / "forecast_model_metadata.json"

    import joblib

    joblib.dump({"type": "moving_average_7", "value": 88.25}, model_path)
    metadata_path.write_text(
        json.dumps(
            {
                "status": "promoted",
                "model_type": "moving_average_7",
                "from_currency": "USD",
                "to_currency": "INR",
                "backtest": {"selected_candidate": "moving_average_7"},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(main, "MODEL_PATH", Path(model_path))
    monkeypatch.setattr(main, "METADATA_PATH", Path(metadata_path))
    main.forecast_model = None
    main.forecast_metadata = {}
    main.forecast_cache.clear()

    model = main.get_forecast_model()
    result = main.forecast_candidate(model, "moving_average_7", 7)

    assert len(result) == 7
    assert all(item["rate"] == 88.25 for item in result)
    assert all(item["lower_bound"] is None for item in result)
    assert all(item["upper_bound"] is None for item in result)


def test_forecast_model_rejects_unpromoted_artifact(monkeypatch, tmp_path):
    import ml_service.main as main
    import joblib

    model_path = tmp_path / "forecast_model.joblib"
    metadata_path = tmp_path / "forecast_model_metadata.json"
    joblib.dump({"type": "moving_average_7", "value": 88.25}, model_path)
    metadata_path.write_text(
        json.dumps({"status": "rejected", "model_type": None}), encoding="utf-8"
    )

    monkeypatch.setattr(main, "MODEL_PATH", Path(model_path))
    monkeypatch.setattr(main, "METADATA_PATH", Path(metadata_path))
    main.forecast_model = None
    main.forecast_metadata = {}

    from fastapi import HTTPException

    try:
        main.get_forecast_model()
    except HTTPException as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("Rejected forecast model was accepted")
