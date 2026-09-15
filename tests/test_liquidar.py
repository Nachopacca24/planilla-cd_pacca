"""Tests de integracion de liquidar().

Tabla de decision que combina las variables de entrada (afiliacion, horas
extra, dias trabajados y prestamo) en escenarios representativos, mas casos
de frontera y de error que atraviesan varias reglas a la vez.
"""

import pytest

from planilla.calculo import liquidar


class TestLiquidarEscenarios:
    def test_mes_completo_afiliado_con_extra_y_prestamo(self):
        r = liquidar(
            salario_base=4000,
            horas_extra=8,
            dias_trabajados=30,
            afiliado_igss=True,
            cuota_prestamo=500,
        )
        assert r.salario_ordinario == pytest.approx(4200.0)
        assert r.bonificacion == pytest.approx(250.0)
        assert r.igss == pytest.approx(202.86)
        assert r.isr == pytest.approx(0.0)
        assert r.prestamo == pytest.approx(500.0)
        assert r.liquido == pytest.approx(3747.14)

    def test_no_afiliado_sin_extra_sin_prestamo(self):
        r = liquidar(
            salario_base=5000,
            horas_extra=0,
            dias_trabajados=30,
            afiliado_igss=False,
            cuota_prestamo=0,
        )
        assert r.igss == 0.0
        assert r.isr == pytest.approx(50.0)
        assert r.prestamo == 0.0
        assert r.liquido == pytest.approx(5200.0)

    def test_mes_parcial_afiliado_sin_extra_sin_prestamo(self):
        r = liquidar(
            salario_base=3000,
            horas_extra=0,
            dias_trabajados=15,
            afiliado_igss=True,
            cuota_prestamo=0,
        )
        assert r.bonificacion == pytest.approx(125.0)
        assert r.igss == pytest.approx(144.9)
        assert r.liquido == pytest.approx(2980.1)

    def test_prestamo_grande_se_limita_al_piso_inembargable(self):
        r = liquidar(
            salario_base=2000,
            horas_extra=0,
            dias_trabajados=30,
            afiliado_igss=True,
            cuota_prestamo=2000,
        )
        piso = r.salario_ordinario * 0.30
        assert r.prestamo == pytest.approx(1553.4)
        assert r.liquido == pytest.approx(piso)

    def test_salario_alto_cae_en_segundo_tramo_de_isr(self):
        r = liquidar(
            salario_base=50000,
            horas_extra=0,
            dias_trabajados=30,
            afiliado_igss=True,
            cuota_prestamo=0,
        )
        assert r.isr == pytest.approx(2720.0)
        assert r.liquido == pytest.approx(45115.0)

    def test_frontera_horas_extra_maximas_y_dias_minimos(self):
        r = liquidar(
            salario_base=4000,
            horas_extra=48,
            dias_trabajados=0,
            afiliado_igss=True,
            cuota_prestamo=0,
        )
        assert r.salario_ordinario == pytest.approx(5200.0)
        assert r.bonificacion == pytest.approx(0.0)
        assert r.liquido == pytest.approx(4948.84)

    def test_valores_por_defecto_equivalen_a_mes_completo_afiliado(self):
        r = liquidar(salario_base=4000)
        r_explicito = liquidar(
            salario_base=4000,
            horas_extra=0,
            dias_trabajados=30,
            afiliado_igss=True,
            cuota_prestamo=0.0,
        )
        assert r == r_explicito

    def test_bonificacion_no_paga_igss(self):
        # El IGSS se calcula sobre el ordinario, la bonificacion queda fuera.
        r = liquidar(salario_base=4000, dias_trabajados=30, afiliado_igss=True)
        assert r.igss == pytest.approx(r.salario_ordinario * 0.0483)

    def test_bonificacion_no_paga_isr(self):
        # El ISR se calcula solo sobre el salario base, sin la bonificacion.
        r = liquidar(salario_base=4000, dias_trabajados=30)
        assert r.isr == pytest.approx(0.0)


class TestLiquidarErroresPropagados:
    def test_salario_base_invalido(self):
        with pytest.raises(ValueError):
            liquidar(salario_base=0)

    def test_horas_extra_invalidas(self):
        with pytest.raises(ValueError):
            liquidar(salario_base=4000, horas_extra=49)

    def test_dias_trabajados_invalidos(self):
        with pytest.raises(ValueError):
            liquidar(salario_base=4000, dias_trabajados=31)

    def test_cuota_prestamo_negativa(self):
        with pytest.raises(ValueError):
            liquidar(salario_base=4000, cuota_prestamo=-1)
