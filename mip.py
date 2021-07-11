# MP = mathematical programming
# CP = constraint programming
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

class Metadata:
    def __init__(self, c: int = -1, d: int = -1):
        self.selecciones = ['BRA', 'ARG', 'COL', 'URU', 'CHI', 'PER', 'VEN', 'BOL', 'PAR', 'ECU']
        self.selecciones_top = {'BRA', 'ARG'}
        self.fechas = [f for f in range(1, 19)]
        self.fechas_impar = [f for f in range(1, 18, 2)]
        self.fixture_pre_armado = pd.read_excel('fixture_pre_armado.xlsx',
                                                engine='openpyxl')
        self.minimax = [c, d]


class Esquema:
    def __init__(self):
        self.Restricciones = {
            'torneo_doble_rueda_todos_vs_todos',
            'torneo_doble_rueda_no_juegue_si_mismo',
            'compacidad',
            'breaks_visitante',
            'funcion_objetivo',
            'fixture_pre_armado',
            'equipos_top',
            'patronHA',
            'esquema_minimax'
        }


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

    if restriccion == 'esquema_invertido':
        for e1 in metadata.selecciones:
            for e2 in metadata.selecciones:
                if e1 != e2:
                    for f in metadata.fechas[0:9]:
                        modelo.add_constraint(variables.x[(e1, e2, f)] - variables.x[(e2, e1, 2*len(metadata.selecciones)-1-f)] == 0,
                                              ctname=f"Invertido__{e1}_{e2}_{f}")

    # endregion

    # region Esquema Mano A Mano:

    if restriccion == 'esquema_mano_a_mano':
        for e1 in metadata.selecciones:
            for e2 in metadata.selecciones:
                if e1 != e2:
                    for f in metadata.fechas_impar:
                        modelo.add_constraint(variables.x[(e1, e2, f)] - variables.x[(e2, e1, f+1)] == 0,
                                              ctname=f"Mano_a_mano__{e1}_{e2}_{f}")

    if restriccion == 'equipos_top_esquema_mano_a_mano':
        for e_debil in metadata.selecciones:
                if not metadata.selecciones_top.__contains__(e_debil):
                    for f in metadata.fechas_impar[0:8]:
                        modelo.add_constraint(
                            modelo.sum(
                                variables.x[(e_debil, e_fuerte, f_)] + variables.x[(e_fuerte, e_debil, f_)] for e_fuerte in metadata.selecciones_top for f_ in [f, f + 2]) <= 1,
                                ctname=f"vsFuerte_Mano_a_mano__{e_debil}_{f}")


    # endregion

    # region Esquema Minimax:

    if restriccion == 'esquema_minimax':
        c = metadata.minimax[0]
        d = metadata.minimax[1]
        for e1 in metadata.selecciones:
            for e2 in metadata.selecciones:
                if e1 != e2:
                    for f in metadata.fechas[0:18-c]:
                        modelo.add_constraint(
                            modelo.sum(
                                variables.x[(e1, e2, f_)] + variables.x[(e2, e1, f_)] for f_ in [z for z in range(f, f+c+1)]) <= 1,
                            ctname=f"Minimax_1__{e1}_{e2}_{f}")
                    for f in metadata.fechas:
                        fechas_sin_f = list(range(max(f-d,1), min(f+d,2*len(metadata.selecciones)-1)))
                        fechas_sin_f.remove(f)
                        modelo.add_constraint(
                            variables.x[(e2, e1, f)] - modelo.sum(variables.x[(e1, e2, f_)] for f_ in fechas_sin_f) <= 0,
                            ctname=f"Minimax_2__{e1}_{e2}_{f}")



    # endregion

    # region Fixture Pre-Armado:
    if restriccion == 'fixture_pre_armado':
        df = metadata.fixture_pre_armado
        if df.shape != (0,0):
            df = df.fillna('NO DATA')
            for e in metadata.selecciones:
                for f in metadata.fechas:
                    valor = df[df.Team == e][f].values[0]
                    if valor != 'NO DATA':
                        if valor.startswith('@'):
                            otro_e = valor[1:]
                            modelo.add_constraint(
                                variables.x[(otro_e, e, f)] == 1,
                                ctname=f"Fixture_pre_armado__{e}_{otro_e}_{f}")
                        else:
                            otro_e = valor
                            modelo.add_constraint(
                                variables.x[(e, otro_e, f)] == 1,
                                ctname=f"Fixture_pre_armado__{e}_{otro_e}_{f}")

    # endregion


def creacionModelo(metadata, esquema):

    modelo = Model('minimax', cts_by_name=True)
    variables = Variables(modelo, metadata)
    modelo.minimize(modelo.sum(variables.w[(e, f)] for e in metadata.selecciones for f in metadata.fechas_impar))
    for restriccion in esquema.Restricciones:
        creacionRestriccion(restriccion, modelo, metadata, variables)
    #print(esquema.Restricciones)
    #para chequear que esté andando
    #print(modelo.export_to_string())

    return modelo


def difEntrePartidos(solucion, metadata):
    #region Calculo diferencia minima y maxima
    diferencias = []
    f1 = 0
    f2 = 0
    for e1 in metadata.selecciones:
        for e2 in metadata.selecciones:
            if e1 != e2:
                for f in metadata.fechas:
                    for variable in solucion.keys():
                        variable = variable.name
                        if variable == f"partido_{e1}_{e2}_{f}":
                            f1 = f
                        if variable == f"partido_{e2}_{e1}_{f}":
                            f2 = f
                diferencias.append(abs(f1-f2))
    min_diff = min(diferencias)
    max_diff = max(diferencias)
    return [min_diff, diferencias.count(min_diff)/2, max_diff, diferencias.count(max_diff)/2]


def aExcel(solucion, metadata):
    #region Creacion excel

    c = metadata.minimax[0]
    d = metadata.minimax[1]
    direccion_actual = os.getcwd()
    excel = xlsxwriter.Workbook(f"{direccion_actual}\minimax_{c}_{d}.xlsx")
    partidos = excel.add_worksheet(f"Fixture minimax")
    breaks = excel.add_worksheet("Breaks y secuencias")
    min_max = excel.add_worksheet("Diferencia entre partidos")
    partidos_acum = excel.add_worksheet("Partidos acumulados")
    bold = excel.add_format({'bold': True})
    #endregion

    #region Generacion diccionarios
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
    #endregion

    #region Rellenado de excel

    #Ponemos primera columna de nombres de equipos en partidos y breaks
    #Ponemos primera fila de numero de fechas en partidos
    for e in metadata.selecciones:
        partidos.write(ubicacion_por_equipo[e]+1, 0, e,  bold)
        breaks.write(ubicacion_por_equipo[e]+1, 0, e,  bold)
        partidos_acum.write(ubicacion_por_equipo[e] + 1, 0, e, bold)

    for i in range(18):
        partidos.write(0, i+1, i+1, bold)
        partidos_acum.write(0, i+1, i+1, bold)

    #Ponemos titulos a las columnas en partidos y breaks
    partidos.write(0, 0, "Team", bold)
    partidos_acum.write(0, 0, "Team", bold)
    breaks.write(0, 0, "Team", bold)
    breaks.write(0, 1, "Breaks", bold)
    breaks.write(0, 2, "H-A", bold)
    breaks.write(0, 3, "A-H", bold)

    #Rellenamos la tabla si es variable de partido, sino sumamos un break o una secuenciaHA:
    for variable in solucion.keys():
        nombre = variable.name
        nombre = nombre.split("_")
        if nombre[0]=='partido':
            e1 = nombre[1]
            e2 = nombre[2]
            f = nombre[3]
            partidos.write(ubicacion_por_equipo[e1] + 1, int(f), e2)
            partidos.write(ubicacion_por_equipo[e2] + 1, int(f), f"@{e1}")
        if nombre[0]=="secuenciaHA":
            e = nombre[1]
            cant_secuenciasHA[e] += int(1)
        if nombre[0]=="break":
            e = nombre[1]
            cant_breaks[e] += int(1)

    #Rellenamos la tabla de partidos acumulados
    for e in metadata.selecciones:
        contador = 0
        for f in range(1,19):
            for variable in solucion.keys():
                nombre = variable.name
                nombre = nombre.split("_")
                if (nombre[0] == 'partido') and (str(nombre[2]) == e) and (int(nombre[3]) == f):
                    contador += 1
                partidos_acum.write(ubicacion_por_equipo[e]+1, int(f), contador)


    #Rellenamos la tabla de breaks
    for e in metadata.selecciones:
        breaks.write(ubicacion_por_equipo[e] + 1, 1, cant_breaks[e])
        breaks.write(ubicacion_por_equipo[e] + 1, 2, cant_secuenciasHA[e])
        breaks.write(ubicacion_por_equipo[e] + 1, 3, 9 - cant_breaks[e] - cant_secuenciasHA[e])

    #Completamos la diferencia entre partidos
    diferencias = difEntrePartidos(solucion, metadata)
    min_max.write(0, 0, "Minima diferencia", bold)
    min_max.write(0, 1, diferencias[0])
    min_max.write(0,2, f"{int(diferencias[1])} veces")
    min_max.write(1, 0, "Maxima diferencia", bold)
    min_max.write(1, 1, diferencias[2])
    min_max.write(1, 2, f"{int(diferencias[3])} veces")
    min_max.set_column(0, 0, len("Maxima diferencia"))
    min_max.set_column(1, 1, 4)
    #endregion

    excel.close()


def minimax(c, d):
    esquema = Esquema()
    metadata = Metadata(c, d)
    modelo = creacionModelo(metadata, esquema)

    #corremos el modelo
    fixture = modelo.solve(log_output=True, time_limit=1500, var_value_map=True)

    if fixture != None:
        solucion = fixture._var_value_map
        aExcel(solucion, metadata)

        return True
        #return True, solucion

    else:
        return False
        #return False, None