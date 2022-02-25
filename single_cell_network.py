import pandas as pd
import numpy as np
import json
import os

from allensdk.api.queries.cell_types_api import CellTypesApi

from bmtk.builder import NetworkBuilder
from bmtk.builder.bionet import SWCReader
from bmtk.builder.auxi.node_params import positions_columinar, xiter_random

import yaml
from yaml.loader import Loader

from netpyne import sim
from netpyne.conversion import sonataImport
import matplotlib.pyplot as plt
import re


def add_simulation_inputs(flag, num_models, scale):
    # models to use from DataFrame
    # flag = 'AA'  # 'TEST', 'AA', 'PS', or 'ALL'
    # num_models = 2  # if 'TEST' specify number of all-active models

    both_df = pd.read_pickle('both_models_df')

    if flag in 'TEST':
        test_rows = both_df.iloc[0:num_models, :]
        rheobases = list(test_rows['rheobase'].values)
    else:
        rheobases = np.unique(both_df['rheobase'].values)

    with open('simulation_config.json') as json_file:
        simulation_config = json.load(json_file)

    inputs = {}

    # scale = float(input('Enter amplitude scale:'))
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

    temp = 5


def build_node_sets(flag, num_models):
    # models to use from DataFrame
    # flag = 'AA'  # 'TEST', 'AA', 'PS', or 'ALL'
    # num_models = 2  # if 'TEST' specify number of all-active models

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


def build_network(flag, num_models):
    # models to use from DataFrame
    # flag = 'AA'  # 'TEST', 'AA', 'PS', or 'ALL'
    # num_models = 2  # if 'TEST' specify number of all-active models
    #
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


def is_valid_spike(Vm, threshold):
    if np.max(Vm) > threshold:
        return True
    else:
        return False


def run(out_dir):
    rootFolder = os.path.abspath('.')
    # outFolder = os.path.abspath('output')+'/'
    sonataConfigFile = rootFolder+'/config.json'

    print('Loading SONATA network from %s' % sonataConfigFile)

    sonataImporter = sonataImport.SONATAImporter()
    sonataImporter.importNet(sonataConfigFile, replaceAxon=True, setdLNseg=True)

    sim.cfg.recordTraces = {'V_soma': {'sec': 'soma_0', 'loc': 0.5, 'var': 'v'}}
    sim.cfg.recordCells = ['all']
    sim.cfg.recordSpikeGids = [-1]
    # sim.cfg.recordLFP = rec_electorde
    # sim.cfg.pt3dRelativeToCellLocation = False  # makes grid as function from soma location
    # sim.cfg.invertedYCoord = False  # make y-axis coordinate negative so it represents depth with 0 at top
    sim.cfg.analysis['plotTraces'] = {'include': ['all'], 'saveFig': True}  # needed for 9 cell example
    sim.cfg.cache_efficient = True

    sim.setupRecording()
    sim.runSim()

    data = sim.gatherData()
    # all_data = sim.allSimData
    cells = sim.net.cells

    # spikes = sim.analysis.utils.getSpktSpkid([0, 1])

    valid_spikes = {'failed_aa': 0, 'failed_ps': 0}
    spike_threshold = -30  # -15  # mV

    # scaling_factor = float(input('Enter scaling factor:'))
    # test_dir = 'ps_scale_2_5_dur_1050'

    if not os.path.exists(f'output/{out_dir}'):
        os.makedirs(f'output/{out_dir}')

    t = np.array(data['t'])
    columns = ['cell_id', 'model_id', 't', 'Vm', 'did_spike', 'first_spike']
    waveforms_df = pd.DataFrame(columns=columns)

    cell_count = 0

    for cell_id, cell_Vm in data['V_soma'].items():
        Vm = np.array(cell_Vm)

        gid = int(re.findall('[0-9]+', cell_id)[0])
        cell = cells[gid]
        model_id = cell.tags['cellType']
        model_type = 'aa' if 'all-active' in model_id else 'ps'

        is_valid = is_valid_spike(Vm, spike_threshold)
        valid_spikes[f"{cell_id}-{model_type}"] = is_valid
        if not is_valid:
            valid_spikes[f"failed_{model_type}"] += 1

        try:
            first_spike_idx = data['spkid'].index(gid)
        except:
            print(f"cell_{gid}-{model_type} did not spike! Default to cell_0 spike time.")
            first_spike_idx = 0

        first_spike = np.array(data['spkt'])[first_spike_idx]
        t_lower = first_spike - 2
        t_upper = first_spike + 8
        t_interval = (t >= t_lower) & (t <= t_upper)
        t_10 = t[t_interval]
        Vm_10 = Vm[t_interval]

        cell_row = {'cell_id': cell_id,
                    'model_id': model_id,
                    't': t,
                    'Vm': Vm,
                    'did_spike': is_valid,
                    'first_spike': first_spike}
        waveforms_df = waveforms_df.append(cell_row, ignore_index=True)

        fig, axs = plt.subplots(2)
        fig.suptitle(f'{cell_id}, {model_id}')
        axs[0].plot(t, np.array(Vm))
        axs[1].plot(t_10, Vm_10)
        axs[1].set_xlabel('t (ms)')

        for ax in axs:
            ax.set_ylabel('Vm')

        fig.savefig(f'output/{out_dir}/{cell_id}-{model_type}-trace.png')

        cell_count += 1

    waveforms_df.to_pickle(f'output/{out_dir}/waveforms_df.pkl', protocol=3)

    f = open(f'output/{out_dir}/valid_spikes_{out_dir}.yaml', 'w+')
    yaml.dump(valid_spikes, f, allow_unicode=True)
