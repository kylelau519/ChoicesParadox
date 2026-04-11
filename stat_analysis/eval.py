# Evaluator class for evaluating the performance of a trained model and answering questions about feature importance and predictions.

import joblib
import numpy as np
from sklearn.metrics
from stat_analysis.preprocess import GLOBAL_VECTORIZER


class Evaluator:
    def __init__(self, model_path: str, map_point_history: MapPointHistory):
        self.model = joblib.load(model_path)
        self.vectorizer = GLOBAL_VECTORIZER

    def predict(self, x):
        y_pred = self.model.predict(x)
        return y_pred

    def report_feature_importance(self, top_n=20):
        if not hasattr(self.model, "feature_importances_"):
            print("Model does not support feature importance.")
            return

        importance = self.model.feature_importances_
        feature_names = self.vectorizer.get_feature_names_out()
        indices = np.argsort(importance)[::-1][:top_n]

        print(f"\n--- Top {top_n} Important Features ---")
        for i in indices:
            if importance[i] > 0:
                print(f"{feature_names[i]}: {importance[i]:.4f}")



    # prob to win the act
    # prob to win against an ecounter
