## file for boost decision tree
# Input format for bdt onehot:
# current HP, max hp, [deck count vectorize], [potion count vectorize], [relic onehot](), [encounter onehot],
# Target: damage taken in the encounter
import json

import joblib
import numpy as np
import scipy.sparse as sp
import sklearn
from stat_analysis.preprocess import RunToInputConverter
from xgboost import XGBRegressor

build_id = "v0.102.0"
ascension = [7, 8, 9, 10]
character = "silent"

data_dirs = [f"../data/runs/{build_id}/{character}/a{a}/" for a in ascension]

import glob
import os

runs = []
for data_dir in data_dirs:
    # Resolve the relative path to an absolute path for globbing
    abs_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), data_dir))
    runs.extend(glob.glob(f"{abs_data_dir}/**/*.run", recursive=True))

all_X_matrices = []
all_y_arrays = []
length = 0
for run in runs:
    converter = RunToInputConverter.from_file(run)
    x, y = converter.vectorize()
    if x is not None and y is not None:
        all_X_matrices.append(x)
        all_y_arrays.append(y)
        length += x.shape[0]

x_final_train = sp.vstack(all_X_matrices, format="csr")
y_final_train = np.concatenate(all_y_arrays)


bdt = XGBRegressor(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
)
bdt.fit(x_final_train, y_final_train)

# Define the model save path
models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))
os.makedirs(models_dir, exist_ok=True)
model_path = os.path.join(models_dir, "xgb_model.joblib")

# Save the trained model
joblib.dump(bdt, model_path)
print(f"Model saved to {model_path}")
