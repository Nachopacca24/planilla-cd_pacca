"""Tests de la interfaz de linea de comandos."""

from planilla.cli import USO, main, parse_args


class TestParseArgs:
    def test_convierte_valores_numericos(self):
        datos = parse_args(["salario_base=4000", "horas_extra=8"])
        assert datos == {"salario_base": 4000.0, "horas_extra": 8.0}

    def test_conserva_valores_no_numericos(self):
        datos = parse_args(["afiliado_igss=no"])
        assert datos == {"afiliado_igss": "no"}

    def test_ignora_argumentos_sin_igual(self):
        datos = parse_args(["salario_base=4000", "ayuda"])
        assert datos == {"salario_base": 4000.0}

    def test_lista_vacia_da_diccionario_vacio(self):
        assert parse_args([]) == {}


class TestMain:
    def test_sin_salario_base_imprime_uso_y_retorna_1(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["planilla"])
        codigo = main()
        salida = capsys.readouterr().out
        assert codigo == 1
        assert USO in salida

    def test_con_datos_completos_imprime_resumen_y_retorna_0(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.argv",
            [
                "planilla",
                "salario_base=4000",
                "horas_extra=8",
                "dias_trabajados=30",
                "cuota_prestamo=500",
                "afiliado_igss=si",
            ],
        )
        codigo = main()
        salida = capsys.readouterr().out
        assert codigo == 0
        assert salida.strip() == "Liquido: Q3747.14 | Descuentos: Q702.86"

    def test_valores_por_defecto(self, monkeypatch, capsys):
        # Sin horas_extra/dias_trabajados/cuota_prestamo/afiliado_igss, main()
        # debe usar 0, 30, "si" (afiliado) y 0.0 respectivamente.
        monkeypatch.setattr("sys.argv", ["planilla", "salario_base=5000"])
        codigo = main()
        salida = capsys.readouterr().out
        assert codigo == 0
        assert salida.strip() == "Liquido: Q4958.5 | Descuentos: Q291.5"

    def test_no_afiliado_excluye_igss(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.argv", ["planilla", "salario_base=5000", "afiliado_igss=no"]
        )
        codigo = main()
        salida = capsys.readouterr().out
        assert codigo == 0
        assert salida.strip() == "Liquido: Q5200.0 | Descuentos: Q50.0"
