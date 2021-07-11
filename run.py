from docplex.mp.model import Model
import argparse
import xlsxwriter
import os
import pandas as pd
import numpy as np

from mip import minimax
from seleccionador_de_partidos import seleccionador_partidos

def main():
    mejor_c, mejor_d = 0, 18
    c, d = 4, 14

    # El primer fixture de la ejecucion
    # Vamos a asumir q siempre va a considerar el fixture pre armado, y q empieza vacio.
    print('empieza la magia')
    anterior_fue_factible, mejor_sol, mejor_optimo_fo = minimax(c, d)

    # Iteramos moviendo c y d
    while anterior_fue_factible:
        c += 1
        d -= 1
        print(f'seleccionador de partidos para {c} y {d}')
        seleccionador_partidos(args.partidos, c, d)
        print(f'arranca la ejecucion con {c} y {d}')
        anterior_fue_factible, sol, optimo_fo = minimax(c, d)

        #if optimo_fo == 0 and anterior_fue_factible:
        #    mejor_sol = sol
        #    mejor_c, mejor_d = c, d

    #print(f'el mejor c con fo = 0: {mejor_c}, \n su d correspondiente {mejor_d} \n su sol: {mejor_sol}')


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