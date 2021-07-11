from docplex.mp.model import Model
import argparse
import xlsxwriter
import os
import pandas as pd
import numpy as np

from mip.py import minimax
from seleccionador_de_partidos.py import seleccionar_partidos

def main():
    mejor_c, mejor_d = 0, 18
    c, d = 4, 14

    # El primer fixture de la ejecucion
    # Vamos a asumir q siempre va a considerar el fixture pre armado, y q empieza vacio.
    anterior_fue_factible, mejor_sol, mejor_optimo_fo = minimax(c, d)

    # Iteramos moviendo c y d
    while anterior_fue_factible:
        c += 1
        d -= 1
        seleccionar_partidos(args.partidos, c, d)
        anterior_fue_factible, sol, optimo_fo = minimax(c, d)
        if optimo_fo == 0:
            mejor_sol = sol
            mejor_optimo_fo = optimo_fo
            mejor_c, mejor_d = c, d

    print(mejor_c, mejor_d, mejor_sol)


if __name__=="__main__":
    # Creamos flags:
    parser = argparse.ArgumentParser(
        description='queremos fijar la cantidad de partidos que vamos a fijar entre iteraciones'
    )
    parser.add_argument(
        "--partidos",
        default=10,
        type=int
    )

    args = parser.parse_args()
    main()