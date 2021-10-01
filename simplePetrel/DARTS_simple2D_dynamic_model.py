from darts.models.reservoirs.struct_reservoir import StructReservoir
from darts.models.physics.dead_oil import DeadOil
from darts.models.darts_model import DartsModel
from darts.tools.keyword_file_tools import load_single_keyword
from darts.engines import rate_prod_well_control, rate_inj_well_control
from darts.models.opt.opt_dead_oil_model import OptDeadOilModel
import math
import numpy as np
import pandas as pd
from models.Block.Projection_Structured import ProjectionStruct
import matplotlib.pyplot as plt
import seaborn as sns
from D_DO.properties_correlations import *


class Reference_Model(DartsModel):
    def __init__(self, T, nx, ny, dx, dy, timestep, perm_input=[], poro_input=[]):
        # call base class constructor
        super().__init__()

        # measure time spend on reading/initialization
        self.timer.node["initialization"].start()
        self.T = T
        self.timestep = timestep
        self.nx = nx
        self.ny = ny
		self.permx = perm_input[:]

        permz = 100
        poro = poro_input[:]

        depth = 2000
        self.reservoir = StructReservoir(self.timer, nx=self.nx, ny=self.ny,
                                         nz=1, dx=dx, dy=dy, dz=10, permx=self.permx,
                                         permy=self.permy, permz=permz, poro=poro, depth=depth,
                                         actnum=1)
										 
		# Consistent well location; wells are located in the 1/4 length of the reservoir with any number of grid cells
        nx_tempt = nx / 4
        well_inj = 0
        if nx_tempt != 1:
            N = int(np.log(nx_tempt) / np.log(3))
            for k in range(N):
                well_inj = well_inj + 3 ** ((N - k) - 1)

        self.injection_well = well_inj + 1
        self.production_wells = nx - (well_inj + 1) + 1

        self.reservoir.add_well("I1")
        self.reservoir.add_perforation(well=self.reservoir.wells[-1], i=nx - (well_inj + 1) + 1,
                                       j=nx - (well_inj + 1) + 1,
                                       k=1, well_index=-1)
        self.reservoir.inj_wells = [self.reservoir.wells[0]]

        self.reservoir.add_well("I2")
        self.reservoir.add_perforation(well=self.reservoir.wells[-1], i=nx - (well_inj + 1) + 1,
                                       j=well_inj + 1,
                                       k=1, well_index=-1)
        self.reservoir.inj_wells.append(self.reservoir.wells[1])

        self.reservoir.add_well("P1")
        self.reservoir.add_perforation(well=self.reservoir.wells[-1], i=well_inj + 1, j=well_inj + 1,
                                       k=1, well_index=-1)
        self.reservoir.prod_wells = [self.reservoir.wells[2]]

        self.reservoir.add_well("P2")
        self.reservoir.add_perforation(well=self.reservoir.wells[-1], i=well_inj + 1, j=nx - (well_inj + 1) + 1,
                                       k=1, well_index=-1)
        self.reservoir.prod_wells.append(self.reservoir.wells[3])

        # ---------------------------------------------------------------------------------------------------------------

        self.physics = DeadOil(timer=self.timer, physics_filename='physics_brugge.in',
                               n_points=1000, min_p=0, max_p=500, min_z=1e-12)

        self.params.first_ts = 1e-4
        self.params.mult_ts = 2
        self.params.max_ts = 30
        self.params.tolerance_newton = 1e-3
        self.params.tolerance_linear = 1e-5
        self.params.max_i_newton = 20
        self.params.max_i_linear = 50

        self.runtime = self.T

        self.timer.node["initialization"].stop()

    def set_initial_conditions(self):
        self.physics.set_uniform_initial_conditions(self.reservoir.mesh, uniform_pressure=170,
                                                    uniform_composition=[0.2])

    def set_boundary_conditions(self):
        for w in self.reservoir.inj_wells:
            w.control = self.physics.new_bhp_water_inj(200)
            #w.control = self.physics.new_rate_water_inj(0)
            #w.constraint = self.physics.new_bhp_water_inj(5000)

        for w in self.reservoir.prod_wells:
            w.control = self.physics.new_bhp_prod(100)
            # w.control = self.physics.new_rate_oil_prod(0)
            # w.constraint = self.physics.new_bhp_prod(100)

    def run(self):
        import random
        random.seed(3)
        P = []
        BHP = []
        schedule = np.linspace(self.timestep, self.T, int(self.T / self.timestep))
        random_Inj_BHP = 200
        random_Pro_BHP = 100
        inj_rate = 200
        for ts in schedule:
            if hasattr(self.reservoir, 'inj_wells'):
                for w in self.reservoir.inj_wells:
                    random_Inj_BHP = 200 + random.uniform(1, 30)
                    w.control.target_pressure = random_Inj_BHP
                    #w.control.target_rate = inj_rate #+ random.uniform(-200, 200)

            if hasattr(self.reservoir, 'prod_wells'):
                for w in self.reservoir.prod_wells:
                    random_Pro_BHP = 100 - random.uniform(1, 30)
                    w.control.target_pressure = random_Pro_BHP

            # BHP.append([random_Inj_BHP, random_Pro_BHP])
            self.physics.engine.run(self.timestep)
            # X = np.array(self.physics.engine.X)
            # P.append(X[0:len(X) - 4:2])
            self.physics.engine.report()

