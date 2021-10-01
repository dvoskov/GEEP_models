from darts.models.reservoirs.struct_reservoir import StructReservoir
from darts.models.physics.dead_oil import DeadOil
from darts.models.darts_model import DartsModel
from darts.tools.keyword_file_tools import load_single_keyword
from darts.engines import rate_prod_well_control, rate_inj_well_control
from darts.models.opt.opt_dead_oil_model import OptDeadOilModel
import math
from darts.tools.plot_darts import *
import numpy as np
import pandas as pd
from models.Block.Projection_Structured import ProjectionStruct
from Sample_opt.Reference_2D import Reference_Model
from Sample_opt.Proxy_2D import Proxy_Model
from Sample_opt.Unstruct_Proxy_2D import Model_unstruct
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from old.opt_tools.model_modifiers import transmissibility_modifier, corey_params_modifier_region
from old.opt_tools.model_modifiers import well_index_modifier
from old.opt_tools.model_modifiers import model_modifier_aggregator
from darts.engines import redirect_darts_output, timer_node, value_vector, index_vector



total_time = 1000
Nx = 108
ts = 50
total_length = 400
# ----------------------------- Reading Reservoir Properties ---------------------------------
# Porosity values are red from an ECLIPSE file exported from Petrel, this method is not applicable in case of more than one realizations 
true_poro_input = load_single_keyword('true_poro.in', 'PORO')
true_perm_input = 35555.56 * ((true_poro_input ** 3) / (1 - true_poro_input) ** 2)      # perms are calculated using Karman-Kozeiny correlation

true_perm_input = true_perm_input.reshape(int(Nx * Nx), )
true_poro_input = true_poro_input.reshape(int(Nx * Nx), )
# ----------------------------- Initializing Reference model ---------------------------------
dx = total_length / Nx
dy = total_length / Nx
M = Reference_Model(T=total_time, nx=Nx, ny=Nx, dx=dx, dy=dy, timestep=ts,
                    perm_input=true_perm_input, poro_input=true_poro_input)
redirect_darts_output('')
M.init()
M.run()
M.print_timers()
ReferenceModel_df_report = pd.DataFrame.from_dict(M.physics.engine.time_data_report)
ReferenceModel_df = pd.DataFrame.from_dict(M.physics.engine.time_data)
ReferenceModel_df.to_pickle("ReferenceModel_data.pkl")
ReferenceModel_df_report.to_pickle("ReferenceModel_data_report.pkl")

X = np.array(M.physics.engine.X, copy=False)
nb = M.nx * M.ny

p = X[0:2 * nb:2]
z = X[1:2 * nb:2]
