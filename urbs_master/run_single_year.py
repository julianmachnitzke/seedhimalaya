import os
import shutil
import urbs
from datetime import date

scripts_dir = os.path.dirname(__file__)

input_files = 'single_year_example.xlsx'  # for single year file name, for intertemporal folder name
input_dir = os.path.join(scripts_dir, '..', 'urbs_master', 'Input')
input_path = os.path.join(input_dir, input_files)

result_name = 'single-year'
result_dir = urbs.prepare_result_directory(result_name)  # name + time stamp

#get year
year = date.today().year
year = 2020

# copy input file to result directory
try:
    shutil.copytree(input_path, os.path.join(result_dir, input_dir))
except NotADirectoryError:
    shutil.copyfile(input_path, os.path.join(result_dir, input_files))
# copy run file to result directory
shutil.copy(__file__, result_dir)

# objective function
objective = 'cost'  # set either 'cost' or 'CO2' as objective

# Choose Solver (cplex, glpk, gurobi, ...)
solver = 'glpk'

# simulation timesteps
(offset, length) = (0, 24*14)  # time step selection
timesteps = range(offset, offset+length+1)
dt = 1  # length of each time step (unit: hours)

# detailed reporting commodity/sites
report_tuples = [
    (year, 'Mid', 'Elec'),
    (year, 'Mid', 'Hydro'), 
    (year, 'Mid', 'Solar'),
    (year, 'Mid', 'Slack')
    ]


# optional: define names for sites in report_tuples
report_sites_name = {}

# plotting commodities/sites
plot_tuples = [
    (year, 'Mid', 'Elec'),
    (year, 'Mid', 'Hydro'), 
    (year, 'Mid', 'Solar'),
    (year, 'Mid', 'Slack')
    ]

# optional: define names for sites in plot_tuples
plot_sites_name = {}

# plotting timesteps
plot_periods = {
    'all': timesteps[1:]
}

# add or change plot colors
my_colors = {
    'Mid': (200, 230, 200)
}
for country, color in my_colors.items():
    urbs.COLORS[country] = color

# select scenarios to be run
scenarios = [
             urbs.scenario_base,
#             urbs.scenario_stock_prices,
#             urbs.scenario_co2_limit,
#             urbs.scenario_co2_tax_mid,
#             urbs.scenario_no_dsm,
#             urbs.scenario_north_process_caps,
#             urbs.scenario_all_together
            ]

for scenario in scenarios:
    prob = urbs.run_scenario(input_path, solver, timesteps, scenario,
                             result_dir, dt, objective,
                             plot_tuples=plot_tuples,
                             plot_sites_name=plot_sites_name,
                             plot_periods=plot_periods,
                             report_tuples=report_tuples,
                             report_sites_name=report_sites_name)