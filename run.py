from netpyne import sim
from netpyne.conversion import sonataImport
import numpy as np
import matplotlib.pyplot as plt
import os
import yaml
import pandas as pd
import re

test_dir = input('Enter output directory name:')

rootFolder = os.path.abspath('.')
outFolder = os.path.abspath('output')+'/'
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
all_data = sim.allSimData
cells = sim.net.cells

spikes = sim.analysis.utils.getSpktSpkid([0, 1])


def is_valid_spike(Vm, threshold):
    if np.max(Vm) > threshold:
        return True
    else:
        return False


valid_spikes = {'failed_aa': 0, 'failed_ps': 0}
spike_threshold = -30  # -15  # mV

# scaling_factor = float(input('Enter scaling factor:'))
# test_dir = 'ps_scale_2_5_dur_1050'

if not os.path.exists(f'output/{test_dir}'):
    os.makedirs(f'output/{test_dir}')

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

    fig.savefig(f'output/{test_dir}/{cell_id}-{model_type}-trace.png')

    cell_count += 1

waveforms_df.to_pickle(f'output/{test_dir}/waveforms_df.pkl', protocol=3)

f = open(f'output/{test_dir}/valid_spikes_{test_dir}.yaml', 'w+')
yaml.dump(valid_spikes, f, allow_unicode=True)
