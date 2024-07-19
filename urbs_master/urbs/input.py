import pandas as pd
import os
import glob
from xlrd import XLRDError
import pyomo.core as pyomo
from .features.modelhelper import *
from .identify import *

scripts_dir = os.path.dirname(__file__)

# def read_input(input_files, year):
#     """Read Excel input file and prepare URBS input dict.

#     Reads the Excel spreadsheets that adheres to the structure shown in
#     mimo-example.xlsx. Column titles in 'Demand' and 'SupIm' are split, so that
#     'Site.Commodity' becomes the MultiIndex column ('Site', 'Commodity').

#     Args:
#         - filename: filename to Excel spreadsheets
#         - year: current year for non-intertemporal problems

#     Returns:
#         a dict of up to 12 DataFrames
#     """

#     if os.path.isdir(input_files):
#         glob_input = os.path.join(input_files, '*.xlsx')
#         input_files = sorted(glob.glob(glob_input))
#     else:
#         input_files = [input_files]

#     gl = []
#     sit = []
#     com = []
#     pro = []
#     pro_com = []
#     tra = []
#     sto = []
#     dem = []
#     sup = []
#     bsp = []
#     ds = []
#     ef = []

#     for filename in input_files:
#         with pd.ExcelFile(filename) as xls:

#             global_prop = xls.parse('Global').set_index(['Property'])
#             # create support timeframe index
#             if ('Support timeframe' in
#                     global_prop.value):
#                 support_timeframe = (
#                     global_prop.loc['Support timeframe']['value'])
#                 global_prop = (
#                     global_prop.drop(['Support timeframe'])
#                     .drop(['description'], axis=1))
#             else:
#                 support_timeframe = year
#             global_prop = pd.concat([global_prop], keys=[support_timeframe],
#                                     names=['support_timeframe'])
#             gl.append(global_prop)
#             site = xls.parse('Site').set_index(['Name'])
#             site = pd.concat([site], keys=[support_timeframe],
#                               names=['support_timeframe'])
#             sit.append(site)
#             commodity = (
#                 xls.parse('Commodity')
#                     .set_index(['Site', 'Commodity', 'Type']))
#             commodity = pd.concat([commodity], keys=[support_timeframe],
#                                   names=['support_timeframe'])
#             com.append(commodity)
#             process = xls.parse('Process').set_index(['Site', 'Process'])
#             process = pd.concat([process], keys=[support_timeframe],
#                                 names=['support_timeframe'])
#             pro.append(process)
#             process_commodity = (
#                 xls.parse('Process-Commodity')
#                     .set_index(['Process', 'Commodity', 'Direction']))
#             process_commodity = pd.concat([process_commodity],
#                                           keys=[support_timeframe],
#                                           names=['support_timeframe'])
#             pro_com.append(process_commodity)
#             demand = xls.parse('Demand').set_index(['t'])
#             demand = pd.concat([demand], keys=[support_timeframe],
#                                 names=['support_timeframe'])
#             # split columns by dots '.', so that 'DE.Elec' becomes
#             # the two-level column index ('DE', 'Elec')
#             demand.columns = split_columns(demand.columns, '.')
#             dem.append(demand)
#             supim = xls.parse('SupIm').set_index(['t'])
#             supim = pd.concat([supim], keys=[support_timeframe],
#                               names=['support_timeframe'])
#             supim.columns = split_columns(supim.columns, '.')
#             sup.append(supim)

#             # collect data for the additional features
#             # Transmission, Storage, DSM
#             if 'Transmission' in xls.sheet_names:
#                 transmission = (
#                     xls.parse('Transmission')
#                     .set_index(['Site In', 'Site Out',
#                                 'Transmission', 'Commodity']))
#                 transmission = (
#                     pd.concat([transmission], keys=[support_timeframe],
#                               names=['support_timeframe']))
#             else:
#                 transmission = pd.DataFrame()
#             tra.append(transmission)
#             if 'Storage' in xls.sheet_names:
#                 storage = (
#                     xls.parse('Storage')
#                     .set_index(['Site', 'Storage', 'Commodity']))
#                 storage = pd.concat([storage], keys=[support_timeframe],
#                                     names=['support_timeframe'])
#             else:
#                 storage = pd.DataFrame()
#             sto.append(storage)
#             if 'DSM' in xls.sheet_names:
#                 dsm = xls.parse('DSM').set_index(['Site', 'Commodity'])
#                 dsm = pd.concat([dsm], keys=[support_timeframe],
#                                 names=['support_timeframe'])
#             else:
#                 dsm = pd.DataFrame()
#             ds.append(dsm)
#             if 'Buy-Sell-Price'in xls.sheet_names:
#                 buy_sell_price = xls.parse('Buy-Sell-Price').set_index(['t'])
#                 buy_sell_price = pd.concat([buy_sell_price],
#                                             keys=[support_timeframe],
#                                             names=['support_timeframe'])
#                 buy_sell_price.columns = \
#                     split_columns(buy_sell_price.columns, '.')
#             else:
#                 buy_sell_price = pd.DataFrame()
#             bsp.append(buy_sell_price)
#             if 'TimeVarEff' in xls.sheet_names:
#                 eff_factor = (xls.parse('TimeVarEff').set_index(['t']))
#                 eff_factor = pd.concat([eff_factor], keys=[support_timeframe],
#                                         names=['support_timeframe'])
#                 eff_factor.columns = split_columns(eff_factor.columns, '.')
#             else:
#                 eff_factor = pd.DataFrame()
#             ef.append(eff_factor)

#     # prepare input data
#     try:
#         global_prop = pd.concat(gl, sort=False)
#         site = pd.concat(sit, sort=False)
#         commodity = pd.concat(com, sort=False)
#         process = pd.concat(pro, sort=False)
#         process_commodity = pd.concat(pro_com, sort=False)
#         demand = pd.concat(dem, sort=False)
#         supim = pd.concat(sup, sort=False)
#         transmission = pd.concat(tra, sort=False)
#         storage = pd.concat(sto, sort=False)
#         dsm = pd.concat(ds, sort=False)
#         buy_sell_price = pd.concat(bsp, sort=False)
#         eff_factor = pd.concat(ef, sort=False)
#     except KeyError:
#         pass

#     data = {
#         'global_prop': global_prop,
#         'site': site,
#         'commodity': commodity,
#         'process': process,
#         'process_commodity': process_commodity,
#         'demand': demand,
#         'supim': supim,
#         'transmission': transmission,
#         'storage': storage,
#         'dsm': dsm,
#         'buy_sell_price': buy_sell_price.dropna(axis=1, how='all'),
#         'eff_factor': eff_factor.dropna(axis=1, how='all')
#     }

#     # sort nested indexes to make direct assignments work
#     for key in data:
#         if isinstance(data[key].index, pd.MultiIndex):
#             data[key].sort_index(inplace=True)
#     return data


def read_input(input_files, year):
    
    directory = os.path.join(scripts_dir, '..', 'urbs_master', 'Input', 'json')

    json_file_path = os.path.join(directory, "commodity.json")
    commodity_load = load_commodity_json_to_dataframe(json_file_path)
    
    json_file_path = os.path.join(directory, "buy_sell_price.json")
    buy_sell_load = load_buy_sell_json_to_dataframe(json_file_path)

    json_file_path = os.path.join(directory, "demand.json")
    demand_load = load_demand_json_to_dataframe(json_file_path)

    json_file_path = os.path.join(directory, "dsm.json")
    dsm_load = load_dsm_json_to_dataframe(json_file_path)
    
    json_file_path = os.path.join(directory, "eff_factor.json")
    eff_factor_load = load_eff_factor_json_to_dataframe(json_file_path)
    
    json_file_path = os.path.join(directory, "global_prop.json")
    global_prop_load = load_global_prop_json_to_dataframe(json_file_path)
        
    json_file_path = os.path.join(directory, "process.json")
    process_load = load_process_json_to_dataframe(json_file_path)

    json_file_path = os.path.join(directory, "process_commodity.json")
    process_commodity_load = load_process_commodity_json_to_dataframe(json_file_path)

    json_file_path = os.path.join(directory, "site.json")
    site_load = load_site_json_to_dataframe(json_file_path)
    
    json_file_path = os.path.join(directory, "storage.json")
    storage_load = load_storage_json_to_dataframe(json_file_path)
    
    json_file_path = os.path.join(directory, "supim.json")
    supim_load = load_supim_json_to_dataframe(json_file_path)
    
    json_file_path = os.path.join(directory, "transmission.json")
    transmission_load = load_transmission_json_to_dataframe(json_file_path)
 
        
    
    data_load_dict = {
    'buy_sell_price': buy_sell_load,
    'commodity': commodity_load,
    'demand': demand_load,
    'dsm': dsm_load,
    'eff_factor': eff_factor_load,
    'global_prop': global_prop_load,
    'process': process_load,
    'process_commodity': process_commodity_load,
    'site': site_load,
    'storage': storage_load,
    'supim': supim_load,
    'transmission': transmission_load}
    
    
    data = data_load_dict
    
    return data


# preparing the pyomo model
def pyomo_model_prep(data, timesteps):
    '''Performs calculations on the data frames in dictionary "data" for
    further usage by the model.

    Args:
        - data: input data dictionary
        - timesteps: range of modeled timesteps

    Returns:
        a rudimentary pyomo.CancreteModel instance
    '''

    m = pyomo.ConcreteModel()

    # Preparations
    # ============
    # Data import. Syntax to access a value within equation definitions looks
    # like this:
    #
    #     storage.loc[site, storage, commodity][attribute]
    #

    m.mode = identify_mode(data)
    m.timesteps = timesteps
    m.global_prop = data['global_prop']
    commodity = data['commodity']
    process = data['process']

    # create no expansion dataframes
    pro_const_cap = process[process['inst-cap'] == process['cap-up']]

    # create list with all support timeframe values
    m.stf_list = m.global_prop.index.levels[0].tolist()
    # creating list wih cost types
    m.cost_type_list = ['Invest', 'Fixed', 'Variable', 'Fuel', 'Environmental']

    # Converting Data frames to dict
    # Data frames that need to be modified will be converted after modification
    m.site_dict = data['site'].to_dict()
    m.demand_dict = data['demand'].to_dict()
    m.supim_dict = data['supim'].to_dict()

    # additional features
    if m.mode['tra']:
        transmission = data['transmission'].dropna(axis=0, how='all')
        # create no expansion dataframes
        tra_const_cap = transmission[
            transmission['inst-cap'] == transmission['cap-up']]

    if m.mode['sto']:
        storage = data['storage'].dropna(axis=0, how='all')
        # create no expansion dataframes
        sto_const_cap_c = storage[storage['inst-cap-c'] == storage['cap-up-c']]
        sto_const_cap_p = storage[storage['inst-cap-p'] == storage['cap-up-p']]

    if m.mode['dsm']:
        m.dsm_dict = data["dsm"].dropna(axis=0, how='all').to_dict()
    if m.mode['bsp']:
        m.buy_sell_price_dict = \
            data["buy_sell_price"].dropna(axis=0, how='all').to_dict()
        # adding Revenue and Purchase to cost types
        m.cost_type_list.extend(['Revenue', 'Purchase'])
    if m.mode['tve']:
        m.eff_factor_dict = \
            data["eff_factor"].dropna(axis=0, how='all').to_dict()

    # Create columns of support timeframe values
    commodity['support_timeframe'] = (commodity.index.
                                      get_level_values('support_timeframe'))
    process['support_timeframe'] = (process.index.
                                    get_level_values('support_timeframe'))
    if m.mode['tra']:
        transmission['support_timeframe'] = (transmission.index.
                                             get_level_values
                                             ('support_timeframe'))
    if m.mode['sto']:
        storage['support_timeframe'] = (storage.index.
                                        get_level_values('support_timeframe'))

    # installed units for intertemporal planning
    if m.mode['int']:
        m.inst_pro = process['inst-cap']
        m.inst_pro = m.inst_pro[m.inst_pro > 0]
        if m.mode['tra']:
            m.inst_tra = transmission['inst-cap']
            m.inst_tra = m.inst_tra[m.inst_tra > 0]
        if m.mode['sto']:
            m.inst_sto = storage['inst-cap-p']
            m.inst_sto = m.inst_sto[m.inst_sto > 0]

    # process input/output ratios
    m.r_in_dict = (data['process_commodity'].xs('In', level='Direction')
                   ['ratio'].to_dict())
    m.r_out_dict = (data['process_commodity'].xs('Out', level='Direction')
                    ['ratio'].to_dict())

    # process areas
    proc_area = data["process"]['area-per-cap']
    proc_area = proc_area[proc_area >= 0]
    m.proc_area_dict = proc_area.to_dict()

    # input ratios for partial efficiencies
    # only keep those entries whose values are
    # a) positive and
    # b) numeric (implicitely, as NaN or NV compare false against 0)
    r_in_min_fraction = data['process_commodity'].xs('In', level='Direction')
    r_in_min_fraction = r_in_min_fraction['ratio-min']
    r_in_min_fraction = r_in_min_fraction[r_in_min_fraction > 0]
    m.r_in_min_fraction_dict = r_in_min_fraction.to_dict()

    # output ratios for partial efficiencies
    # only keep those entries whose values are
    # a) positive and
    # b) numeric (implicitely, as NaN or NV compare false against 0)
    r_out_min_fraction = data['process_commodity'].xs('Out', level='Direction')
    r_out_min_fraction = r_out_min_fraction['ratio-min']
    r_out_min_fraction = r_out_min_fraction[r_out_min_fraction > 0]
    m.r_out_min_fraction_dict = r_out_min_fraction.to_dict()

    # storages with fixed initial state
    if m.mode['sto']:
        stor_init_bound = storage['init']
        m.stor_init_bound_dict = \
            stor_init_bound[stor_init_bound >= 0].to_dict()

        try:
            # storages with fixed energy-to-power ratio
            sto_ep_ratio = storage['ep-ratio']
            m.sto_ep_ratio_dict = sto_ep_ratio[sto_ep_ratio >= 0].to_dict()
        except KeyError:
            m.sto_ep_ratio_dict = {}

    # derive invcost factor from WACC and depreciation duration
    if m.mode['int']:
        # modify pro_const_cap for intertemporal mode
        for index in tuple(pro_const_cap.index):
            stf_process = process.xs((index[1], index[2]), level=(1, 2))
            if (not stf_process['cap-up'].max(axis=0) ==
                    pro_const_cap.loc[index]['inst-cap']):
                pro_const_cap = pro_const_cap.drop(index)

        # derive invest factor from WACC, depreciation and discount untility
        process['discount'] = (m.global_prop.xs('Discount rate', level=1)
                                .loc[m.global_prop.index.min()[0]]['value'])
        process['stf_min'] = m.global_prop.index.min()[0]
        process['stf_end'] = (m.global_prop.index.max()[0] +
                              m.global_prop.loc[
                              (max(commodity.index.get_level_values
                                   ('support_timeframe').unique()),
                               'Weight')]['value'] - 1)
        process['invcost-factor'] = (process.apply(
                                     lambda x: invcost_factor(
                                         x['depreciation'],
                                         x['wacc'],
                                         x['discount'],
                                         x['support_timeframe'],
                                         x['stf_min']),
                                     axis=1))

        # derive overpay-factor from WACC, depreciation and discount untility
        process['overpay-factor'] = (process.apply(
                                     lambda x: overpay_factor(
                                         x['depreciation'],
                                         x['wacc'],
                                         x['discount'],
                                         x['support_timeframe'],
                                         x['stf_min'],
                                         x['stf_end']),
                                     axis=1))
        process.loc[(process['overpay-factor'] < 0) |
                    (process['overpay-factor']
                     .isnull()), 'overpay-factor'] = 0

        # Derive multiplier for all energy based costs
        commodity['stf_dist'] = (commodity['support_timeframe'].
                                 apply(stf_dist, m=m))
        commodity['discount-factor'] = (commodity['support_timeframe'].
                                        apply(discount_factor, m=m))
        commodity['eff-distance'] = (commodity['stf_dist'].
                                     apply(effective_distance, m=m))
        commodity['cost_factor'] = (commodity['discount-factor'] *
                                    commodity['eff-distance'])
        process['stf_dist'] = (process['support_timeframe'].
                               apply(stf_dist, m=m))
        process['discount-factor'] = (process['support_timeframe'].
                                      apply(discount_factor, m=m))
        process['eff-distance'] = (process['stf_dist'].
                                   apply(effective_distance, m=m))
        process['cost_factor'] = (process['discount-factor'] *
                                  process['eff-distance'])

        # Additional features
        # transmission mode
        if m.mode['tra']:
            # modify tra_const_cap for intertemporal mode
            for index in tuple(tra_const_cap.index):
                stf_transmission = transmission.xs((index[1], index[2], index[3], index[4]),
                                                   level=(1, 2, 3, 4))
                if (not stf_transmission['cap-up'].max(axis=0) ==
                        tra_const_cap.loc[index]['inst-cap']):
                    tra_const_cap = tra_const_cap.drop(index)
            # derive invest factor from WACC, depreciation and
            # discount untility
            transmission['discount'] = (
                m.global_prop.xs('Discount rate', level=1)
                .loc[m.global_prop.index.min()[0]]['value'])
            transmission['stf_min'] = m.global_prop.index.min()[0]
            transmission['stf_end'] = (m.global_prop.index.max()[0] +
                                       m.global_prop.loc[
                                       (max(commodity.index.get_level_values
                                            ('support_timeframe').unique()),
                                        'Weight')]['value'] - 1)
            transmission['invcost-factor'] = (
                transmission.apply(lambda x: invcost_factor(
                    x['depreciation'],
                    x['wacc'],
                    x['discount'],
                    x['support_timeframe'],
                    x['stf_min']),
                    axis=1))
            # derive overpay-factor from WACC, depreciation and
            # discount untility
            transmission['overpay-factor'] = (
                transmission.apply(lambda x: overpay_factor(
                    x['depreciation'],
                    x['wacc'],
                    x['discount'],
                    x['support_timeframe'],
                    x['stf_min'],
                    x['stf_end']),
                    axis=1))
            # Derive multiplier for all energy based costs
            transmission.loc[(transmission['overpay-factor'] < 0) |
                             (transmission['overpay-factor'].isnull()),
                             'overpay-factor'] = 0
            transmission['stf_dist'] = (transmission['support_timeframe'].
                                        apply(stf_dist, m=m))
            transmission['discount-factor'] = (
                transmission['support_timeframe'].apply(discount_factor, m=m))
            transmission['eff-distance'] = (transmission['stf_dist'].
                                            apply(effective_distance, m=m))
            transmission['cost_factor'] = (transmission['discount-factor'] *
                                           transmission['eff-distance'])
        # storage mode
        if m.mode['sto']:
            # modify sto_const_cap_c and sto_const_cap_p for intertemporal mode
            for index in tuple(sto_const_cap_c.index):
                stf_storage = storage.xs((index[1], index[2], index[3]), level=(1, 2, 3))
                if (not stf_storage['cap-up-c'].max(axis=0) ==
                        sto_const_cap_c.loc[index]['inst-cap-c']):
                    sto_const_cap_c = sto_const_cap_c.drop(index)

            for index in tuple(sto_const_cap_p.index):
                stf_storage = storage.xs((index[1], index[2], index[3]), level=(1, 2, 3))
                if (not stf_storage['cap-up-p'].max(axis=0) ==
                        sto_const_cap_p.loc[index]['inst-cap-p']):
                    sto_const_cap_p = sto_const_cap_p.drop(index)

            # derive invest factor from WACC, depreciation and
            # discount untility
            storage['discount'] = m.global_prop.xs('Discount rate', level=1) \
                                   .loc[m.global_prop.index.min()[0]]['value']
            storage['stf_min'] = m.global_prop.index.min()[0]
            storage['stf_end'] = (m.global_prop.index.max()[0] +
                                  m.global_prop.loc[
                                  (max(commodity.index.get_level_values
                                       ('support_timeframe').unique()),
                                   'Weight')]['value'] - 1)
            storage['invcost-factor'] = (
                storage.apply(
                    lambda x: invcost_factor(
                        x['depreciation'],
                        x['wacc'],
                        x['discount'],
                        x['support_timeframe'],
                        x['stf_min']),
                    axis=1))
            storage['overpay-factor'] = (
                storage.apply(lambda x: overpay_factor(
                    x['depreciation'],
                    x['wacc'],
                    x['discount'],
                    x['support_timeframe'],
                    x['stf_min'],
                    x['stf_end']),
                    axis=1))

            storage.loc[(storage['overpay-factor'] < 0) |
                        (storage['overpay-factor'].isnull()),
                        'overpay-factor'] = 0

            storage['stf_dist'] = (storage['support_timeframe']
                                   .apply(stf_dist, m=m))
            storage['discount-factor'] = (storage['support_timeframe']
                                          .apply(discount_factor, m=m))
            storage['eff-distance'] = (storage['stf_dist']
                                       .apply(effective_distance, m=m))
            storage['cost_factor'] = (storage['discount-factor'] *
                                      storage['eff-distance'])
    else:
        # for one year problems
        process['invcost-factor'] = (
            process.apply(
                lambda x: invcost_factor(
                    x['depreciation'],
                    x['wacc']),
                axis=1))

        # cost factor will be set to 1 for non intertemporal problems
        commodity['cost_factor'] = 1
        process['cost_factor'] = 1

        # additional features
        if m.mode['tra']:
            transmission['invcost-factor'] = (
                transmission.apply(lambda x:
                                   invcost_factor(x['depreciation'],
                                                  x['wacc']),
                                   axis=1))
            transmission['cost_factor'] = 1
        if m.mode['sto']:
            storage['invcost-factor'] = (
                storage.apply(lambda x:
                              invcost_factor(x['depreciation'],
                                             x['wacc']),
                              axis=1))
            storage['cost_factor'] = 1

    # Converting Data frames to dictionaries
    m.global_prop_dict = m.global_prop.to_dict()
    m.commodity_dict = commodity.to_dict()
    m.process_dict = process.to_dict()

    # dictionaries for additional features
    if m.mode['tra']:
        m.transmission_dict = transmission.to_dict()
        # DCPF transmission lines are bidirectional and do not have symmetry
        # fix-cost and inv-cost should be multiplied by 2
        if m.mode['dpf']:
            transmission_dc = transmission[transmission['reactance'] > 0]
            m.transmission_dc_dict = transmission_dc.to_dict()
            for t in m.transmission_dc_dict['reactance']:
                m.transmission_dict['inv-cost'][t] = 2 * m.transmission_dict['inv-cost'][t]
                m.transmission_dict['fix-cost'][t] = 2 * m.transmission_dict['fix-cost'][t]

    if m.mode['sto']:
        m.storage_dict = storage.to_dict()

    # update m.mode['exp'] and write dictionaries with constant capacities
    m.mode['exp']['pro'] = identify_expansion(pro_const_cap['inst-cap'],
                                              process['inst-cap'].dropna())
    m.pro_const_cap_dict = pro_const_cap['inst-cap'].to_dict()

    if m.mode['tra']:
        m.mode['exp']['tra'] = identify_expansion(
            tra_const_cap['inst-cap'],
            transmission['inst-cap'].dropna())
        m.tra_const_cap_dict = tra_const_cap['inst-cap'].to_dict()

    if m.mode['sto']:
        m.mode['exp']['sto-c'] = identify_expansion(
            sto_const_cap_c['inst-cap-c'], storage['inst-cap-c'].dropna())
        m.sto_const_cap_c_dict = sto_const_cap_c['inst-cap-c'].to_dict()
        m.mode['exp']['sto-p'] = identify_expansion(
            sto_const_cap_c['inst-cap-p'], storage['inst-cap-p'].dropna())
        m.sto_const_cap_p_dict = sto_const_cap_p['inst-cap-p'].to_dict()

    return m


def split_columns(columns, sep='.'):
    """Split columns by separator into MultiIndex.

    Given a list of column labels containing a separator string (default: '.'),
    derive a MulitIndex that is split at the separator string.

    Args:
        - columns: list of column labels, containing the separator string
        - sep: the separator string (default: '.')

    Returns:
        a MultiIndex corresponding to input, with levels split at separator

    Example:
        >>> split_columns(['DE.Elec', 'MA.Elec', 'NO.Wind'])
        MultiIndex(levels=[['DE', 'MA', 'NO'], ['Elec', 'Wind']],
                   labels=[[0, 1, 2], [0, 0, 1]])

    """
    if len(columns) == 0:
        return columns
    column_tuples = [tuple(col.split('.')) for col in columns]
    return pd.MultiIndex.from_tuples(column_tuples)


def get_input(prob, name):
    """Return input DataFrame of given name from urbs instance.

    These are identical to the key names returned by function `read_excel`.
    That means they are lower-case names and use underscores for word
    separation, e.g. 'process_commodity'.

    Args:
        - prob: a urbs model instance
        - name: an input DataFrame name ('commodity', 'process', ...)

    Returns:
        the corresponding input DataFrame

    """
    if hasattr(prob, name):
        # classic case: input data DataFrames are accessible via named
        # attributes, e.g. `prob.process`.
        return getattr(prob, name)
    elif hasattr(prob, '_data') and name in prob._data:
        # load case: input data is accessible via the input data cache dict
        return prob._data[name]
    else:
        # unknown
        raise ValueError("Unknown input DataFrame name!")


#%%

## json  part

import os
import pandas as pd
import json
import copy


directory = r'C:\Users\LENOVO\OneDrive\Documenti\CampusBiomedico\Erasmus\completesite\urbs_master\Input\json'

#%%

## commodity

json_file_path = os.path.join(directory, "commodity.json")

def load_commodity_json_to_dataframe(input_path):
    # Loading the JSON file
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Converting the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
    
    # Setting the MultiIndex
    df.set_index(['support_timeframe', 'Site', 'Commodity', 'Type'], inplace=True)
    
    return df


commodity_load = load_commodity_json_to_dataframe(json_file_path)



#%%

## buy sell price

json_file_path = os.path.join(directory, "buy_sell_price.json")

def load_buy_sell_json_to_dataframe(input_path):
    # Loading the JSON file
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Converting the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
    
    #     # Adjust column names for "Elec buy" and "Elec sell"
    # def adjust_column_name(col):
    #     if col == 'Elec buy':
    #         return ('Elec', 'buy')
    #     elif col == 'Elec sell':
    #         return ('Elec', 'sell')
    #     return col
    
    # # Apply the adjustment function to column names
    # df.columns = [adjust_column_name(col) for col in df.columns]
    
    # Setting the MultiIndex
    df.set_index(['support_timeframe', 't'], inplace=True)
    
    return df


buy_sell_load = load_buy_sell_json_to_dataframe(json_file_path)

#%%

## demand

json_file_path = os.path.join(directory, "demand.json")


def load_demand_json_to_dataframe(input_path):
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Initialize lists to store the extracted data
    rows = []
    data = []

    # Extract data from JSON
    for item in data_list:
        support_timeframe = item['support_timeframe']
        t = item['t']
        
        for level1_key, nested_dict in item.items():
            if level1_key not in ['support_timeframe', 't']:
                for level2_key, value in nested_dict.items():
                    rows.append((support_timeframe, t))
                    data.append((level1_key, level2_key, value))

    # Create a DataFrame
    df = pd.DataFrame(data, columns=['level1', 'level2', 'value'], index=pd.MultiIndex.from_tuples(rows, names=['support_timeframe', 't']))
    
    # Convert the 'value' column to the correct type (e.g., numeric) if necessary
    df['value'] = pd.to_numeric(df['value'], errors='ignore')
    
    # Pivot the DataFrame to get the desired structure
    df = df.pivot_table(index=['support_timeframe', 't'], columns=['level1', 'level2'], values='value', aggfunc='first')
    
    return df

# Example usage
demand_load = load_demand_json_to_dataframe(json_file_path)
print(demand_load)

#%%

## dsm

json_file_path = os.path.join(directory, "dsm.json")


def load_dsm_json_to_dataframe(input_path):
    # Loading the JSON file
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Converting the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
    
    # Checking if the DataFrame is empty
    if df.empty:
        # Creating an empty DataFrame with the specified columns and MultiIndex
        columns = ['delay', 'eff', 'recov', 'cap-max-do', 'cap-max-up']
        index = pd.MultiIndex.from_arrays([[], [], []], names=['support_timeframe', 'Site', 'Commodity'])
        df = pd.DataFrame(columns=columns, index=index)
    else:
        # Setting the MultiIndex
        df.set_index(['support_timeframe', 'Site', 'Commodity'], inplace=True)
    
    return df



dsm_load = load_dsm_json_to_dataframe(json_file_path)

#%%

## eff factor

json_file_path = os.path.join(directory, "eff_factor.json")



def load_eff_factor_json_to_dataframe(input_path):
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Initialize lists to store the extracted data
    rows = []
    data = []

    # Extract data from JSON
    for item in data_list:
        support_timeframe = item['support_timeframe']
        t = item['t']
        
        for level1_key, nested_dict in item.items():
            if level1_key not in ['support_timeframe', 't']:
                for level2_key, value in nested_dict.items():
                    rows.append((support_timeframe, t))
                    data.append((level1_key, level2_key, value))

    # Create a DataFrame
    df = pd.DataFrame(data, columns=['level1', 'level2', 'value'], index=pd.MultiIndex.from_tuples(rows, names=['support_timeframe', 't']))
    
    # Convert the 'value' column to the correct type (e.g., numeric) if necessary
    df['value'] = pd.to_numeric(df['value'], errors='ignore')
    
    # Pivot the DataFrame to get the desired structure
    df = df.pivot_table(index=['support_timeframe', 't'], columns=['level1', 'level2'], values='value', aggfunc='first')
    
    return df

# Example usage
eff_factor_load = load_eff_factor_json_to_dataframe(json_file_path)
print(eff_factor_load)

#%%

## global prop

json_file_path = os.path.join(directory, "global_prop.json")


def load_global_prop_json_to_dataframe(input_path):
    # Loading the JSON file
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Converting the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
    
    #     # Adjust column names for "Elec buy" and "Elec sell"
    # def adjust_column_name(col):
    #     if col == 'Elec buy':
    #         return ('Elec', 'buy')
    #     elif col == 'Elec sell':
    #         return ('Elec', 'sell')
    #     return col
    
    # # Apply the adjustment function to column names
    # df.columns = [adjust_column_name(col) for col in df.columns]
    
    # Setting the MultiIndex
    df.set_index(['support_timeframe', 'Property'], inplace=True)
    
    return df


global_prop_load = load_global_prop_json_to_dataframe(json_file_path)


#%%

## process

json_file_path = os.path.join(directory, "process.json")


def load_process_json_to_dataframe(input_path):
    # Loading the JSON file
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Converting the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
    
    #     # Adjust column names for "Elec buy" and "Elec sell"
    # def adjust_column_name(col):
    #     if col == 'Elec buy':
    #         return ('Elec', 'buy')
    #     elif col == 'Elec sell':
    #         return ('Elec', 'sell')
    #     return col
    
    # # Apply the adjustment function to column names
    # df.columns = [adjust_column_name(col) for col in df.columns]
    
    # Setting the MultiIndex
    df.set_index(['support_timeframe', 'Site', 'Process'], inplace=True)
    
    return df


process_load = load_process_json_to_dataframe(json_file_path)


#%%

## process commodity

json_file_path = os.path.join(directory, "process_commodity.json")


def load_process_commodity_json_to_dataframe(input_path):
    # Loading the JSON file
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Converting the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
    
    #     # Adjust column names for "Elec buy" and "Elec sell"
    # def adjust_column_name(col):
    #     if col == 'Elec buy':
    #         return ('Elec', 'buy')
    #     elif col == 'Elec sell':
    #         return ('Elec', 'sell')
    #     return col
    
    # # Apply the adjustment function to column names
    # df.columns = [adjust_column_name(col) for col in df.columns]
    
    # Setting the MultiIndex
    df.set_index(['support_timeframe', 'Process', 'Commodity', 'Direction'], inplace=True)
    
    return df


process_commodity_load = load_process_commodity_json_to_dataframe(json_file_path)


#%%

## site

json_file_path = os.path.join(directory, "site.json")


def load_site_json_to_dataframe(input_path):
    # Loading the JSON file
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Converting the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
    
    
    # Setting the MultiIndex
    df.set_index(['support_timeframe', 'Name'], inplace=True)
    
    return df


site_load = load_site_json_to_dataframe(json_file_path)

#%%

## storage

json_file_path = os.path.join(directory, "storage.json")


def load_storage_json_to_dataframe(input_path):
    # Loading the JSON file
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Converting the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
    
    # Checking if the DataFrame is empty
    if df.empty:
        # Creating an empty DataFrame with the specified columns and MultiIndex
        columns = [
            'inst-cap-c', 'cap-lo-c', 'cap-up-c', 'inst-cap-p', 'cap-lo-p', 'cap-up-p', 
            'eff-in', 'eff-out', 'inv-cost-p', 'inv-cost-c', 'fix-cost-p', 'fix-cost-c', 
            'var-cost-p', 'var-cost-c', 'wacc', 'depreciation', 'init', 'discharge', 'ep-ratio'
        ]
        index = pd.MultiIndex.from_arrays([[], [], [], []], names=['support_timeframe', 'Site', 'Storage', 'Commodity'])
        df = pd.DataFrame(columns=columns, index=index)
    else:
        # Setting the MultiIndex
        df.set_index(['support_timeframe', 'Site', 'Storage', 'Commodity'], inplace=True)
    
    return df


storage_load = load_storage_json_to_dataframe(json_file_path)


#%%

## supim

json_file_path = os.path.join(directory, "supim.json")



def load_supim_json_to_dataframe(input_path):
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Initialize lists to store the extracted data
    rows = []
    data = []

    # Extract data from JSON
    for item in data_list:
        support_timeframe = item['support_timeframe']
        t = item['t']
        
        for level1_key, nested_dict in item.items():
            if level1_key not in ['support_timeframe', 't']:
                for level2_key, value in nested_dict.items():
                    rows.append((support_timeframe, t))
                    data.append((level1_key, level2_key, value))

    # Create a DataFrame
    df = pd.DataFrame(data, columns=['level1', 'level2', 'value'], index=pd.MultiIndex.from_tuples(rows, names=['support_timeframe', 't']))
    
    # Convert the 'value' column to the correct type (e.g., numeric) if necessary
    df['value'] = pd.to_numeric(df['value'], errors='ignore')
    
    # Pivot the DataFrame to get the desired structure
    df = df.pivot_table(index=['support_timeframe', 't'], columns=['level1', 'level2'], values='value', aggfunc='first')
    
    return df

# Example usage
supim_load = load_supim_json_to_dataframe(json_file_path)
print(supim_load)


#%%

## transmission


json_file_path = os.path.join(directory, "transmission.json")


def load_transmission_json_to_dataframe(input_path):
    # Loading the JSON file
    with open(input_path, 'r') as file:
        data_list = json.load(file)
    
    # Converting the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
    
    # Checking if the DataFrame is empty
    if df.empty:
        # Creating an empty DataFrame with the specified columns and MultiIndex
        columns = [
            'eff', 'inv-cost', 'fix-cost', 'var-cost', 'inst-cap', 'cap-lo', 
            'cap-up', 'wacc', 'depreciation', 'reactance', 'difflimit', 'base_voltage'
        ]
        index = pd.MultiIndex.from_arrays([[], [], [], [], []], names=['support_timeframe', 'Site In', 'Site Out', 'Transmission', 'Commodity'])
        df = pd.DataFrame(columns=columns, index=index)
    else:
        # Setting the MultiIndex
        df.set_index(['support_timeframe', 'Site In', 'Site Out', 'Transmission', 'Commodity'], inplace=True)
    
    return df


transmission_load = load_transmission_json_to_dataframe(json_file_path)

#%%
## bring together dataframes

data_load_dict = {
    'buy_sell_price': buy_sell_load,
    'commodity': commodity_load,
    'demand': demand_load,
    'dsm': dsm_load,
    'eff_factor': eff_factor_load,
    'global_prop': global_prop_load,
    'process': process_load,
    'process_commodity': process_commodity_load,
    'site': site_load,
    'storage': storage_load,
    'supim': supim_load,
    'transmission': transmission_load}