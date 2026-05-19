import os
import yaml
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
import shap
from loguru import logger

# Paths
ML_ROOT      = Path(__file__).resolve().parent.parent
ARTIFACTS    = ML_ROOT / "artifacts"
CONFIG_PATH  = ML_ROOT / "config" / "model_params.yaml"
ARTIFACTS.mkdir(exist_ok=True)

with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

XGB_PARAMS       = CONFIG["xgboost"]
FORECAST_HORIZONS = CONFIG["forecast_horizons"]


# Train
def train_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> xgb.XGBRegressor:
    """Train XGBoost model with early stopping on validation set."""

    model = xgb.XGBRegressor(
        n_estimators       = XGB_PARAMS["n_estimators"],
        max_depth          = XGB_PARAMS["max_depth"],
        learning_rate      = XGB_PARAMS["learning_rate"],
        subsample          = XGB_PARAMS["subsample"],
        colsample_bytree   = XGB_PARAMS["colsample_bytree"],
        min_child_weight   = XGB_PARAMS["min_child_weight"],
        early_stopping_rounds = XGB_PARAMS["early_stopping_rounds"],
        eval_metric        = XGB_PARAMS["eval_metric"],
        random_state       = 42,
        n_jobs             = -1,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    logger.info(f"Best iteration: {model.best_iteration}")
    return model


# Evaluate
def evaluate_model(
    model: xgb.XGBRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    city: str,
    horizon: int,
) -> dict:
    """Evaluate model — MAE, RMSE, and AQI category accuracy."""
    from preprocessing.feature_engineer import get_aqi_category

    preds = model.predict(X_test)
    preds = np.clip(preds, 0, 500)   # AQI can't be negative or above 500

    mae  = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))

    # Category accuracy — did we predict the right health band?
    true_cats  = [get_aqi_category(v) for v in y_test]
    pred_cats  = [get_aqi_category(v) for v in preds]
    cat_acc    = sum(t == p for t, p in zip(true_cats, pred_cats)) / len(true_cats)

    metrics = {
        "city":             city,
        "horizon_hours":    horizon,
        "mae":              round(mae, 2),
        "rmse":             round(rmse, 2),
        "category_accuracy": round(cat_acc * 100, 1),
        "n_test_samples":   len(y_test),
        "evaluated_at":     datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        f"[{city} | {horizon}h] MAE={mae:.2f} | RMSE={rmse:.2f} | "
        f"Category Acc={cat_acc*100:.1f}%"
    )
    return metrics


# SHAP feature importance
def explain_model(
    model: xgb.XGBRegressor,
    X_sample: pd.DataFrame,
    city: str,
    horizon: int,
) -> pd.DataFrame:
    """
    Compute SHAP values to explain which features drive predictions.
    Uses a sample of 500 rows for speed.
    """
    sample = X_sample.sample(min(500, len(X_sample)), random_state=42)

    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sample)

    importance_df = pd.DataFrame({
        "feature":    X_sample.columns,
        "mean_shap":  np.abs(shap_values).mean(axis=0),
    }).sort_values("mean_shap", ascending=False).reset_index(drop=True)

    logger.info(f"Top 5 features for {city} {horizon}h forecast:")
    for _, row in importance_df.head(5).iterrows():
        logger.info(f"  {row['feature']}: {row['mean_shap']:.3f}")

    return importance_df


# Save model artifacts
def save_model(model, scaler, feature_cols: list, city: str, horizon: int, metrics: dict):
    """Save model, scaler, feature list and metrics to artifacts/."""
    version   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    base_name = f"xgboost_{city}_{horizon}h_{version}"

    # Model
    model_path = ARTIFACTS / f"{base_name}.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    # Scaler
    scaler_path = ARTIFACTS / f"scaler_{city}_{horizon}h_{version}.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    # Feature list + metrics as JSON
    import json
    meta = {
        "city":          city,
        "horizon_hours": horizon,
        "version":       version,
        "feature_cols":  feature_cols,
        "metrics":       metrics,
        "model_file":    model_path.name,
        "scaler_file":   scaler_path.name,
    }
    meta_path = ARTIFACTS / f"meta_{city}_{horizon}h_{version}.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    logger.success(f"Saved model artifacts: {base_name}")
    return str(model_path)


# Full training pipeline for one city
def train_city_models(city: str, data_source: str = "auto") -> list[dict]:
    """
    Full training pipeline for one city across all forecast horizons.
    Returns list of metrics dicts (one per horizon).
    """
    from training.data_loader import load_training_data, prepare_features_and_targets

    logger.info(f"═══ Training models for {city} ═══")

    df, source = load_training_data(city)
    if df.empty:
        logger.error(f"No data available for {city}")
        return []

    logger.info(f"Data source: {source} | Records: {len(df)}")
    all_metrics = []

    for horizon in FORECAST_HORIZONS:
        logger.info(f"--- Horizon: {horizon}h ---")

        X, y = prepare_features_and_targets(df, horizon_hours=horizon)

        if len(X) < 100:
            logger.warning(f"Too few samples for {city} {horizon}h — skipping")
            continue

        # Time series split — never shuffle time series data
        tscv      = TimeSeriesSplit(n_splits=5)
        splits    = list(tscv.split(X))

        # Use last split for final train/val/test
        train_idx, test_idx = splits[-1]
        val_idx             = splits[-2][1]   # second to last val as validation

        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]
        X_val   = X.iloc[val_idx]
        y_val   = y.iloc[val_idx]
        X_test  = X.iloc[test_idx]
        y_test  = y.iloc[test_idx]

        # Scale features
        scaler  = StandardScaler()
        X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
        X_val_scaled   = pd.DataFrame(scaler.transform(X_val),   columns=X_val.columns)
        X_test_scaled  = pd.DataFrame(scaler.transform(X_test),  columns=X_test.columns)

        # Train
        model = train_xgboost(X_train_scaled, y_train, X_val_scaled, y_val)

        # Evaluate
        metrics = evaluate_model(model, X_test_scaled, y_test, city, horizon)
        all_metrics.append(metrics)

        # SHAP explanation
        explain_model(model, X_test_scaled, city, horizon)

        # Save
        save_model(model, scaler, list(X.columns), city, horizon, metrics)

    return all_metrics