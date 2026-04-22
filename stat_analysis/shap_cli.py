import logging
import os
import readline
import sys

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from config import CHARACTER, SUPPORTED_BUILD_IDS, get_model_path

# Add the project root to sys.path to allow imports from stat_analysis
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from item_scrapper.items import (
    ALL_CARDS,
    ALL_ENCOUNTERS,
    COLORLESS_CARDS,
    EVENT_CARDS,
    POTIONS,
    RELICS,
)
from stat_analysis.preprocess import GLOBAL_VECTORIZER, LoadRuns
from stat_analysis.train import HurdleModel

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SHAPCompleter:
    def __init__(self, commands, items):
        self.commands = sorted(commands)
        self.items = sorted(items)
        # Create a list of item IDs both with and without prefix for convenience
        self.short_items = sorted(
            [i.split(".", 1)[1] if "." in i else i for i in self.items]
        )
        self.all_options = sorted(
            list(set(self.commands + self.items + self.short_items))
        )

    def complete(self, text, state_idx):
        if state_idx == 0:
            if text:
                upper_text = text.upper()
                self.matches = [
                    s for s in self.all_options if s.upper().startswith(upper_text)
                ]
            else:
                self.matches = self.commands
        try:
            return self.matches[state_idx]
        except (IndexError, AttributeError):
            return None


class SHAPExplorer:
    def __init__(self, character=CHARACTER, model_path=None):
        self.character = character
        if model_path is None:
            model_path = f"models/hurdle_model_{character}.joblib"
        self.model_path = model_path
        self.model = None
        self.x_df = None
        self.explainer_clf = None
        self.explainer_reg = None
        self.shap_values_clf = None
        self.shap_values_reg = None

        self.filters = {
            "show_relics": False,
            "show_potions": False,
            "show_colorless": True,
            "show_encounters": False,
        }

    def load(self):
        if not os.path.exists(self.model_path):
            logger.error(f"Model file not found: {self.model_path}")
            return False

        logger.info(f"Loading model from {self.model_path}")
        # Need HurdleModel in namespace for joblib
        try:
            self.model = joblib.load(self.model_path)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

        logger.info("Loading data for SHAP evaluation...")
        runs_dir = "data/runs"
        build_id = "v0.102.0"
        if os.path.exists(runs_dir):
            versions = sorted([d for d in os.listdir(runs_dir) if d.startswith("v")])
            versions = [
                v
                for v in versions
                if any(supported in v for supported in SUPPORTED_BUILD_IDS)
            ]
            print(versions)
            build_id = versions

        loader = LoadRuns(
            character=self.character, ascension=[7, 8, 9, 10], build_id=build_id
        )
        data = loader.get_hurdle_train_test_set(test_size=0.5)
        if data[1] is None:
            logger.error("No data found to evaluate.")
            return False
        x_test = data[1]

        feature_names = GLOBAL_VECTORIZER.get_feature_names_out()
        self.x_df = pd.DataFrame(x_test.toarray(), columns=feature_names)

        logger.info("Computing SHAP values (TreeExplainer is usually fast)...")
        self.explainer_clf = shap.TreeExplainer(self.model.clf)
        self.shap_values_clf = self.explainer_clf.shap_values(self.x_df)
        if isinstance(self.shap_values_clf, list):
            self.shap_values_clf = self.shap_values_clf[1]

        self.explainer_reg = shap.TreeExplainer(self.model.reg_mean)
        self.shap_values_reg = self.explainer_reg.shap_values(self.x_df)

        logger.info("SHAP Explorer ready.")
        return True

    def get_filtered_df_and_shap(self, component="reg"):
        shap_values = (
            self.shap_values_reg if component == "reg" else self.shap_values_clf
        )
        df = self.x_df.copy()

        cols_to_keep = []
        for col in df.columns:
            if col.startswith("RELIC.") and not self.filters["show_relics"]:
                continue
            if col.startswith("POTION.") and not self.filters["show_potions"]:
                continue
            if col.startswith("ENCOUNTER") and not self.filters["show_encounters"]:
                continue
            if col.startswith("CARD."):
                base_name = col.rstrip("+")
                if base_name in COLORLESS_CARDS and not self.filters["show_colorless"]:
                    continue
            cols_to_keep.append(col)

        indices = [list(df.columns).index(c) for c in cols_to_keep]
        filtered_df = df[cols_to_keep]
        filtered_shap = shap_values[:, indices]
        return filtered_df, filtered_shap

    def plot_beeswarm(self, component="reg"):
        df, sv = self.get_filtered_df_and_shap(component)

        # Add non-zero counts to feature names for better visibility of sparsity
        total_rows = len(df)
        new_columns = []
        for col in df.columns:
            nz = (df[col] != 0).sum()
            new_columns.append(f"{col.lower()} ({nz}/{total_rows - nz})")
        df.columns = new_columns

        plt.figure(figsize=(14, 10))
        # shap.plots.beeswarm expects an Explanation object for some versions,
        # but summary_plot is often more robust for older SHAP.
        shap.summary_plot(sv, df, show=False)
        plt.title(f"Beeswarm Plot - {component.upper()} - {self.character}")
        plt.tight_layout()
        plt.show()

    def plot_summary(self, component="reg"):
        df, sv = self.get_filtered_df_and_shap(component)

        # Add non-zero counts to feature names for better visibility of sparsity
        total_rows = len(df)
        new_columns = []
        for col in df.columns:
            nz = (df[col] != 0).sum()
            new_columns.append(f"{col} (nz: {nz}, z: {total_rows - nz})")
        df.columns = new_columns

        plt.figure(figsize=(14, 10))
        shap.summary_plot(sv, df, plot_type="bar", show=False)
        plt.title(f"Global Feature Importance - {component.upper()} - {self.character}")
        plt.tight_layout()
        plt.show()

    def resolve_feature_name(self, feature):
        if feature in self.x_df.columns:
            return feature

        upper = feature.upper()
        for prefix in ["CARD.", "RELIC.", "POTION.", "ENCOUNTER."]:
            if f"{prefix}{upper}" in self.x_df.columns:
                return f"{prefix}{upper}"
        return None

    def plot_dependence(self, feature, component="reg", interaction_feature=None):
        feat_name = self.resolve_feature_name(feature)
        if not feat_name:
            print(f"Feature '{feature}' not found.")
            return

        shap_values = (
            self.shap_values_reg if component == "reg" else self.shap_values_clf
        )

        inter_feat_name = None
        if interaction_feature:
            inter_feat_name = self.resolve_feature_name(interaction_feature)
            if not inter_feat_name:
                print(
                    f"Interaction feature '{interaction_feature}' not found. Using auto."
                )
                inter_feat_name = "auto"

        plt.figure(figsize=(12, 8))
        shap.dependence_plot(
            feat_name,
            shap_values,
            self.x_df,
            interaction_index=inter_feat_name if inter_feat_name else "auto",
            show=False,
        )
        plt.title(f"Dependence Plot: {feat_name} ({component.upper()})")
        plt.tight_layout()
        plt.show()

    def show_top_related(self, feature, n=10):
        feat_name = self.resolve_feature_name(feature)
        if not feat_name:
            print(f"Feature '{feature}' not found.")
            return

        # Correlation in data space
        corr = (
            self.x_df.corrwith(self.x_df[feat_name]).abs().sort_values(ascending=False)
        )
        print(f"\nTop {n} features correlated with {feat_name} in data:")
        for name, val in corr.head(n + 1).items():
            if name == feat_name:
                continue
            print(f"  {name:<30} | {val:.4f}")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--char",
        type=str,
        choices=list(config.CHARACTER_CONFIGS.keys()),
        default=CHARACTER,
    )
    parser.add_argument("--model", type=str, default=None)
    args = parser.parse_args()

    if args.char:
        config.CHARACTER = args.char

    m_path = args.model if args.model else config.get_model_path()
    explorer = SHAPExplorer(character=config.CHARACTER, model_path=m_path)
    if not explorer.load():
        return

    commands = [
        "beeswarm",
        "summary",
        "depend",
        "interact",
        "top",
        "filter",
        "help",
        "quit",
    ]
    item_list = (
        list(ALL_CARDS.keys())
        + list(RELICS.keys())
        + list(POTIONS.keys())
        + list(ALL_ENCOUNTERS.keys())
    )

    completer = SHAPCompleter(commands, item_list)
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")

    print(f"\nSHAP Interactive Explorer - Character: {explorer.character}")
    print(
        "Commands: beeswarm, summary, depend <item>, interact <item1> <item2>, top <item>, filter, help, quit"
    )

    while True:
        try:
            line = input(f"({explorer.character}) SHAP> ").strip()
            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()

            if cmd == "quit":
                break
            elif cmd == "help":
                print("\nAvailable Commands:")
                print(
                    "  beeswarm [clf|reg]                - Show beeswarm plot (reg is default)"
                )
                print(
                    "  summary [clf|reg]                 - Show global importance bar plot"
                )
                print(
                    "  depend <item> [clf|reg]           - Show dependency plot for an item"
                )
                print(
                    "  interact <item1> <item2> [clf|reg]- Show interaction/dependency between two items"
                )
                print(
                    "  top <item>                        - Show features highly correlated with item in data"
                )
                print(
                    "  filter <key> <on|off>             - Toggle filters (relics, potions, colorless, encounters)"
                )
                print("  quit                              - Exit")
            elif cmd == "beeswarm":
                comp = parts[1].lower() if len(parts) > 1 else "reg"
                explorer.plot_beeswarm(comp)
            elif cmd == "summary":
                comp = parts[1].lower() if len(parts) > 1 else "reg"
                explorer.plot_summary(comp)
            elif cmd == "depend":
                if len(parts) < 2:
                    print("Usage: depend <item> [clf|reg]")
                    continue
                item = parts[1]
                comp = parts[2].lower() if len(parts) > 2 else "reg"
                explorer.plot_dependence(item, comp)
            elif cmd == "interact":
                if len(parts) < 3:
                    print("Usage: interact <item1> <item2> [clf|reg]")
                    continue
                item1 = parts[1]
                item2 = parts[2]
                comp = parts[3].lower() if len(parts) > 3 else "reg"
                explorer.plot_dependence(item1, comp, interaction_feature=item2)
            elif cmd == "top":
                if len(parts) < 2:
                    print("Usage: top <item>")
                    continue
                explorer.show_top_related(parts[1])
            elif cmd == "filter":
                if len(parts) < 3:
                    print(f"Current filters: {explorer.filters}")
                    print(
                        "Usage: filter <relics|potions|colorless|encounters> <on|off>"
                    )
                    continue
                target = parts[1].lower()
                if target == "colorless":
                    key = "show_colorless"
                elif target == "relics":
                    key = "show_relics"
                elif target == "potions":
                    key = "show_potions"
                elif target == "encounters":
                    key = "show_encounters"
                else:
                    print(f"Unknown filter: {target}")
                    continue

                explorer.filters[key] = parts[2].lower() == "on"
                print(f"Filter {key} set to {explorer.filters[key]}")
            else:
                print(f"Unknown command: {cmd}")
        except KeyboardInterrupt:
            print("\nUse 'quit' to exit.")
        except EOFError:
            break
        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)


if __name__ == "__main__":
    main()
