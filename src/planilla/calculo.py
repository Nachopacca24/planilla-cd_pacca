"""Reglas de calculo de la planilla mensual.

La especificacion de estas reglas vive en el README del repositorio.
"""

from dataclasses import dataclass

VALOR_BONIFICACION = 250.0
TASA_IGSS = 0.0483
HORAS_JORNADA_MES = 240
RECARGO_HORA_EXTRA = 1.5
MAX_HORAS_EXTRA = 48
DIAS_MES = 30
DEDUCCION_ISR_ANUAL = 48000.0
TRAMO_ISR = 300000.0
TASA_ISR_TRAMO_1 = 0.05
TASA_ISR_TRAMO_2 = 0.07
ISR_ACUMULADO_TRAMO_1 = 15000.0
FRACCION_INEMBARGABLE = 0.30

def redondear(x):
    """Redondea a dos decimales."""
    return round(x, 2)


@dataclass(frozen=True)
class Planilla:
    """Resultado de liquidar un mes."""

    salario_ordinario: float
    bonificacion: float
    igss: float
    isr: float
    prestamo: float
    liquido: float


def valor_hora(salario_base):
    """Valor de una hora ordinaria."""
    if salario_base <= 0:
        raise ValueError("el salario base debe ser mayor que cero")
    return salario_base / HORAS_JORNADA_MES


def pago_horas_extra(salario_base, horas_extra):
    """Pago total de las horas extra del mes."""
    if horas_extra < 0 or horas_extra > MAX_HORAS_EXTRA:
        raise ValueError("horas extra fuera del rango permitido")
    return valor_hora(salario_base) * RECARGO_HORA_EXTRA * horas_extra


def salario_ordinario(salario_base, horas_extra):
    """Salario base mas el pago de horas extra."""
    return salario_base + pago_horas_extra(salario_base, horas_extra)


def bonificacion_incentivo(dias_trabajados):
    """Bonificacion incentivo, proporcional si el mes quedo incompleto."""
    if dias_trabajados < 0 or dias_trabajados > DIAS_MES:
        raise ValueError("dias trabajados fuera del rango permitido")
    if dias_trabajados >= DIAS_MES:
        return VALOR_BONIFICACION
    return VALOR_BONIFICACION * dias_trabajados / DIAS_MES


def descuento_igss(salario_ordinario_mes, afiliado):
    """Cuota laboral del IGSS sobre el salario ordinario."""
    if afiliado is None:
        return 0.0
    if not afiliado:
        return 0.0
    return salario_ordinario_mes * TASA_IGSS


def isr_anual(renta_bruta_anual):
    """ISR anual segun los dos tramos."""
    imponible = renta_bruta_anual - DEDUCCION_ISR_ANUAL
    if imponible <= 0:
        return 0.0
    if imponible <= TRAMO_ISR:
        return imponible * TASA_ISR_TRAMO_1
    return ISR_ACUMULADO_TRAMO_1 + (imponible - TRAMO_ISR) * TASA_ISR_TRAMO_2


def descuento_isr(salario_base):
    """Doceava parte del ISR anual."""
    anual = isr_anual(salario_base * 12)
    return anual / 12


def descuento_prestamo(liquido_antes, salario_ordinario_mes, cuota):
    """Cuota de prestamo efectivamente descontada, respetando el piso."""
    if cuota < 0:
        raise ValueError("la cuota del prestamo no puede ser negativa")
    piso = salario_ordinario_mes * FRACCION_INEMBARGABLE
    margen = liquido_antes - piso
    if margen <= 0:
        return 0.0
    return min(cuota, margen)


def liquidar(
    salario_base,
    horas_extra=0,
    dias_trabajados=DIAS_MES,
    afiliado_igss=True,
    cuota_prestamo=0.0,
):
    """Liquida un mes completo y devuelve el desglose."""
    ordinario = salario_ordinario(salario_base, horas_extra)
    bono = bonificacion_incentivo(dias_trabajados)
    igss = descuento_igss(ordinario, afiliado_igss)
    isr = descuento_isr(salario_base)
    antes = ordinario + bono - igss - isr
    prestamo = descuento_prestamo(antes, ordinario, cuota_prestamo)
    return Planilla(ordinario, bono, igss, isr, prestamo, antes - prestamo)


def resumen(planilla):
    """Linea de resumen para imprimir en consola."""
    liquido = redondear(planilla.liquido)
    total_descuentos = redondear(planilla.igss + planilla.isr + planilla.prestamo)
    return f"Liquido: Q{liquido} | Descuentos: Q{total_descuentos}"
