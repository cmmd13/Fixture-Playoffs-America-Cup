# MP = mathematical programming
# CP = constraint programming
from docplex.mp.model import Model

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.path import Path # Para colores a la gráfica
from matplotlib.patches import PathPatch # Más para colores
import seaborn as sns #Libreria donde estan los colores

# Creación del modelo
md1 = Model('modelo')

# Creacion de variables
x1 = md1.continuous_var(name='x1')
x2 = md1.continuous_var(name='x2')

# Creando la f.o.
md1.maximize(10 * x1 + 1 * x2)

# Creando las restricciones
md1.add_constraint(x1 + x2 <= 80)
md1.add_constraint(x1 <= 40)
# Las de no negatividad son añadidas automáticamente

# Printiamos el modelo
print(md1.export_to_string())

# Resolvemos el problema
# Log_output te imprime lo q va haciendo cplex
solution = md1.solve(log_output = True)

# Veamos si es óptima:
md1.get_solve_status()

# Veamos la solucion
solution.display()