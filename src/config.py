"""
Configuração central do dashboard.

Todos os caminhos são construídos de forma RELATIVA ao projeto
(``Path(__file__).resolve().parent``), para que a aplicação funcione tanto
localmente (Windows/Linux/macOS) quanto no Streamlit Community Cloud.

As constantes de análise (tickers, paleta das marcas, empresa foco, datas de
eventos societários) foram extraídas diretamente do notebook original
``notebook/notebook_original.ipynb`` e NÃO devem ser alteradas sem revisar a
metodologia lá descrita.
"""

from __future__ import annotations

import os
from pathlib import Path

try:  # python-dotenv é opcional; o app funciona sem ele.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - fallback quando dotenv não está instalado
    pass


# --------------------------------------------------------------------------- #
# Caminhos (sempre relativos ao projeto)
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = Path(os.getenv("DATA_PATH", BASE_DIR / "data" / "beleza.parquet"))
if not DATA_PATH.is_absolute():
    DATA_PATH = BASE_DIR / DATA_PATH

ASSETS_PATH = Path(os.getenv("ASSETS_PATH", BASE_DIR / "assets"))
if not ASSETS_PATH.is_absolute():
    ASSETS_PATH = BASE_DIR / ASSETS_PATH

RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", BASE_DIR / "data" / "raw"))
if not RAW_DATA_PATH.is_absolute():
    RAW_DATA_PATH = BASE_DIR / RAW_DATA_PATH

LOGO_PATH = ASSETS_PATH / "logo_natura.png"
ILLUSTRATIONS = {
    "imagem_01": ASSETS_PATH / "imagem_01.png",
    "imagem_02": ASSETS_PATH / "imagem_02.png",
    "imagem_03": ASSETS_PATH / "imagem_03.png",
}


# --------------------------------------------------------------------------- #
# Constantes da análise (do notebook original)
# --------------------------------------------------------------------------- #
# Ações do setor de beleza e cuidados pessoais analisadas.
EMPRESAS_BELEZA = ["NTCO3", "COTY34", "HYPE3", "PNVL3", "RADL3", "ESPA3"]

# Empresa foco da consultoria (Natura).
EMPRESA_FOCO = "NTCO3"

# Virada de ticker NTCO3 -> NATU3 em 01/07/2025 (mesma empresa).
TICKER_RENOMEADO = {"NATU3": "NTCO3"}
DATA_TROCA_TICKER = "2025-07-01"

# Grupamento de ações da ESPA3, 10 para 1, em 15/06/2026.
DATA_GRUPAMENTO_ESPA3 = "2026-06-15"
FATOR_GRUPAMENTO_ESPA3 = 10

# Layout de arquivo COTAHIST da B3 (série histórica, mercado à vista).
COTAHIST_WIDTHS = [
    2, 8, 2, 12, 3, 12, 10, 3, 4, 13, 13, 13, 13, 13, 13, 13,
    5, 18, 18, 13, 1, 8, 7, 13, 12, 3,
]
COTAHIST_COLUNAS = [
    "TIPREG", "DATPRG", "CODBDI", "CODNEG", "TPMERC", "NOMRES", "ESPECI",
    "PRAZOT", "MODREF", "PREABE", "PREMAX", "PREMIN", "PREMED", "PREULT",
    "PREOFC", "PREOFV", "TOTNEG", "QUATOT", "VOLTOT", "PREEXE", "INDOPC",
    "DATVEN", "FATCOT", "PTOEXE", "CODISI", "DISMES",
]
COTAHIST_COLUNAS_FINANCEIRAS = [
    "PREABE", "PREMAX", "PREMIN", "PREMED", "PREULT",
    "PREOFC", "PREOFV", "VOLTOT", "PREEXE",
]
COTAHIST_COLUNAS_PRECO = ["PREABE", "PREMAX", "PREMIN", "PREMED", "PREULT", "PREOFC", "PREOFV"]

# Colunas mantidas no dataset processado (data/beleza.parquet).
COLUNAS_DATASET = [
    "DATPRG", "CODNEG", "PREABE", "PREMAX", "PREMIN", "PREMED",
    "PREULT", "VOLTOT", "TOTNEG", "QUATOT",
]

# Teste A/B do notebook (Etapa 4).
TESTE_AB_GRUPO_A = "NTCO3"
TESTE_AB_GRUPO_B = "RADL3"
TESTE_AB_ALPHA = 0.05

# Meses em português (módulo de sazonalidade).
MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

# Datas comemorativas investigadas no módulo de sazonalidade (HIPÓTESES, não
# relações causais comprovadas).
MESES_SAZONAIS = {
    5: "Dia das Mães",
    6: "Dia dos Namorados",
    8: "Dia dos Pais",
    11: "Black Friday",
    12: "Natal",
}


# --------------------------------------------------------------------------- #
# Identidade visual — paleta das marcas (do notebook original)
# --------------------------------------------------------------------------- #
CORES_MARCAS = {
    "NTCO3": {"escuro": "#B8750F", "principal": "#F4AB34", "claro": "#F9D28A"},
    "RADL3": {"escuro": "#006B3C", "principal": "#00A859", "claro": "#66D1A0"},
    "HYPE3": {"escuro": "#0755A0", "principal": "#1185F0", "claro": "#70B7F7"},
    "PNVL3": {"escuro": "#01245A", "principal": "#013684", "claro": "#6685B0"},
    "ESPA3": {"escuro": "#007A9D", "principal": "#00B2E4", "claro": "#66D0EE"},
    "COTY34": {"escuro": "#3E1F43", "principal": "#63316B", "claro": "#A984AE"},
}

NOMES_EMPRESAS = {
    "NTCO3": "Natura &Co",
    "RADL3": "Raia Drogasil",
    "HYPE3": "Hypera Pharma",
    "PNVL3": "Grupo Dimed / Panvel",
    "ESPA3": "Espaçolaser",
    "COTY34": "Coty Inc. (BDR)",
}


# --------------------------------------------------------------------------- #
# Temas (infográfico editorial) — cores definidas no briefing do projeto
# --------------------------------------------------------------------------- #
TEMA_CLARO = {
    "nome": "claro",
    "bg": "#FAF9F6",
    "bg_bloco": "#F4EFE7",
    "bg_bloco_alt": "#FFFFFF",
    "texto": "#263238",
    "texto_secundario": "#5B6B70",
    "verde": "#006B3C",
    "laranja": "#F28C28",
    "terracota": "#D96C4F",
    "bege": "#F4EFE7",
    "borda": "#E2DED3",
    "grid": "rgba(38,50,56,0.12)",
    "plotly_template": "plotly_white",
}

TEMA_ESCURO = {
    "nome": "escuro",
    "bg": "#101817",
    "bg_bloco": "#18221F",
    "bg_bloco_alt": "#1F2B27",
    "texto": "#F5F5F5",
    "texto_secundario": "#A9B4B0",
    "verde": "#00A859",
    "laranja": "#F4AB34",
    "terracota": "#E4886B",
    "bege": "#2A332F",
    "borda": "#2E3A36",
    "grid": "rgba(245,245,245,0.12)",
    "plotly_template": "plotly_dark",
}

TEMAS = {"claro": TEMA_CLARO, "escuro": TEMA_ESCURO}


# --------------------------------------------------------------------------- #
# Rodapé (texto exato exigido no briefing)
# --------------------------------------------------------------------------- #
FOOTER = {
    "linha_1": "Séries Históricas B3 (2025-2026)",
    "professor": "Eronides da Silva Neto",
    "curso": "Especialização em Engenharia de Dados",
    "dataset_url": (
        "https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/"
        "market-data/historico/mercado-a-vista/series-historicas/"
    ),
    "aluno": "Ana Paula Ferreira Pessoa",
}

TITULO_APP = (
    "Análise Exploratória: Tendências e Evolução do Setor de Beleza "
    "no Mercado Financeiro"
)


def tema(nome: str) -> dict:
    """Retorna o dicionário de tema (claro/escuro), com fallback para claro."""
    return TEMAS.get(nome, TEMA_CLARO)
