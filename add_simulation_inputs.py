import pandas as pd
import numpy as np
import json


# models to use from DataFrame
flag = 'AA'  # 'TEST', 'AA', 'PS', or 'ALL'
num_models = 2  # if 'TEST' specify number of all-active models

both_df = pd.read_pickle('both_models_df')

if flag in 'TEST':
    test_rows = both_df.iloc[0:num_models, :]
    rheobases = list(test_rows['rheobase'].values)
else:
    rheobases = np.unique(both_df['rheobase'].values)

with open('simulation_config.json') as json_file:
    simulation_config = json.load(json_file)

inputs = {}

scale = float(input('Enter amplitude scale:'))
# scale = 0.0023

for rheobase in rheobases:
    name = f"IClamp{rheobase}"
    inputs[name] = {"input_type": "current_clamp",
                    "module": "IClamp",
                    "delay": 1000,
                    "duration": 50,
                    "amp": rheobase*scale,
                    "node_set": f"rheobase-{rheobase}"}

simulation_config['inputs'] = inputs

print(f"SIMULATION INPUTS ADDED FOR {flag} MODELS WITH SCALE {scale}!")

with open('simulation_config.json', 'w') as json_file:
    json.dump(simulation_config, json_file, indent=4)
