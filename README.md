# ChoicesParadox

## Setup config
The whole repository entry point is the `config.py` file. You can modify the config file to change the training parameters, model architecture, and other settings. Both evaluator and trainer are built around the `CHARACTER` in the config file, so you can easily switch between different characters by changing the `CHARACTER` variable in the config file.

## Training BDT for each character
1. Set the `CHARACTER` variable in the `config.py` file to the desired character (e.g., "iconclad", "necrobinder", "regent").
2. Under the ChiocesParadox directory, run:
```bash
python -m stat_analysis.train
```
Your model and model report should appear in the `models/` directory after training is complete.

You may change the `EXPERIMENT_PANEL` in the config file. They are the experimental data engineering features aiming to improve the perofrmance of the BDT.

## Running Card picking Live CLI
We offer a live CLI for users to interact with the trained BDT model. This offer suggestions for card picking based on the current game state. Currently, this is experimental and will peek into the future combat.
1. Set the `CHARACTER` variable in the `config.py` file to the desired character (e.g., "iconclad", "necrobinder", "regent").
2. Make sure the `EXPERIMENT_PANEL` variable using the same with your trained BDT model.
3. In `current_run_path` variable in `config.py`, point it to the `current_run.save` file, it should be in your steam save directory. An example is uploaded in the `config.py` file.
4. Under the ChiocesParadox directory, run:
```bash
python -m main
```
5. Follow the CLI instructions to input the current game state and get card picking suggestions.


## SHAP interactive visualization
We provide an interactive SHAP visualization for the trained BDT model. This visualization allows you to explore the feature importance and how different features contribute to the model's predictions. To run the SHAP interactive visualization:
1. Set the `CHARACTER` variable in the `config.py` file to the desired character (e.g., "iconclad", "necrobinder", "regent").
2. If you are commited to the setting in the `config.py`, under the ChiocesParadox directory, run:
```bash
python -m stat_analysis.shap_cli
```
3. Or you can specify the character
```bash
python -m stat_analysis.shap_cli --char iconclad --model /path/to/your/model.joblib
```


## Tests
Run all tests recursively at project root:
```bash
./scripts/run_test.sh
```
