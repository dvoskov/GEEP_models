from darts.engines import value_vector, redirect_darts_output, sim_params
from model_2ph_do import Model
import pandas as pd

import matplotlib.pyplot as plt

redirect_darts_output('out.log')
m = Model()
m.init()
m.export_pro_vtk()
for a in range(10):
    m.run_python(100)
    m.export_pro_vtk()
m.print_timers()
m.print_stat()

time_data = pd.DataFrame.from_dict(m.physics.engine.time_data)
time_data.to_pickle("darts_time_data.pkl")

writer = pd.ExcelWriter('time_data.xlsx')
time_data.to_excel(writer, 'Sheet1')
writer.save()

# rate plotting
from darts.tools.plot_darts import *

plt.rc('font', size=12)
ax1 = plot_total_prod_oil_rate_darts(time_data, style='-', color='b')
ax1.set(xlabel="Days", ylabel="Total produced rate, sm$^3$/day")
plt.xlim(0, 1000)

plt.show()