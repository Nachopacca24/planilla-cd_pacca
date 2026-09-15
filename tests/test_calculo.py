"""Tests unitarios de las reglas de calculo.

Cada bloque cubre una funcion aplicando particion de equivalencia (clases
validas e invalidas) y valores frontera sobre los limites de esa particion.
"""

import pytest

from planilla.calculo import (
    bonificacion_incentivo,
    descuento_igss,
    descuento_isr,
    descuento_prestamo,
    isr_anual,
    pago_horas_extra,
    redondear,
    resumen,
    salario_ordinario,
    valor_hora,
    Planilla,
)


# ---------------------------------------------------------------------------
# valor_hora: particiones {salario_base <= 0 (invalida), salario_base > 0 (valida)}
# ---------------------------------------------------------------------------


class TestValorHora:
    def test_particion_valida_tipica(self):
        assert valor_hora(4000) == pytest.approx(4000 / 240)

    def test_frontera_justo_arriba_de_cero(self):
        assert valor_hora(0.01) == pytest.approx(0.01 / 240)

    def test_frontera_salario_igual_a_jornada(self):
        assert valor_hora(240) == pytest.approx(1.0)

    def test_frontera_cero_invalida(self):
        with pytest.raises(ValueError):
            valor_hora(0)

    def test_particion_invalida_negativa(self):
        with pytest.raises(ValueError):
            valor_hora(-100)


# ---------------------------------------------------------------------------
# pago_horas_extra: particion valida [0, 48], invalidas < 0 y > 48
# ---------------------------------------------------------------------------


class TestPagoHorasExtra:
    def test_frontera_cero_horas(self):
        assert pago_horas_extra(4000, 0) == 0.0

    def test_frontera_maximo_permitido(self):
        esperado = valor_hora(4000) * 1.5 * 48
        assert pago_horas_extra(4000, 48) == pytest.approx(esperado)

    def test_particion_valida_intermedia(self):
        esperado = valor_hora(4000) * 1.5 * 8
        assert pago_horas_extra(4000, 8) == pytest.approx(esperado)

    def test_frontera_justo_sobre_el_maximo_invalida(self):
        with pytest.raises(ValueError):
            pago_horas_extra(4000, 49)

    def test_particion_invalida_negativa(self):
        with pytest.raises(ValueError):
            pago_horas_extra(4000, -1)


# ---------------------------------------------------------------------------
# salario_ordinario: composicion de salario_base + pago_horas_extra
# ---------------------------------------------------------------------------


class TestSalarioOrdinario:
    def test_sin_horas_extra(self):
        assert salario_ordinario(4000, 0) == pytest.approx(4000.0)

    def test_con_horas_extra(self):
        assert salario_ordinario(4000, 8) == pytest.approx(4200.0)

    def test_propaga_error_de_horas_extra_invalidas(self):
        with pytest.raises(ValueError):
            salario_ordinario(4000, 100)


# ---------------------------------------------------------------------------
# bonificacion_incentivo: tabla de decision sobre dias_trabajados
# dias < 0            -> invalido
# 0 <= dias < 30       -> proporcional
# dias == 30           -> completa (Q250)
# dias > 30            -> invalido
# ---------------------------------------------------------------------------


class TestBonificacionIncentivo:
    def test_frontera_cero_dias(self):
        assert bonificacion_incentivo(0) == pytest.approx(0.0)

    def test_particion_valida_proporcional(self):
        assert bonificacion_incentivo(15) == pytest.approx(125.0)

    def test_frontera_justo_bajo_mes_completo(self):
        assert bonificacion_incentivo(29) == pytest.approx(250 * 29 / 30)

    def test_frontera_mes_completo(self):
        assert bonificacion_incentivo(30) == pytest.approx(250.0)

    def test_frontera_justo_sobre_mes_completo_invalida(self):
        with pytest.raises(ValueError):
            bonificacion_incentivo(31)

    def test_particion_invalida_negativa(self):
        with pytest.raises(ValueError):
            bonificacion_incentivo(-1)


# ---------------------------------------------------------------------------
# descuento_igss: tabla de decision sobre afiliado_igss
# ---------------------------------------------------------------------------


class TestDescuentoIgss:
    def test_afiliado_true_aplica_tasa(self):
        assert descuento_igss(4200.0, True) == pytest.approx(4200.0 * 0.0483)

    def test_afiliado_false_no_descuenta(self):
        assert descuento_igss(4200.0, False) == 0.0

    def test_afiliado_none_no_descuenta(self):
        assert descuento_igss(4200.0, None) == 0.0


# ---------------------------------------------------------------------------
# isr_anual: tabla de decision sobre la renta imponible
# imponible <= 0                 -> no paga
# 0 < imponible <= 300000        -> 5%
# imponible > 300000             -> Q15000 + 7% del excedente
# (imponible = renta_bruta_anual - 48000)
# ---------------------------------------------------------------------------


class TestIsrAnual:
    def test_frontera_imponible_exactamente_cero(self):
        assert isr_anual(48000) == 0.0

    def test_particion_invalida_renta_baja(self):
        assert isr_anual(40000) == 0.0

    def test_particion_valida_tramo_uno(self):
        # renta 100000 -> imponible 52000 -> 5%
        assert isr_anual(100000) == pytest.approx(2600.0)

    def test_frontera_tope_tramo_uno(self):
        # renta 348000 -> imponible exactamente 300000
        assert isr_anual(348000) == pytest.approx(15000.0)

    def test_frontera_justo_sobre_tope_tramo_uno(self):
        # renta 348001 -> imponible 300001, ya en tramo 2
        assert isr_anual(348001) == pytest.approx(15000.07)

    def test_particion_valida_tramo_dos(self):
        # renta 500000 -> imponible 452000
        assert isr_anual(500000) == pytest.approx(25640.0)


# ---------------------------------------------------------------------------
# descuento_isr: doceava parte del ISR anual, calculado sobre salario_base
# ---------------------------------------------------------------------------


class TestDescuentoIsr:
    def test_bajo_deduccion_no_paga(self):
        assert descuento_isr(4000) == 0.0

    def test_tramo_uno(self):
        assert descuento_isr(10000) == pytest.approx(300.0)

    def test_tramo_dos(self):
        assert descuento_isr(50000) == pytest.approx(2720.0)


# ---------------------------------------------------------------------------
# descuento_prestamo: tabla de decision sobre cuota vs. el piso inembargable
# cuota < 0                          -> invalida
# margen (liquido_antes - piso) <= 0 -> no se descuenta nada
# margen > 0 y cuota <= margen       -> se descuenta la cuota completa
# margen > 0 y cuota > margen        -> se descuenta solo el margen
# ---------------------------------------------------------------------------


class TestDescuentoPrestamo:
    def test_cuota_negativa_invalida(self):
        with pytest.raises(ValueError):
            descuento_prestamo(4000, 4000, -1)

    def test_cuota_cero_no_descuenta(self):
        assert descuento_prestamo(4000, 4000, 0) == 0.0

    def test_frontera_margen_exactamente_cero(self):
        # ordinario=4000, piso=1200, liquido_antes=1200 -> margen=0
        assert descuento_prestamo(1200, 4000, 500) == 0.0

    def test_margen_negativo_no_descuenta(self):
        assert descuento_prestamo(1000, 4000, 500) == 0.0

    def test_cuota_dentro_del_margen_se_descuenta_completa(self):
        # ordinario=4000, piso=1200, liquido_antes=4000 -> margen=2800
        assert descuento_prestamo(4000, 4000, 500) == pytest.approx(500.0)

    def test_cuota_excede_margen_se_limita_al_margen(self):
        assert descuento_prestamo(4000, 4000, 5000) == pytest.approx(2800.0)


# ---------------------------------------------------------------------------
# redondear y resumen
# ---------------------------------------------------------------------------


class TestRedondear:
    def test_redondea_a_dos_decimales(self):
        assert redondear(3747.1449999) == 3747.14


class TestResumen:
    def test_formato_de_linea(self):
        planilla = Planilla(
            salario_ordinario=4200.0,
            bonificacion=250.0,
            igss=202.86,
            isr=0.0,
            prestamo=500.0,
            liquido=3747.14,
        )
        assert resumen(planilla) == "Liquido: Q3747.14 | Descuentos: Q702.86"
