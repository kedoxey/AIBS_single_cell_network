import pandas as pd
import numpy as np
import json


# models to use from DataFrame
flag = 'AA'  # 'TEST', 'AA', 'PS', or 'ALL'
num_models = 2  # if 'TEST' specify number of all-active models

both_df = pd.read_pickle('both_models_df')
both_AA_ids = list(both_df['all-active model id'].values)
both_PS_ids = list(both_df['perisomatic model id'].values)

with open('node_sets.json') as json_file:
    node_sets = json.load(json_file)

if flag in 'TEST':
    # both_ids = [both_AA_ids[0]]
    # first_row = both_df.iloc[0]
    both_ids = both_AA_ids[:num_models]
    test_rows = both_df.iloc[:num_models, :]
    rheobases = np.unique(test_rows['rheobase'].values)
else:
    if flag in 'AA':
        both_ids = both_AA_ids
    elif flag in 'PS':
        both_ids = both_PS_ids
    else:
        both_ids = both_AA_ids + both_PS_ids
    rheobases = np.unique(both_df['rheobase'].values)

rheobase_models = {str(rheobase): [] for rheobase in rheobases}

for i, id in enumerate(both_ids):
    df_row = both_df.loc[(both_df['all-active model id'] == id) | (both_df['perisomatic model id'] == id)]
    rheobase = str(df_row['rheobase'].item())
    rheobase_models[rheobase].append(i)

for rheobase, models in rheobase_models.items():
    name = f"rheobase-{rheobase}"
    node_sets[name] = {"population": "single_cells", "node_type_id": models}

print(f"NODE SETS BUILT FOR {flag} MODELS")

with open('node_sets.json', 'w') as json_file:
    json.dump(node_sets, json_file, indent=4)
