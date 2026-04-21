from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_ITEMS_DIR = BASE_DIR / "data" / "items"
SCRAPPER_DIR = BASE_DIR / "item_scrapper"

# Default character for UI/eval
CHARACTER = "defect"

EXPERIMENT_PANEL = {
    "group_all_curses": True,
    "correlate_upgrades": True,
    "count_potions_as_binary": False,
    "ignore_starter_relic": False,
    "ignore_health": True,
    "total_upgrades": False,
    "total_deck_size": False,
    "starter_ratio": False,
}

SUPPORTED_BUILD_IDS = ["0.102", "0.103"]
ASCENSION = [7, 8, 9, 10]

CHARACTER_CONFIGS = {
    "ironclad": {
        "clf_params": {
            "max_depth": 6,
            "n_estimators": 1000,
            "learning_rate": 0.05,
            "tree_method": "hist",
        },
        "reg_params": {
            "max_depth": 6,
            "n_estimators": 1500,
            "learning_rate": 0.05,
            "objective": "reg:tweedie",
            "tree_method": "hist",
        },
    },
    "silent": {
        "clf_params": {
            "max_depth": 5,
            "n_estimators": 1200,
            "learning_rate": 0.03,
            "tree_method": "hist",
        },
        "reg_params": {
            "max_depth": 5,
            "n_estimators": 2000,
            "learning_rate": 0.03,
            "objective": "reg:tweedie",
            "tree_method": "hist",
        },
    },
    "defect": {
        "clf_params": {
            "max_depth": 5,
            "n_estimators": 1000,
            "learning_rate": 0.04,
            "tree_method": "hist",
        },
        "reg_params": {
            "max_depth": 5,
            "n_estimators": 1500,
            "learning_rate": 0.04,
            "objective": "reg:tweedie",
            "tree_method": "hist",
        },
    },
    "necrobinder": {
        "clf_params": {
            "max_depth": 5,
            "n_estimators": 1000,
            "learning_rate": 0.03,
            "tree_method": "hist",
        },
        "reg_params": {
            "max_depth": 5,
            "n_estimators": 1500,
            "learning_rate": 0.03,
            "objective": "reg:tweedie",
            "min_child_weight": 3,
            "tree_method": "hist",
        },
    },
    "regent": {
        "clf_params": {
            "max_depth": 5,
            "n_estimators": 1000,
            "learning_rate": 0.03,
            "tree_method": "hist",
        },
        "reg_params": {
            "max_depth": 5,
            "n_estimators": 1500,
            "learning_rate": 0.03,
            "objective": "reg:tweedie",
            "tree_method": "hist",
        },
    },
}

current_run_path = "/Users/kylelau519/Library/Application Support/Steam/userdata/243023389/2868840/remote/profile1/saves/current_run.save"


def get_model_path():
    return f"{BASE_DIR}/models/hurdle_model_{CHARACTER}.joblib"
