# AIBS_single_cell_network

Code to simulate all-active and perisomatic models from the Allen Institute using NetPyNE.

## Quick Run
### batch_testing.py
In the script, specify number of simulations (num_runs), type of models (flags = 'TEST', 'AA', 'PS', 'ALL') for testing, all-active, perisomatic, or all, number of models if a testing run (num_models) and 0 if not, name of output directories (out_dirs), and the scale of simulation input's current (scales) (0.001 x scale). Specify these parameters as a list, repeat if necessary for more than one simulation.

#### Example
num_runs = 2  
flags = ['TEST', 'AA']  
num_models = [3, 0]  
out_dirs = ['testing_scale_2', 'aa_scale_1']  
scales = [0.002, 0.001]

## Longer Run
Scripts in order
### add_simulation_inputs.py
In the script, specify type of models (flag = 'TEST', 'AA', 'PS', 'ALL') and number of models if a test run. The script will prompt you for the simulation's input current scale, which is 0.001 x scale.

## build_node_sets.py
In the script, specify type of models (flag = 'TEST', 'AA', 'PS', 'ALL') and number of models if a test run.

## build_network.py
In the script, specify type of models (flag = 'TEST', 'AA', 'PS', 'ALL') and number of models if a test run.

## run.py
The script will prompt you for the name of the output directory.

## Example Output
### Voltage trace
![cell_0-ps-trace](https://user-images.githubusercontent.com/22531287/155786147-15ba4159-300f-4feb-bcfa-e0612752370a.png)  
The top figure is the trace for the entire duration of 1050ms where current is injected after 1000ms and the bottom is a 10ms trace around the first valid spike. If there is not a valid spike, the bottom figure defaults to the valid spike time of the very first model in the simulation.

### valid_spikes_[out_dir].yaml
YAML file containing whether the cell spiked, based on a threshold of -30mV, and the counts of all-active and perisomatic models that did spike.

### waveforms_df.pkl
DataFrame that contains spike times and simulation and model metadata.
