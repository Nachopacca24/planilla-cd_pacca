"""Interfaz de linea de comandos."""

import sys

from planilla.calculo import liquidar, resumen

USO = (
    "uso: planilla salario_base=4000 horas_extra=8 dias_trabajados=30 "
    "cuota_prestamo=500 afiliado_igss=si"
)


def parse_args(argv):
    """Convierte los argumentos clave=valor en un diccionario."""
    datos = {}
    for arg in argv:
        if "=" not in arg:
            continue
        clave, valor = arg.split("=", 1)
        try:
            datos[clave] = float(valor)
        except ValueError:
            datos[clave] = valor
    return datos


def main():
    """Punto de entrada del comando planilla."""
    datos = parse_args(sys.argv[1:])
    if "salario_base" not in datos:
        print(USO)
        return 1
    resultado = liquidar(
        salario_base=datos["salario_base"],
        horas_extra=datos.get("horas_extra", 0),
        dias_trabajados=datos.get("dias_trabajados", 30),
        afiliado_igss=datos.get("afiliado_igss", "si") != "no",
        cuota_prestamo=datos.get("cuota_prestamo", 0.0),
    )
    print(resumen(resultado))
    return 0


if __name__ == "__main__":
    sys.exit(main())
