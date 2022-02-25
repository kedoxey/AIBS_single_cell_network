import pandas
import xml.etree.ElementTree as ET

ET.register_namespace('', 'http://www.neuroml.org/schema/neuroml2')

nml2_cell_dir = 'biophysical_neuron_templates'

both_models_file = '/Users/katedoxey/Desktop/research/visual_vergil/parse_models/both_models_df'
both_df = pandas.read_pickle(both_models_file)
perisomatic_model_ids = list(pandas.to_numeric(both_df['perisomatic model id']))

neuronal_model_ids = perisomatic_model_ids
# neuronal_model_ids = [486557284, 471085845, 478513187, 478810017, 473871592, 480631402]

for perisomatic_id in neuronal_model_ids:
    cell_file = f'Cell_{perisomatic_id}.cell.nml'

    cell_loc = f'{nml2_cell_dir}/{cell_file}'

    tree = ET.parse(cell_loc)
    root = tree.getroot()

    resist = root.find('{*}cell/{*}biophysicalProperties/{*}intracellularProperties/{*}resistivity')

    resist.set('segmentGroup', 'all')

    tree.write(cell_loc)
