# MP = mathematical programming
# CP = constraint programming
from docplex.mp.model import Model
import argparse

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
                        modelo.add_constraint(variables.x[(e, otro_e, f)] - variables.x[(otro_e, e, f+len(metadata.fechas)/2)] == 0,
                                         ctname=f"Mirror__{e}_{otro_e}_{f}")

    #endregion

    #region Esquema Frances:
    # TODO: Armar restricciones esquema frances
    if restriccion == 'esquema_frances':
        True
    #endregion

    #region Esquema Ingles:
    # TODO: Armar restricciones esquema ingles
    if restriccion == 'esquema_ingles':
        True

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

    modelo = Model(args.esquema)
    variables = Variables(modelo, metadata)
    modelo.minimize(modelo.sum(variables.w[(e, f)] for e in metadata.selecciones for f in metadata.fechas_impar))
    for restriccion in esquema.Restricciones:
        creacionRestriccion(restriccion, modelo, metadata, variables)

    #para chequear que esté andando
    #print(modelo.export_to_string())

    return modelo


def correrModelo(modelo):
    fixture = modelo.solve(log_output=True, time_limit=1)
    fixture.display()
    print(modelo.get_solve_status())
    #TODO: ver como devolver la solucion


def creacionResumen(solucion):
    True
#TODO: hacer el creador del resumen


def main():
    esquema = Esquema()
    metadata = Metadata()
    modelo = creacionModelo(metadata, esquema)
    correrModelo(modelo)
    #solucion = correrModelo(modelo)
    #creacionResumen(solucion)


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