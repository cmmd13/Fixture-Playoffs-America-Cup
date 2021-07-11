import pandas as pd
import xlsxwriter as xls
import numpy as np
import os

def partidos_posibles_(c, d):
    fixture = pd.read_excel(f'minimax_{c}_{d}', engine='openpyxl')
    partidos_posibles = []
    for i in fixture.index:
        equipo1 = fixture['Team'][i]

        #encontramos las fechas en las q juegan
        for equipo2 in fixture['Team']:
            if equipo2 != equipo1:
                for fecha in range(1, 19):
                    if fixture[fecha][i] == "@" + equipo2:
                        fecha_partido1 = fecha
                    elif fixture[fecha][i] == equipo2:
                        fecha_partido2 = fecha

                distancia_partidos = np.abs(fecha_partido1-fecha_partido2)
                respeta_distancia = c <= distancia_partidos and d >= distancia_partidos

                esta_repetido = False
                for partidos_posible in partidos_posibles:
                    if equipo1 == partidos_posible[1] and equipo2 == partidos_posible[0]:
                        esta_repetido = True

                if not(esta_repetido) and respeta_distancia:
                    partidos_posibles.append([equipo1, equipo2, fecha_partido1, fecha_partido2])

    #Armamos el dataframe:
    partidos_posibles = pd.DataFrame(partidos_posibles,
                                     columns=['equipo1', 'equipo2', 'fecha_partido1', 'fecha_partido2'])

    return partidos_posibles


def crear_fixture_pre_armado(partidos_seleccionados):
    #region CreateExcel
    direccion_actual = os.getcwd()
    excel = xls.Workbook(direccion_actual + "\\" + "fixture_pre_armado.xlsx")
    partidos = excel.add_worksheet("Fixture")
    bold = excel.add_format({'bold': True})
    #endregion

    #region FillingExcel
    #el diccionario para saber a donde ubicar cada equipo:
    ubicacion_equipo = {
        'ARG': 1,
        'BOL': 2,
        'BRA': 3,
        'CHI': 4,
        'COL': 5,
        'ECU': 6,
        'PAR': 7,
        'PER': 8,
        'URU': 9,
        'VEN': 10
    }

    #La fila primera:
    partidos.write(0, 0, "Team", bold)
    for i in range(18):
        partidos.write(0, i+1, i+1, bold)

    #La primera columna:
    for equipo, ubicacion in ubicacion_equipo.items():
        partidos.write(ubicacion, 0, equipo, bold)

    #Rellenamos la carne del excel
    for i in partidos_seleccionados.index:
        equipo1 = partidos_seleccionados['equipo1'][i]
        equipo2 = partidos_seleccionados['equipo2'][i]
        fecha1 = partidos_seleccionados['fecha_partido1'][i]
        fecha2 = partidos_seleccionados['fecha_partido2'][i]

        partidos.write(ubicacion_equipo[equipo1], fecha1, "@" + equipo2)
        partidos.write(ubicacion_equipo[equipo1], fecha2, equipo2)
        partidos.write(ubicacion_equipo[equipo2], fecha1, equipo1)
        partidos.write(ubicacion_equipo[equipo2], fecha2, "@" + equipo1)

    #endregion

    excel.close()


def seleccionador_partidos(cantidad_partidos_pedidos, c, d):
    partidos_posibles = partidos_posibles_(c, d)

    cantidad_partidos_posibles = partidos_posibles.shape[0]
    if cantidad_partidos_posibles < cantidad_partidos_pedidos:
        print(f'no fue posible obtener {cantidad_partidos_pedidos}')
        partidos_seleccionados = pd.DataFrame(columns=['equipo1', 'equipo2', 'fecha_partido1', 'fecha_partido2'])
    else:
        partidos_seleccionados = partidos_posibles.sample(cantidad_partidos_pedidos)

    print('Creando fixture_pre_armado')
    crear_fixture_pre_armado(partidos_seleccionados)