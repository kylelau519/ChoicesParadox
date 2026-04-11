## file for boost decision tree
# Input format for bdt onehot:
# current HP, max hp, [deck count vectorize], [potion count vectorize], [relic onehot](), [encounter onehot],
# Target: damage taken in the encounter
import json

import joblib
import numpy as np
import scipy.sparse as sp
import sklearn
from stat_analysis.preprocess import LoadRuns
from xgboost import XGBRegressor

build_id = "v0.102.0"
ascension = [7, 8, 9, 10]
character = "*"

runs = LoadRuns(character, ascension, build_id)
x_train, x_test, y_train, y_test = runs.get_train_test_set(test_size=0.2)

bdt = XGBRegressor(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
)
bdt.fit(x_train, y_train)
