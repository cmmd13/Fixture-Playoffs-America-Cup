# MP = mathematical programming
# CP = constraint programming
from docplex.mp.model import Model

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.path import Path # Para colores a la gráfica
from matplotlib.patches import PathPatch # Más para colores
import seaborn as sns #Libreria donde estan los colores

#region Creación de datos

selecciones = ['BRA', 'ARG', 'COL', 'URU', 'CHI', 'PER', 'VEN', 'BOL', 'PAR', 'ECU']
selecciones_top = {'BRA', 'ARG'}
fechas = [f for f in range(0,18)]
fechas_impar = [f for f in range(0,17,2)]

#endregion

#region Modelo

# Creación de modelo
model = Model('espejado')

# Variables
x = model.binary_var_dict(((e_loc, e_vis, f) for e_loc in selecciones for e_vis in selecciones for f in fechas),
                           name='partido')
y = model.binary_var_dict(((equipo, f) for equipo in selecciones for f in fechas_impar),
                           name='secuenciaHA')
w = model.binary_var_dict(((equipo, f) for equipo in selecciones for f in fechas_impar),
                           name='break')

# f.o.
model.minimize(model.sum(w[(e, f)] for e in selecciones for f in fechas_impar))

#region Restricciones
#Doble round robin
for e_loc in selecciones:
    for e_vis in selecciones:
        if e_loc != e_vis:
            model.add_constraint(model.sum(x[(e_loc, e_vis, f)] + x[(e_vis, e_loc, f)] for f in fechas[0:9]) == 1,
                                 ctname=f"drr_primera_vuelta_{e_loc}_{e_vis}")
            model.add_constraint(model.sum(x[(e_loc, e_vis, f)] + x[(e_vis, e_loc, f)] for f in fechas[9:18]) == 1,
                                 ctname=f"drr_segunda_vuelta_{e_loc}_{e_vis}")
            model.add_constraint(model.sum(x[(e_loc, e_vis, f)] for f in fechas) == 1,
                                ctname=f"drr_se_juegue{e_loc}_{e_vis}")
        else:
            model.add_constraint(model.sum(x[(e_loc, e_vis, f)] for f in fechas) == 0,
                                 ctname=f"drr_no_juegue_si_mismo_{e_vis}")



#Compacidad
for equipo in selecciones:
    selecciones_sin_equipo = selecciones.copy()
    selecciones_sin_equipo.remove(equipo)
    for f in fechas:
        model.add_constraint(model.sum(x[(otro_equipo, equipo, f)] + x[(equipo, otro_equipo, f)]for otro_equipo in selecciones_sin_equipo) == 1,
                             ctname=f"comp_{equipo}_{f}")

#Contra equipos top
for e_debil in selecciones:
    if not selecciones_top.__contains__(e_debil):
        for f in fechas[0:17]:
            model.add_constraint(model.sum(x[(e_debil, e_fuerte, f_)] + x[(e_fuerte, e_debil, f_)] for e_fuerte in selecciones_top for f_ in [f, f+1]) <= 1,
                                           ctname=f"vsFuerte_{e_debil}_{f}")

#Patrones H-A
#for e in selecciones:
#    n = len(selecciones)
#    model.add_constraint(model.sum(y[(e, f)]for f in fechas_impar) <= n/2,
#                         ctname=f"patronesHA_cota_sup_{e}")
#    model.add_constraint(model.sum(y[(e, f)] for f in fechas_impar) >= n/2-1,
#                         ctname=f"patronesHA_cota_inf_{e}")
#
#    for f in fechas_impar:
#        selecciones_sin_equipo = selecciones.copy()
#        selecciones_sin_equipo.remove(e)
#        model.add_constraint(model.sum(x[e,otro_e,f] + x[otro_e,e,f+1] for otro_e in selecciones_sin_equipo) - y[(e, f)] <=1,
#                             ctname=f"patronesHA_prender_y_{e}_{f}")
#        model.add_constraint(y[(e, f)] - model.sum(x[e, otro_e, f] for otro_e in selecciones_sin_equipo) <= 0,
#            ctname=f"patronesHA_apagarH_y_{e}_{f}")
#        model.add_constraint(y[(e, f)] - model.sum(x[otro_e, e, f+1] for otro_e in selecciones_sin_equipo) <= 0,
#            ctname=f"patronesHA_apagarA_y_{e}_{f}")

#Breaks de visitante
for e in selecciones:
    for f in fechas_impar:
        selecciones_sin_equipo = selecciones.copy()
        selecciones_sin_equipo.remove(e)
        model.add_constraint(model.sum(x[otro_e,e,f] + x[otro_e,e,f+1] for otro_e in selecciones_sin_equipo) - w[(e, f)] <=1,
                             ctname=f"breaks_prender_w_{e}_{f}")
        model.add_constraint(w[(e, f)] - model.sum(x[otro_e, e, f] for otro_e in selecciones_sin_equipo) <= 0,
            ctname=f"breaks_apagarA1_w_{e}_{f}")
        model.add_constraint(w[(e, f)] - model.sum(x[otro_e, e, f+1] for otro_e in selecciones_sin_equipo) <= 0,
            ctname=f"breaks_apagarA2_w_{e}_{f}")

# Esquema Mirror:
for e in selecciones:
    for otro_e in selecciones:
        if e != otro_e:
            for f in fechas[0:9]:
                model.add_constraint(x[(e, otro_e, f)] - x[(otro_e, e, f+len(fechas)/2)] == 0,
                                 ctname=f"Mirror__{e}_{otro_e}_{f}")

#endregion

#para chequear que esté andando
#print(model.export_to_string())

#endregion

#region Resolución de modelo
fixture = model.solve(log_output=True)
fixture.display()
print(model.get_solve_status())

#endregion