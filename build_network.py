import os
import json
import h5py
import numpy as np


from allensdk.api.queries.cell_types_api import CellTypesApi

from bmtk.builder import NetworkBuilder
from bmtk.builder.bionet import SWCReader
from bmtk.builder.auxi.node_params import positions_columinar, xiter_random

import urllib.request
import yaml
from yaml.loader import Loader
import pandas as pd
import numpy as np

# models to use from DataFrame
flag = 'AA'  # 'TEST', 'AA', 'PS', or 'ALL'
num_models = 2  # if 'TEST' specify number of all-active models

np.random.seed(0)

with open('model_data/models.yaml') as f:
    models = yaml.load(f, Loader=Loader)

with open('model_data/specimens.yaml') as f:
    specimens = yaml.load(f, Loader=Loader)

both_df = pd.read_pickle('both_models_df')
both_AA_ids = list(both_df['all-active model id'].values)
both_PS_ids = list(both_df['perisomatic model id'].values)

morphology_files = {}

aa_cell_models = []
ps_cell_models = []

cell_types_api = CellTypesApi()

if flag in 'TEST':
    test_rows = both_df.iloc[:num_models, :]
    models_df = test_rows
else:
    models_df = both_df

for row in models_df.iterrows():
    row_items = row[1]
    specimen_id = row_items['specimen id']
    all_active_id = row_items['all-active model id']
    perisomatic_id = row_items['perisomatic model id']

    specimen = specimens[specimen_id]
    aa_model = specimen['all-active']
    ps_model = specimen['perisomatic']

    morphology_file = f"{aa_model['cre_lines']}_{aa_model['neuron_reconstruction_id']}_m"

    if not os.path.exists(f"morphologies/{morphology_file}.swc"):
        cell_types_api.save_reconstruction(int(specimen_id), f"morphologies/{morphology_file}.swc")

    if flag in ('TEST', 'AA', 'ALL'):
        aa_model_name = f"{aa_model['id']}_all-active"
        aa_model_template = f"nml:Cell_{aa_model['id']}.cell.nml"
        aa_cell_model = {'model_name': aa_model_name,
                         'ei': 'i',
                         'morphology': morphology_file,
                         'model_template': aa_model_template}
        aa_cell_models.append(aa_cell_model)

    if flag in ('PS', 'ALL'):
        ps_model_name = f"{ps_model['id']}_perisomatic"
        ps_model_template = f"nml:Cell_{ps_model['id']}.cell.nml"
        ps_cell_model = {'model_name': ps_model_name,
                         'ei': 'i',
                         'morphology': morphology_file,
                         'model_template': ps_model_template}
        ps_cell_models.append(ps_cell_model)

cell_models = aa_cell_models + ps_cell_models

morphologies = {p['model_name']: SWCReader(f"morphologies/{p['morphology']}.swc") for p in cell_models}

with open("circuit_config.json", "r") as jsonFile:
    cir_cfg_data = json.load(jsonFile)

if flag in 'TEST':
    single_cells = NetworkBuilder(f'single_cells_{num_models}')
    cir_cfg_data['networks']['nodes'] = [{'nodes_file': f'$NETWORK_DIR/single_cells_{num_models}_nodes.h5',
                                          'node_types_file': f'$NETWORK_DIR/single_cells_{num_models}_node_types.csv'}]
    print('BUILT TEST NETWORK!')
elif flag in 'AA':
    single_cells = NetworkBuilder('single_cells_aa')
    cir_cfg_data['networks']['nodes'] = [{'nodes_file': '$NETWORK_DIR/single_cells_aa_nodes.h5',
                                          'node_types_file': '$NETWORK_DIR/single_cells_aa_node_types.csv'}]
    print('BUILT ALL-ACTIVE NETWORK!')
elif flag in 'PS':
    single_cells = NetworkBuilder('single_cells_ps')
    cir_cfg_data['networks']['nodes'] = [{'nodes_file': '$NETWORK_DIR/single_cells_ps_nodes.h5',
                                          'node_types_file': '$NETWORK_DIR/single_cells_ps_node_types.csv'}]
    print('BUILT PERISOMATIC NETWORK!')
else:
    single_cells = NetworkBuilder('single_cells_all')
    cir_cfg_data['networks']['nodes'] = [{'nodes_file': '$NETWORK_DIR/single_cells_all_nodes.h5',
                                          'node_types_file': '$NETWORK_DIR/single_cells_all_node_types.csv'}]
    print('BUILT ALL NETWORK!')

with open("circuit_config.json", "w") as jsonFile:
    json.dump(cir_cfg_data, jsonFile, indent=4)

for i, model_props in enumerate(cell_models):
    n_cells = 1

    positions = positions_columinar(N=n_cells, center=[0, 10.0, 0], max_radius=50.0, height=200.0)

    single_cells.add_nodes(N=n_cells,
                           x=positions[:, 0], y=positions[:, 1], z=positions[:, 2],
                           rotation_angle_yaxis=xiter_random(N=n_cells, min_x=0.0, max_x=2*np.pi),
                           model_type='biophysical',
                           model_processing='aibs_perisomatic',
                           **model_props)

single_cells.build()
single_cells.save(output_dir='network')
