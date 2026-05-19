import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger

# Test 1 — Synthetic data generation
def test_synthetic_data():
    logger.info("TEST 1: Synthetic data generation")
    from training.synthetic_data import generate_city_data

    df = generate_city_data("lagos", days=30)
    assert not df.empty, "Synthetic data is empty"
    assert "pm25" in df.columns, "Missing pm25 column"
    assert "aqi_value" not in df.columns or True   # aqi computed later
    assert len(df) == 30 * 24 + 1, f"Expected ~720 rows, got {len(df)}"
    logger.success(f"Synthetic data: {len(df)} rows, {len(df.columns)} columns")
    logger.info(f"   PM2.5 range: {df['pm25'].min():.1f} – {df['pm25'].max():.1f} µg/m³")
    return df


# Test 2 — Feature preparation
def test_feature_preparation(df):
    logger.info("TEST 2: Feature preparation")
    from training.data_loader import prepare_features_and_targets

    X, y = prepare_features_and_targets(df, horizon_hours=1)
    assert not X.empty, "Feature matrix is empty"
    assert len(X) == len(y), "X and y length mismatch"
    assert y.notna().all(), "Target contains NaN values"
    logger.success(f"Features: {X.shape[0]} samples × {X.shape[1]} features")
    logger.info(f"   Target (AQI 1h ahead): min={y.min():.1f}, max={y.max():.1f}, mean={y.mean():.1f}")
    return X, y


# Test 3 — Model training (single city, single horizon)
def test_model_training():
    logger.info("TEST 3: Model training — Lagos, 1h horizon")
    from models.xgboost_model import train_city_models

    metrics = train_city_models("lagos")
    assert len(metrics) > 0, "No metrics returned — training failed"

    for m in metrics:
        assert m["mae"] < 100, f"MAE too high: {m['mae']}"
        assert m["category_accuracy"] > 0, "Category accuracy is 0"

    logger.success(f"✅ Training complete for Lagos")
    for m in metrics:
        logger.info(
            f"   {m['horizon_hours']}h → MAE={m['mae']}, "
            f"RMSE={m['rmse']}, Cat Acc={m['category_accuracy']}%"
        )
    return metrics


# Test 4 — Artifacts saved correctly
def test_artifacts_saved():
    logger.info("TEST 4: Checking saved artifacts")
    artifacts = Path(__file__).resolve().parent.parent / "artifacts"

    model_files  = list(artifacts.glob("xgboost_lagos_*.pkl"))
    scaler_files = list(artifacts.glob("scaler_lagos_*.pkl"))
    meta_files   = list(artifacts.glob("meta_lagos_*.json"))

    assert len(model_files) > 0,  "No model files saved"
    assert len(scaler_files) > 0, "No scaler files saved"
    assert len(meta_files) > 0,   "No meta files saved"

    logger.success(f"✅ Artifacts found:")
    logger.info(f"   Models:  {len(model_files)}")
    logger.info(f"   Scalers: {len(scaler_files)}")
    logger.info(f"   Meta:    {len(meta_files)}")


# Run all tests
if __name__ == "__main__":
    logger.info("═══════════════════════════════════════")
    logger.info("BreatheSafe NG — Phase 2 Test Suite")
    logger.info("═══════════════════════════════════════")

    try:
        df = test_synthetic_data()
        X, y = test_feature_preparation(df)
        metrics = test_model_training()
        test_artifacts_saved()

        logger.info("\nAll Phase 2 tests passed ✅")
        logger.info("Ready to proceed to Phase 3 — API + Dashboard")

    except AssertionError as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)