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
from stat_analysis.preprocess import LoadRuns
from xgboost import XGBClassifier, XGBRegressor

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class HurdleModel:
    def __init__(self, clf, reg):
        self.clf = clf
        self.reg = reg

    def predict(self, X):
        # P(y > 0)
        p_damage = self.clf.predict_proba(X)[:, 1]
        # E[y | y > 0]
        expected_damage = self.reg.predict(X)
        # Combined prediction: E[y] = P(y > 0) * E[y | y > 0]
        return p_damage * expected_damage


class HurdleTrainer:
    def __init__(self, build_id="v0.102.0", character="*", ascension=None, suffix=""):
        self.build_id = build_id
        self.character = character
        self.ascension = ascension or [7, 8, 9, 10]
        self.model = None
        self.suffix = suffix

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
    ):
        print(f"Training Classifier with params: {clf_params}")
        clf = XGBClassifier(**clf_params)
        clf.fit(x_clf_train, y_clf_train)

        print(f"Training Regressor with params: {reg_params}")
        reg = XGBRegressor(**reg_params)
        reg.fit(x_reg_train, y_reg_train)

        self.model = HurdleModel(clf, reg)
        return self.model

    def save_model(self, path="models/hurdle_model.joblib"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        print(f"Model saved to {path}")

    def test_model(self, x_test, y_test, model_path=None):
        if model_path:
            # Ensure HurdleModel is in the namespace when loading
            self.model = joblib.load(model_path)
        if self.model is None:
            raise ValueError("Model has not been trained yet.")

        # For testing, we use the combined test set (all samples)
        y_pred = self.model.predict(x_test)

        # Classifier scores (probabilities for class 1: damage taken)
        # Shifted to -1 to 1 range: 0 -> -1, 1 -> 1
        y_clf_probs = self.model.clf.predict_proba(x_test)[:, 1]
        y_clf_scores = 2 * y_clf_probs - 1

        # Actual labels for separation analysis
        y_clf_true = (y_test > 0).astype(int)

        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = mse**0.5
        r2 = r2_score(y_test, y_pred)

        print("\n--- Hurdle Model Regression Report ---")
        print(f"Mean Absolute Error (MAE): {mae:.4f}")
        print(f"Mean Squared Error (MSE):  {mse:.4f}")
        print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
        print(f"R-squared (R2): {r2:.4f}")

        # Also report classifier performance
        y_clf_pred = self.model.clf.predict(x_test)
        acc = accuracy_score(y_clf_true, y_clf_pred)
        print(f"Classifier Accuracy: {acc:.4f}")

        # Plotting
        os.makedirs("reports", exist_ok=True)
        sns.set_theme(style="whitegrid")

        # 1. Residuals
        residuals = y_pred - y_test
        plt.figure(figsize=(10, 6))
        sns.histplot(residuals, kde=True, color="green")
        plt.title("Hurdle Model: Histogram of Residuals")
        plt.savefig(f"reports/hurdle_residuals_{self.suffix}.png")

        # 2. Predicted vs Actual
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, alpha=0.3)
        plt.plot(
            [y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", lw=2
        )
        plt.xlabel("Actual")
        plt.ylabel("Predicted")
        plt.title("Hurdle Model: Predicted vs Actual")
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
        print(
            f"Saved classifier separation plot to reports/hurdle_clf_separation_{self.suffix}.png"
        )

        # 4. Confusion Matrix
        cm = confusion_matrix(y_clf_true, y_clf_pred)
        plt.figure(figsize=(8, 6))
        disp = ConfusionMatrixDisplay(
            confusion_matrix=cm, display_labels=["Flawless", "Damage"]
        )
        disp.plot(cmap="Blues", values_format="d")
        plt.title("Hurdle Classifier: Confusion Matrix")
        plt.grid(False)
        plt.savefig(f"reports/hurdle_confusion_matrix_{self.suffix}.png")
        print(
            f"Saved confusion matrix to reports/hurdle_confusion_matrix_{self.suffix}.png"
        )

        plt.close("all")
        return y_pred


def main():
    trainer = HurdleTrainer(ascension=[3, 4, 5, 6, 7, 8, 9, 10], suffix="hurdle")
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
        "max_depth": 6,
        "n_estimators": 1000,
        "learning_rate": 0.05,
        "tree_method": "hist",
    }

    reg_params = {
        "objective": "reg:squarederror",
        "max_depth": 8,
        "n_estimators": 2000,
        "learning_rate": 0.05,
        "tree_method": "hist",
    }

    # Train
    model_path = "models/hurdle_model.joblib"
    trainer.train(
        y_clf_train=y_clf_train,
        x_clf_train=x_train,
        y_reg_train=y_reg_train,
        x_reg_train=x_reg_train,
        clf_params=clf_params,
        reg_params=reg_params,
    )
    trainer.save_model(model_path)

    # Test and Report
    trainer.test_model(x_test, y_test, model_path=model_path)


if __name__ == "__main__":
    main()
