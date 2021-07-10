from docplex.mp.model import Model
import argparse
import xlsxwriter
import os
import pandas as pd
import numpy as np

from matplotlib import pyplot as plt
from matplotlib.path import Path # Para colores a la gráfica
from matplotlib.patches import PathPatch # Más para colores
import seaborn as sns #Libreria donde estan los colores

#TODO: acomodar mip.py, el ex run.py
#Queremos pasarle 3 paramétros, c, d y si tiene o no que mirar las restricciones de partidos
from mip.py import minimax
from seleccionador_de_partidos.py import seleccionar_partidos

def main():
    mejor_iter = 0
    mejor_sol = null
    mejor_optimo_fo = 10000
    anterior_fue_factible = True

    c = 4
    d = 14


    # El primer fixture de la ejecucion
    anterior_fue_factible, mejor_sol, mejor_optimo_fo = minimax(c, d, considerar_partidos=False)

    # Iteramos moviendo c y d
    while anterior_fue_factible:
        c+=1
        d-=1
        #TODO: armar seleccionador de partidos
        seleccionar_partidos(args.partidos, c, d)
        anterior_fue_factible, mejor_sol, mejor_optimo_fo = minimax(c, d, iter, considerar_partidos=True)

    #TODO: pensar si no habría q tirar un reporte

if __name__=="__main__":
    #TODO: arreglar flags
    # Creamos flags:
    parser = argparse.ArgumentParser(
        description='queremos fijar la cantidad de iteraciones que vamos a hacer en e'
    )
    parser.add_argument(
        "--iter",
        default='mirror',
        choices=['mirror', 'frances', 'ingles', 'invertido', 'mano_a_mano', 'minimax']
    )
    parser.add_argument(
        "--partidos",
        default='mirror',
        choices=['mirror', 'frances', 'ingles', 'invertido', 'mano_a_mano', 'minimax']
    )

    args = parser.parse_args()
    main()