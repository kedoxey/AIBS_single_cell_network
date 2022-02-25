import json
import sys

with open("simulation_config.json", "r") as jsonFile:
    sim_data = json.load(jsonFile)

scaling_factor = float(input('Enter scaling factor:'))
# scaling_factor = float(sys.argv[1])

for _, iclamp_config in sim_data['inputs'].items():
    rheobase = int(iclamp_config['node_set'].split('-')[1])
    scaled_amp = scaling_factor * rheobase

    iclamp_config['amp'] = scaled_amp

with open("simulation_config.json", "w") as jsonFile:
    json.dump(sim_data, jsonFile, indent=4)
