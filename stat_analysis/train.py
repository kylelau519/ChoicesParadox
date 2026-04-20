import logging
import os

import joblib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from xgboost import XGBClassifier, XGBRegressor

from item_scrapper.items import SUPPORTED_BUILD_IDS
from stat_analysis.preprocess import LoadRuns

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class HurdleModel:
    def __init__(self, clf, reg_mean, reg_low, reg_high):
        self.clf = clf
        self.reg_mean = reg_mean
        self.reg_low = reg_low
        self.reg_high = reg_high

    def predict(self, X):
        # P(y > 0)
        p_damage = self.clf.predict_proba(X)[:, 1]
        # E[y | y > 0] for different cases
        mean_cond = self.reg_mean.predict(X)
        low_cond = self.reg_low.predict(X)
        high_cond = self.reg_high.predict(X)

        # Combined predictions: E[y] = P(y > 0) * E[y | y > 0]
        return {
            "mean": p_damage * mean_cond,
            "low": p_damage * low_cond,
            "high": p_damage * high_cond,
        }


class HurdleTrainer:
    def __init__(
        self,
        build_id=None,
        character="*",
        ascension=None,
        suffix="",
        model_path=None,
    ):
        if build_id is None:
            # Find all versions in data/runs
            runs_dir = "data/runs"
            if os.path.exists(runs_dir):
                self.build_id = sorted(
                    [
                        d
                        for d in os.listdir(runs_dir)
                        if os.path.isdir(os.path.join(runs_dir, d))
                        and d.startswith("v")
                        and any(v in d for v in SUPPORTED_BUILD_IDS)
                    ]
                )
            else:
                self.build_id = "v0.102.0"
        else:
            self.build_id = build_id
        self.character = character
        self.ascension = ascension or [7, 8, 9, 10]
        self.model = None
        self.suffix = suffix
        if model_path:
            self.model_path = model_path
        else:
            self.model_path = f"models/hurdle_model_{self.suffix}.joblib"

    def load_data(self, test_size=0.2):
        loader = LoadRuns(self.character, self.ascension, self.build_id)
        return loader.get_hurdle_train_test_set(test_size=test_size)

    def train(
        self,
        x_clf_train,
        y_clf_train,
        x_reg_train,
        y_reg_train,
        clf_params,
        reg_params,
        low_alpha=0.1,
        high_alpha=0.9,
    ):
        print(f"Training Classifier with params: {clf_params}")
        clf = XGBClassifier(**clf_params)
        clf.fit(x_clf_train, y_clf_train)

        print(f"Training Mean Regressor with params: {reg_params}")
        reg_mean = XGBRegressor(**reg_params)
        reg_mean.fit(x_reg_train, y_reg_train)

        print(f"Training Low Regressor (alpha={low_alpha})")
        low_params = reg_params.copy()
        low_params["objective"] = "reg:quantileerror"
        low_params["quantile_alpha"] = low_alpha
        # Tweedie specific params might not be compatible with quantile
        low_params.pop("tweedie_variance_power", None)
        reg_low = XGBRegressor(**low_params)
        reg_low.fit(x_reg_train, y_reg_train)

        print(f"Training High Regressor (alpha={high_alpha})")
        high_params = reg_params.copy()
        high_params["objective"] = "reg:quantileerror"
        high_params["quantile_alpha"] = high_alpha
        high_params["max_depth"] = 4
        high_params.pop("tweedie_variance_power", None)
        reg_high = XGBRegressor(**high_params)
        reg_high.fit(x_reg_train, y_reg_train)

        self.model = HurdleModel(clf, reg_mean, reg_low, reg_high)
        return self.model

    def save_model(self, path=None):
        if path is None:
            path = self.model_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        print(f"Model saved to {path}")

    def test_model(self, x_test, y_test, model_path=None):
        if model_path is None:
            model_path = self.model_path
            self.model = joblib.load(model_path)
        if self.model is None:
            raise ValueError("Model has not been trained yet.")

        # For testing, we use the combined test set (all samples)
        preds = self.model.predict(x_test)
        y_pred_mean = preds["mean"]
        y_pred_low = preds["low"]
        y_pred_high = preds["high"]

        # Classifier scores (probabilities for class 1: damage taken)
        y_clf_probs = self.model.clf.predict_proba(x_test)[:, 1]
        y_clf_scores = 2 * y_clf_probs - 1
        y_clf_true = (y_test > 0).astype(int)

        # Calculate metrics for mean prediction
        mae = mean_absolute_error(y_test, y_pred_mean)
        mse = mean_squared_error(y_test, y_pred_mean)
        rmse = mse**0.5
        r2 = r2_score(y_test, y_pred_mean)

        print("\n--- Hurdle Model Regression Report (Mean) ---")
        print(f"Mean Absolute Error (MAE): {mae:.4f}")
        print(f"Mean Squared Error (MSE):  {mse:.4f}")
        print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
        print(f"R-squared (R2): {r2:.4f}")

        # Coverage for low/high
        damage_mask = y_test > 0

        if np.sum(damage_mask) > 0:
            coverage = np.mean(
                (y_test[damage_mask] >= y_pred_low[damage_mask])
                & (y_test[damage_mask] <= y_pred_high[damage_mask])
            )
        else:
            coverage = 0.0  # Fallback if test set somehow has zero damage taken
        print(f"True Interval Coverage (Low to High): {coverage:.4f}")

        # Also report classifier performance
        y_clf_pred = self.model.clf.predict(x_test)
        acc = accuracy_score(y_clf_true, y_clf_pred)
        print(f"Classifier Accuracy: {acc:.4f}")

        # Plotting
        os.makedirs("reports", exist_ok=True)
        sns.set_theme(style="whitegrid")

        # 1. Residuals (Mean)
        residuals = y_pred_mean - y_test
        plt.figure(figsize=(10, 6))
        sns.histplot(residuals, kde=True, color="green")
        plt.title("Hurdle Model: Histogram of Residuals (Mean)")
        plt.savefig(f"reports/hurdle_residuals_{self.suffix}.png")

        # 2. Predicted vs Actual (Mean) with error bars or area?
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred_mean, alpha=0.3, label="Mean Prediction")
        # Sample some points to show low/high intervals
        idx = np.random.choice(len(y_test), min(100, len(y_test)), replace=False)
        plt.vlines(
            y_test[idx],
            y_pred_low[idx],
            y_pred_high[idx],
            color="gray",
            alpha=0.2,
            label="Low-High Interval",
        )

        plt.plot(
            [y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", lw=2
        )
        plt.xlabel("Actual")
        plt.ylabel("Predicted")
        plt.title("Hurdle Model: Predicted (Mean) vs Actual")
        plt.legend()
        plt.savefig(f"reports/hurdle_pred_vs_actual_{self.suffix}.png")

        # 3. Classifier Separation (-1 to 1 score)
        plt.figure(figsize=(12, 6))
        sns.histplot(
            x=y_clf_scores[y_clf_true == 0],
            label="Flawless (Actual y=0)",
            color="blue",
            kde=True,
            element="step",
            alpha=0.5,
            bins=10,
        )
        sns.histplot(
            x=y_clf_scores[y_clf_true == 1],
            label="Damage Taken (Actual y>0)",
            color="red",
            kde=True,
            element="step",
            alpha=0.5,
            bins=10,
        )
        plt.axvline(0, color="black", linestyle="--", label="Threshold (p=0.5)")
        plt.title("Classifier Separation (Score Range -1 to 1)")
        plt.xlabel("Score (-1: Flawless Probable, 1: Damage Probable)")
        plt.ylabel("Frequency")
        plt.legend()
        plt.savefig(f"reports/hurdle_clf_separation_{self.suffix}.png")

        # 4. Confusion Matrix
        cm = confusion_matrix(y_clf_true, y_clf_pred, normalize="true")
        plt.figure(figsize=(8, 6))
        disp = ConfusionMatrixDisplay(
            confusion_matrix=cm, display_labels=["Flawless", "Damage"]
        )
        disp.plot(cmap="Blues", values_format=".2%")
        plt.title("Hurdle Classifier: Confusion Matrix (%)")
        plt.grid(False)
        plt.savefig(f"reports/hurdle_confusion_matrix_{self.suffix}.png")

        plt.close("all")
        return y_pred_mean


def main():
    character = "necrobinder"
    trainer = HurdleTrainer(
        ascension=[7, 8, 9, 10], suffix=character, character=character
    )
    print(f"Loading data for build_ids: {trainer.build_id}")
    data = trainer.load_data()
    if data[0] is None:
        print("Error: No data found.")
        return

    (
        x_train,
        x_test,
        y_train,
        y_test,
        y_clf_train,
        y_clf_test,
        x_reg_train,
        x_reg_test,
        y_reg_train,
        y_reg_test,
    ) = data

    clf_params = {
        "max_depth": 5,
        "n_estimators": 1000,
        "learning_rate": 0.03,
        "tree_method": "hist",
    }

    reg_params = {
        "objective": "reg:tweedie",
        "max_depth": 5,  # DECREASED: Trees don't need to be as deep anymore
        "n_estimators": 1500,  # Kept high (Relies on early stopping)
        "learning_rate": 0.03,  # Kept low
        "tree_method": "hist",
        "min_child_weight": 3,  # DECREASED: Adjusted for the smaller dataset
        # "colsample_bytree": 0.8,  # INCREASED: Less need to hide features
        # "subsample": 0.8,  # NEW: Prevents overfitting the smaller dataset
    }

    # Train
    trainer.train(
        y_clf_train=y_clf_train,
        x_clf_train=x_train,
        y_reg_train=y_reg_train,
        x_reg_train=x_reg_train,
        clf_params=clf_params,
        reg_params=reg_params,
    )
    trainer.save_model()

    # Test and Report
    trainer.test_model(x_test, y_test, model_path=trainer.model_path)


if __name__ == "__main__":
    main()
