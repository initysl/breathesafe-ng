import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger

ML_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_ROOT))

from models.xgboost_model import train_city_models

CITIES = ["abuja", "lagos", "kano", "port_harcourt", "ibadan", "osogbo"]


def main():
    parser = argparse.ArgumentParser(description="Train XGBoost AQI forecast models")
    parser.add_argument("--city", type=str, default=None, help="Train single city only")
    args = parser.parse_args()

    cities = [args.city] if args.city else CITIES
    started_at = datetime.now(timezone.utc)

    logger.info(f"═══════════════════════════════════════")
    logger.info(f"BreatheSafe NG — XGBoost Training Run")
    logger.info(f"Cities: {cities}")
    logger.info(f"═══════════════════════════════════════")

    all_results = {}

    for city in cities:
        metrics = train_city_models(city)
        all_results[city] = metrics

    # Save training summary
    summary = {
        "started_at":    started_at.isoformat(),
        "completed_at":  datetime.now(timezone.utc).isoformat(),
        "cities":        cities,
        "results":       all_results,
    }

    summary_path = ML_ROOT / "artifacts" / f"training_summary_{started_at.strftime('%Y%m%d_%H%M')}.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary table
    logger.info("\n═══ Training Summary ═══")
    logger.info(f"{'City':<15} {'Horizon':<10} {'MAE':<10} {'RMSE':<10} {'Cat Acc':<10}")
    logger.info("-" * 55)
    for city, city_metrics in all_results.items():
        for m in city_metrics:
            logger.info(
                f"{m['city']:<15} {str(m['horizon_hours'])+'h':<10} "
                f"{m['mae']:<10} {m['rmse']:<10} {str(m['category_accuracy'])+'%':<10}"
            )

    logger.success(f"Training complete. Summary saved to {summary_path}")


if __name__ == "__main__":
    main()