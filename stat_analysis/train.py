import logging
import os

import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from stat_analysis.preprocess import GLOBAL_VECTORIZER, LoadRuns

logger = logging.getLogger(__name__)


class Trainer:
    def __init__(self, build_id="v0.102.0", character="*", ascension=None, suffix=""):
        self.build_id = build_id
        self.character = character
        self.ascension = ascension or [7, 8, 9, 10]
        self.model = None
        self.suffix = suffix

    def load_data(self, test_size=0.2):
        loader = LoadRuns(self.character, self.ascension, self.build_id)
        x_train, x_test, y_train, y_test = loader.get_train_test_set(
            test_size=test_size
        )
        return x_train, x_test, y_train, y_test

    def train(self, x_train, y_train, **params):
        self.model = XGBRegressor(**params)
        print(f"Training XGBRegressor (params={params})...")
        self.model.fit(x_train, y_train)
        return self.model

    def save_model(self, path="models/xgb_model.joblib"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        print(f"Model saved to {path}")

    def test_model(self, x_test, y_test, model_path=None):
        self.model = joblib.load(model_path) if model_path else self.model
        if self.model is None and model_path is None:
            raise ValueError("Model has not been trained yet.")

        y_pred = self.model.predict(x_test)

        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = mse**0.5
        r2 = r2_score(y_test, y_pred)

        print("\n--- Regression Report ---")
        print(f"Mean Absolute Error (MAE): {mae:.4f}")
        print(f"Mean Squared Error (MSE):  {mse:.4f}")
        print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
        print(f"R-squared (R2): {r2:.4f}")

        # Plotting
        os.makedirs("reports", exist_ok=True)
        residuals = y_pred - y_test

        # Set theme
        sns.set_theme(style="whitegrid")

        # 1. Histogram of residuals
        plt.figure(figsize=(10, 6))
        sns.histplot(residuals, kde=True, color="blue")
        plt.title("Histogram of Residuals (y_pred - y_test)")
        plt.xlabel("Residual")
        plt.ylabel("Frequency")
        plt.savefig(f"reports/residuals_histogram_{self.suffix}.png")
        print(f"Saved residuals histogram to reports/residuals_histogram.png")

        # 2. Predicted vs Actual
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, alpha=0.3)
        plt.plot(
            [y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", lw=2
        )
        plt.xlabel("Actual")
        plt.ylabel("Predicted")
        plt.title("Predicted vs Actual Values")
        plt.savefig(f"reports/predicted_vs_actual_{self.suffix}.png")
        print(f"Saved predicted vs actual plot to reports/predicted_vs_actual.png")

        plt.close("all")

        return y_pred


def main():
    trainer = Trainer(ascension=[3, 4, 5, 6, 7, 8, 9, 10])
    x_train, x_test, y_train, y_test = trainer.load_data()

    for i in range(5):
        logger.debug(
            f"Sample {i} - X: {GLOBAL_VECTORIZER.inverse_transform(x_train[i : i + 1])}, y: {y_train[i]}"
        )

    if x_train is None:
        print("Error: No data found.")
        return

    params = {
        "objective": "count:poisson",
        "eval_metric": "rmse",
        "max_depth": 10,
        "n_estimators": 6000,
        "colsample_bytree": 0.2,
        "subsample": 0.8,
        "learning_rate": 0.03,
        "tree_method": "hist",
    }

    # Train
    model_path = "models/xgb_model.joblib"
    trainer.train(x_train, y_train, **params)
    trainer.save_model(model_path)

    # Test and Report
    trainer.test_model(x_test, y_test, model_path=model_path)


if __name__ == "__main__":
    main()
