""" Métodos de ayuda útiles 
en cualquier parte del código
"""

from datetime import datetime


def devuelveAñoAcademicoActual():
    hoy = datetime.now()
    if hoy.month <= 7:  # Si mes entre enero y julio
        año = hoy.year - 1
    else:  # Si mes entre julio y diciembre
        año = hoy.year

    return año
