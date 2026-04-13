import os

import joblib
from xgboost import XGBRegressor

from stat_analysis.preprocess import LoadRuns


class Trainer:
    def __init__(self, build_id="v0.102.0", character="*", ascension=None):
        self.build_id = build_id
        self.character = character
        self.ascension = ascension or [7, 8, 9, 10]
        self.model = None

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


def main():
    trainer = Trainer()
    x_train, x_test, y_train, y_test = trainer.load_data()

    if x_train is None:
        print("Error: No data found.")
        return

    params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "max_depth": 10,
        "n_estimators": 6000,
        "colsample_bytree": 0.2,
        "subsample": 0.8,
        "learning_rate": 0.03,
        "tree_method": "hist",
    }

    # Train
    trainer.train(x_train, y_train, **params)
    model_path = "models/xgb_model.joblib"
    trainer.save_model(model_path)


if __name__ == "__main__":
    main()
