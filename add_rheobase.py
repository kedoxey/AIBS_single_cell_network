import pandas as pd

from allensdk.api.queries.cell_types_api import CellTypesApi

both_models_file = 'both_models_df'
both_df = pd.read_pickle(both_models_file)

specimen_ids = both_df['specimen id'].values
rheobases = []

cell_types_api = CellTypesApi()

for specimen_id in specimen_ids:
    data = cell_types_api.model_query(model='EphysFeature', criteria=f'[specimen_id$eq{specimen_id}]')
    rheobases.append(int(data[0]['threshold_i_long_square']))

both_df['rheobase'] = rheobases

both_df.to_pickle(both_models_file, protocol=3)

temp = 5
