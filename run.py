# MP = mathematical programming
# CP = constraint programming
from docplex.mp.model import Model
import argparse
import xlsxwriter
import os

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.path import Path # Para colores a la gráfica
from matplotlib.patches import PathPatch # Más para colores
import seaborn as sns #Libreria donde estan los colores

class Metadata:
    def __init__(self):
        self.selecciones = ['BRA', 'ARG', 'COL', 'URU', 'CHI', 'PER', 'VEN', 'BOL', 'PAR', 'ECU']
        self.selecciones_top = {'BRA', 'ARG'}
        self.fechas = [f for f in range(1, 19)]
        self.fechas_impar = [f for f in range(1, 18, 2)]


class Esquema:
    def __init__(self):
        self.Restricciones = {
            'torneo_doble_rueda_todos_vs_todos',
            'torneo_doble_rueda_no_juegue_si_mismo',
            'compacidad',
            'equipos_top',
            'breaks_visitante',
            'funcion_objetivo'
        }

        self.RestriccionesEsquema()



    def RestriccionesEsquema(self):

        if args.esquema != 'mano_a_mano':
            restricciones = {
                'torneo_doble_rueda_primera_vuelta',
                'torneo_doble_rueda_segunda_vuelta'
            }
        else:
            restricciones = set()

        if args.esquema != 'mirror':
            restricciones.add('patronHA')

        restricciones.add(f'esquema_{args.esquema}')

        self.Restricciones = self.Restricciones.union(restricciones)


class Variables:
    def __init__(self, modelo, metadata):
        self.x = modelo.binary_var_dict(((e_loc, e_vis, f) for e_loc in metadata.selecciones for e_vis in metadata.selecciones for f in metadata.fechas),
                                  name='partido')
        self.y = modelo.binary_var_dict(((equipo, f) for equipo in metadata.selecciones for f in metadata.fechas_impar),
                                  name='secuenciaHA')
        self.w = modelo.binary_var_dict(((equipo, f) for equipo in metadata.selecciones for f in metadata.fechas_impar),
                                  name='break')


def creacionRestriccion(restriccion, modelo, metadata, variables):

    #region Double Round Robin

    if restriccion == 'torneo_doble_rueda_primera_vuelta':
        for e_loc in metadata.selecciones:
            for e_vis in metadata.selecciones:
                if e_loc != e_vis:
                    modelo.add_constraint(
                        modelo.sum(variables.x[(e_loc, e_vis, f)] + variables.x[(e_vis, e_loc, f)] for f in metadata.fechas[0:9]) == 1,
                        ctname=f"drr_primera_vuelta_{e_loc}_{e_vis}")

    if restriccion == 'torneo_doble_rueda_segunda_vuelta':
        for e_loc in metadata.selecciones:
            for e_vis in metadata.selecciones:
                if e_loc != e_vis:
                    modelo.add_constraint(
                        modelo.sum(variables.x[(e_loc, e_vis, f)] + variables.x[(e_vis, e_loc, f)] for f in metadata.fechas[9:18]) == 1,
                        ctname=f"drr_segunda_vuelta_{e_loc}_{e_vis}")

    if restriccion == 'torneo_doble_rueda_todos_vs_todos':
        for e_loc in metadata.selecciones:
            for e_vis in metadata.selecciones:
                if e_loc != e_vis:
                    modelo.add_constraint(
                        modelo.sum(variables.x[(e_loc, e_vis, f)] for f in metadata.fechas) == 1,
                        ctname=f"drr_se_juegue{e_loc}_{e_vis}")

    if restriccion == 'torneo_doble_rueda_no_juegue_si_mismo':
        for e_loc in metadata.selecciones:
            for e_vis in metadata.selecciones:
                if e_loc == e_vis:
                    modelo.add_constraint(
                        modelo.sum(variables.x[(e_loc, e_vis, f)] for f in metadata.fechas) == 0,
                        ctname=f"drr_no_juegue_si_mismo_{e_vis}")

    #endregion

    #region Compacidad

    if restriccion == 'compacidad':
        for equipo in metadata.selecciones:
            selecciones_sin_equipo = metadata.selecciones.copy()
            selecciones_sin_equipo.remove(equipo)
            for f in metadata.fechas:
                modelo.add_constraint(
                    modelo.sum(variables.x[(otro_equipo, equipo, f)] + variables.x[(equipo, otro_equipo, f)] for otro_equipo in selecciones_sin_equipo) == 1,
                    ctname=f"comp_{equipo}_{f}")

    #endregion

    #region Vs Equipos Top

    if restriccion == 'equipos_top':
        for e_debil in metadata.selecciones:
            if not metadata.selecciones_top.__contains__(e_debil):
                for f in metadata.fechas[0:17]:
                    modelo.add_constraint(
                        modelo.sum(variables.x[(e_debil, e_fuerte, f_)] + variables.x[(e_fuerte, e_debil, f_)] for e_fuerte in metadata.selecciones_top for f_ in [f, f + 1]) <= 1,
                        ctname=f"vsFuerte_{e_debil}_{f}")

    #endregion

    #region Patrones H-A

    if restriccion == 'patronHA':
        for e in metadata.selecciones:
            n = len(metadata.selecciones)
            modelo.add_constraint(modelo.sum(variables.y[(e, f)]for f in metadata.fechas_impar) <= n/2,
                                 ctname=f"patronesHA_cota_sup_{e}")
            modelo.add_constraint(modelo.sum(variables.y[(e, f)] for f in metadata.fechas_impar) >= n/2-1,
                                 ctname=f"patronesHA_cota_inf_{e}")

            for f in metadata.fechas_impar:
                selecciones_sin_equipo = metadata.selecciones.copy()
                selecciones_sin_equipo.remove(e)
                modelo.add_constraint(modelo.sum(variables.x[e,otro_e,f] + variables.x[otro_e,e,f+1] for otro_e in selecciones_sin_equipo) - variables.y[(e, f)] <=1,
                                     ctname=f"patronesHA_prender_y_{e}_{f}")
                modelo.add_constraint(variables.y[(e, f)] - modelo.sum(variables.x[e, otro_e, f] for otro_e in selecciones_sin_equipo) <= 0,
                    ctname=f"patronesHA_apagarH_y_{e}_{f}")
                modelo.add_constraint(variables.y[(e, f)] - modelo.sum(variables.x[otro_e, e, f+1] for otro_e in selecciones_sin_equipo) <= 0,
                    ctname=f"patronesHA_apagarA_y_{e}_{f}")

    #endregion

    #region Breaks de visitante

    if restriccion == 'breaks_visitante':
        for e in metadata.selecciones:
            for f in metadata.fechas_impar:
                selecciones_sin_equipo = metadata.selecciones.copy()
                selecciones_sin_equipo.remove(e)
                modelo.add_constraint(modelo.sum(variables.x[otro_e,e,f] + variables.x[otro_e,e,f+1] for otro_e in selecciones_sin_equipo) - variables.w[(e, f)] <=1,
                                     ctname=f"breaks_prender_w_{e}_{f}")
                modelo.add_constraint(variables.w[(e, f)] - modelo.sum(variables.x[otro_e, e, f] for otro_e in selecciones_sin_equipo) <= 0,
                    ctname=f"breaks_apagarA1_w_{e}_{f}")
                modelo.add_constraint(variables.w[(e, f)] - modelo.sum(variables.x[otro_e, e, f+1] for otro_e in selecciones_sin_equipo) <= 0,
                    ctname=f"breaks_apagarA2_w_{e}_{f}")

    #endregion

    #region Esquema Mirror:

    if restriccion == "esquema_mirror":
        for e in metadata.selecciones:
            for otro_e in metadata.selecciones:
                if e != otro_e:
                    for f in metadata.fechas[0:9]:
                        modelo.add_constraint(variables.x[(e, otro_e, f)] - variables.x[(otro_e, e, f+len(metadata.selecciones)-1)] == 0,
                                         ctname=f"Mirror__{e}_{otro_e}_{f}")

    #endregion

    #region Esquema Frances:

    if restriccion == 'esquema_frances':
        for e1 in metadata.selecciones:
            for e2 in metadata.selecciones:
                if e1 != e2:
                    modelo.add_constraint(variables.x[(e1, e2, 1)] - variables.x[(e2, e1, 2*len(metadata.selecciones)-2)] == 0,
                        ctname=f"Frances__{e1}_{e2}_{1}")
                    for f in metadata.fechas[1:9]:
                        modelo.add_constraint(variables.x[(e1, e2, f)] - variables.x[(e2, e1, f+len(metadata.selecciones)-2)] == 0,
                                         ctname=f"Frances__{e1}_{e2}_{f}")

    #endregion

    #region Esquema Ingles:

    if restriccion == 'esquema_ingles':
        for e1 in metadata.selecciones:
            for e2 in metadata.selecciones:
                if e1 != e2:
                    modelo.add_constraint(variables.x[(e1, e2, len(metadata.selecciones)-1)] - variables.x[(e2, e1, len(metadata.selecciones))] == 0,
                                          ctname=f"Ingles__{e1}_{e2}_{len(metadata.selecciones)-1}")
                    for f in metadata.fechas[1:8]:
                        modelo.add_constraint(variables.x[(e1, e2, f)] - variables.x[(e2, e1, f+len(metadata.selecciones))] == 0,
                        ctname=f"Ingles__{e1}_{e2}_{f}")


    #endregion

    # region Esquema Invertido:
    # TODO: Armar restricciones esquema invertido
    if restriccion == 'esquema_invertido':
        True

    # endregion

    # region Esquema Mano A Mano:
    # TODO: Armar restricciones esquema mano a mano
    if restriccion == 'esquema_mano_a_mano':
        True

    # endregion

    # region Esquema Minimax:
    # TODO: Armar restricciones esquema minimax
    if restriccion == 'esquema_minimax':
        True

    # endregion


def creacionModelo(metadata, esquema):

    #modelo = Model(args.esquema)
    modelo = Model(args.esquema, cts_by_name=True)
    variables = Variables(modelo, metadata)
    modelo.minimize(modelo.sum(variables.w[(e, f)] for e in metadata.selecciones for f in metadata.fechas_impar))
    for restriccion in esquema.Restricciones:
        creacionRestriccion(restriccion, modelo, metadata, variables)

    #para chequear que esté andando
    #print(modelo.export_to_string())

    return modelo


def correrModelo(modelo):
    fixture = modelo.solve(log_output=True, time_limit=10, var_value_map=True)
    print(fixture._var_value_map)
    #fixture.display()
    #print(modelo._cts_by_name['Ingles__ARG_BRA_9'])
    #fechas = [f for f in range(1,19)]
    #for f in fechas[1:8]:
    #    print(modelo._cts_by_name[f'Ingles__ARG_BRA_{f}'])
    #TODO: ver como devolver la solucio
    return fixture._var_value_map


def aExcel(solucion, metadata):
    #region Creacion excel

    direccion_actual = os.getcwd()
    excel = xlsxwriter.Workbook(f"{direccion_actual}\{args.esquema}.xlsx")
    partidos = excel.add_worksheet("fixture")
    breaks = excel.add_worksheet("breaks")
    secuenciasHA = excel.add_worksheet("patronesHA")
    #endregion

    #Generamos diccionario de posiciones de cada equipo, cantidad de breaks y cantidad de secuenciasHA
    ubicacion_por_equipo={}
    cant_breaks={}
    cant_secuenciasHA={}
    i=0
    for e in metadata.selecciones:
        ubicacion_por_equipo[e] = i
        cant_breaks[e] = 0
        cant_secuenciasHA[e] = 0
        i = i + 1

    #region Rellenada de excel

    #Ponemos primera fila y primera columna de partidos
    for e in metadata.selecciones:
        partidos.write(0, ubicacion_por_equipo[e]+1, e)
        partidos.write(ubicacion_por_equipo[e]+1, 0, e)

    #Ponemos primeras dos columnas de breaks y patrones HA:
    for e in metadata.selecciones:
        breaks.write(ubicacion_por_equipo[e]+1, 0, e)
        secuenciasHA.write(ubicacion_por_equipo[e] + 1, 0, e)

        breaks.write(ubicacion_por_equipo[e] + 1, 0, e)
        secuenciasHA.write(ubicacion_por_equipo[e] + 1, 0, e)

        breaks.write(0, 1, "breaks")
        secuenciasHA.write(0, 1, "secuenciasHA")

        breaks.write(0, 0, "equipo")
        secuenciasHA.write(0, 0, "equipo")


        #Rellenamos la tabla si es variable de partido, sino sumamos un break o una secuenciaHA:
    for variable in solucion.keys():
        nombre = variable.name
        nombre = nombre.split("_")
        if nombre[0]=='partido':
            e1 = nombre[1]
            e2 = nombre[2]
            f = nombre[3]
            partidos.write(ubicacion_por_equipo[e1] + 1, ubicacion_por_equipo[e2] + 1, f)
        if nombre[0]=="secuenciaHA":
            e = nombre[1]
            cant_secuenciasHA[e] += int(1)
        if nombre[0]=="break":
            print('a')
            e = nombre[1]
            cant_breaks[e] += int(1)

    #Rellenamos las tablas de breaks y secuenciaHA
    for e in metadata.selecciones:
        breaks.write(ubicacion_por_equipo[e] + 1, 1, cant_breaks[e])
        secuenciasHA.write(ubicacion_por_equipo[e] + 1, 1, cant_secuenciasHA[e])
    #endregion

    excel.close()


def main():
    esquema = Esquema()
    metadata = Metadata()
    modelo = creacionModelo(metadata, esquema)
    #correrModelo(modelo)
    solucion = correrModelo(modelo)
    aExcel(solucion, metadata)


if __name__=="__main__":
    # Creamos flags:
    parser = argparse.ArgumentParser(
        description='queremos fijar el tipo de esquema del fixture, valor predefino = mirror'
    )
    parser.add_argument(
        "--esquema",
        default='mirror',
        choices=['mirror', 'frances', 'ingles', 'invertido', 'mano_a_mano', 'minimax']
    )
    args = parser.parse_args()
    main()