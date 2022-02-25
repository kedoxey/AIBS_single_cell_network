import single_cell_network as scn

num_runs = 2
flags = ['TEST', 'TEST']  # 'TEST', 'AA', 'PS', 'ALL'
num_models = [2, 3]  # if 'TEST', number of all-active models
out_dirs = ['testing1', 'testing2']
scales = [0.0025, 0.003]

for i in range(num_runs):
    flag = flags[i]
    num_model = num_models[i]
    out_dir = out_dirs[i]
    scale = scales[i]

    scn.add_simulation_inputs(flag, num_model, scale)
    scn.build_node_sets(flag, num_model)
    scn.build_network(flag, num_model)
    scn.run(out_dir)
