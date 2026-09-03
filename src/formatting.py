"""Formatação de números no padrão brasileiro (do notebook original)."""

from __future__ import annotations

import math


def formatar_moeda(valor: float) -> str:
    """Formata valor em Real, padrão brasileiro (ex.: R$ 1.234,56)."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    texto = "R$ {:,.2f}".format(valor)
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual(valor: float, casas: int = 2) -> str:
    """Formata valor em percentual com vírgula decimal (ex.: 12,34%)."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    return ("{:." + str(casas) + "f}%").format(valor).replace(".", ",")


def formatar_numero(valor: float, casas: int = 0) -> str:
    """Formata número grande com separador de milhar brasileiro."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    texto = ("{:,." + str(casas) + "f}").format(valor)
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
