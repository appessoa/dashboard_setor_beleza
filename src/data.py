"""
Camada de dados.

Contém:

* ``processar_cotahist`` — parser do layout COTAHIST da B3, idêntico ao do
  notebook original (``processar_cotahist``).
* ``aplicar_tratamentos_societarios`` — virada de ticker NTCO3 -> NATU3 e
  ajuste do grupamento 10:1 da ESPA3 (notebook, célula de definição do
  ``df_beleza``).
* ``carregar_dataset`` — leitura do parquet processado (``data/beleza.parquet``),
  com cache do Streamlit.
* ``filtrar`` — aplica os filtros globais de período e empresa.

Nenhuma lógica estatística foi alterada em relação ao notebook: apenas foi
reorganizada em funções reutilizáveis e desacoplada do Jupyter (sem
``display`` / ``print`` de depuração no caminho do dashboard).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config

try:  # Streamlit é opcional para permitir uso dos módulos fora do app.
    import streamlit as st

    _cache_data = st.cache_data
except Exception:  # pragma: no cover
    def _cache_data(*args, **kwargs):
        def _wrap(func):
            return func

        if args and callable(args[0]):
            return args[0]
        return _wrap


# --------------------------------------------------------------------------- #
# Parser COTAHIST (do notebook original)
# --------------------------------------------------------------------------- #
def processar_cotahist(caminho_arquivo: str | Path) -> pd.DataFrame:
    """
    Processa um arquivo COTAHIST da B3 (layout de largura fixa).

    Réplica fiel da função ``processar_cotahist`` do notebook:

    * mantém apenas registros de cotação (``TIPREG == '01'``);
    * converte ``DATPRG`` para datetime;
    * divide as colunas financeiras por 100 (centavos -> reais);
    * converte ``TOTNEG`` e ``QUATOT`` para numérico.
    """
    df = pd.read_fwf(
        caminho_arquivo,
        widths=config.COTAHIST_WIDTHS,
        names=config.COTAHIST_COLUNAS,
        dtype=str,
    )
    df = df[df["TIPREG"] == "01"].copy()
    df["DATPRG"] = pd.to_datetime(df["DATPRG"], format="%Y%m%d", errors="coerce")

    for col in config.COTAHIST_COLUNAS_FINANCEIRAS:
        df[col] = pd.to_numeric(df[col], errors="coerce") / 100.0

    df["TOTNEG"] = pd.to_numeric(df["TOTNEG"], errors="coerce")
    df["QUATOT"] = pd.to_numeric(df["QUATOT"], errors="coerce")
    df = df.drop(columns=["TIPREG"])
    return df


def parse_linhas_cotahist(linhas: list[str]) -> pd.DataFrame:
    """
    Igual a ``processar_cotahist``, porém a partir de uma lista de linhas já
    pré-filtradas (usado pelo script de pré-processamento para não carregar o
    arquivo COTAHIST inteiro na memória).
    """
    from io import StringIO

    if not linhas:
        return pd.DataFrame(columns=[c for c in config.COTAHIST_COLUNAS if c != "TIPREG"])

    buffer = StringIO("".join(linhas))
    df = pd.read_fwf(
        buffer,
        widths=config.COTAHIST_WIDTHS,
        names=config.COTAHIST_COLUNAS,
        dtype=str,
    )
    df = df[df["TIPREG"] == "01"].copy()
    df["DATPRG"] = pd.to_datetime(df["DATPRG"], format="%Y%m%d", errors="coerce")
    for col in config.COTAHIST_COLUNAS_FINANCEIRAS:
        df[col] = pd.to_numeric(df[col], errors="coerce") / 100.0
    df["TOTNEG"] = pd.to_numeric(df["TOTNEG"], errors="coerce")
    df["QUATOT"] = pd.to_numeric(df["QUATOT"], errors="coerce")
    return df.drop(columns=["TIPREG"])


# --------------------------------------------------------------------------- #
# Tratamentos societários (do notebook original)
# --------------------------------------------------------------------------- #
def aplicar_tratamentos_societarios(df_historico: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica os dois tratamentos societários identificados no notebook ao validar
    a análise com os dados reais:

    1. **NTCO3 -> NATU3 (01/07/2025).** A Natura&Co Holding (NTCO3) foi
       incorporada pela Natura Cosméticos; a partir de 02/07/2025 as ações
       passaram a ser negociadas como NATU3 (conversão 1:1, sem ajuste de
       preço). Os registros de NATU3 são renomeados para NTCO3, formando uma
       série contínua.

    2. **Grupamento da ESPA3, 10 para 1 (15/06/2026).** Os preços anteriores ao
       grupamento são multiplicados por 10 e a quantidade negociada (QUATOT) é
       dividida por 10, deixando a série inteira em base "pós-grupamento". O
       volume financeiro (VOLTOT) não é ajustado.
    """
    df = df_historico.copy()
    df["CODNEG"] = df["CODNEG"].str.strip()

    codigos = config.EMPRESAS_BELEZA + list(config.TICKER_RENOMEADO.keys())
    df = df[df["CODNEG"].isin(codigos)].copy()

    # 1. Virada de ticker
    for origem, destino in config.TICKER_RENOMEADO.items():
        df.loc[df["CODNEG"] == origem, "CODNEG"] = destino

    # 2. Grupamento ESPA3
    data_grupamento = pd.Timestamp(config.DATA_GRUPAMENTO_ESPA3)
    mascara_pre = (df["CODNEG"] == "ESPA3") & (df["DATPRG"] < data_grupamento)
    for col in config.COTAHIST_COLUNAS_PRECO:
        if col in df.columns:
            df.loc[mascara_pre, col] *= config.FATOR_GRUPAMENTO_ESPA3
    if "QUATOT" in df.columns:
        df.loc[mascara_pre, "QUATOT"] /= config.FATOR_GRUPAMENTO_ESPA3

    df = df.sort_values(["CODNEG", "DATPRG"]).reset_index(drop=True)
    return df


# --------------------------------------------------------------------------- #
# Carga do dataset processado (dashboard)
# --------------------------------------------------------------------------- #
@_cache_data(show_spinner="Carregando dados da B3…")
def carregar_dataset(caminho: str | None = None) -> pd.DataFrame:
    """
    Lê ``data/beleza.parquet`` (dataset já processado pelo
    ``scripts/preprocess_data.py``).

    Levanta ``FileNotFoundError`` com instrução clara se o parquet não existir.
    """
    destino = Path(caminho) if caminho else config.DATA_PATH
    if not destino.exists():
        raise FileNotFoundError(
            f"Dataset processado não encontrado em '{destino}'. "
            "Gere-o com:  python scripts/preprocess_data.py"
        )
    df = pd.read_parquet(destino)
    df["DATPRG"] = pd.to_datetime(df["DATPRG"])
    df["CODNEG"] = df["CODNEG"].astype(str)
    return df.sort_values(["CODNEG", "DATPRG"]).reset_index(drop=True)


def intervalo_datas(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Retorna (data mínima, data máxima) do dataset."""
    return df["DATPRG"].min(), df["DATPRG"].max()


def empresas_disponiveis(df: pd.DataFrame) -> list[str]:
    """Lista de tickers presentes no dataset, na ordem canônica da análise."""
    presentes = set(df["CODNEG"].unique())
    ordenadas = [e for e in config.EMPRESAS_BELEZA if e in presentes]
    extras = sorted(presentes - set(ordenadas))
    return ordenadas + extras


def filtrar(
    df: pd.DataFrame,
    empresas: list[str] | None = None,
    data_inicial: pd.Timestamp | None = None,
    data_final: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Aplica os filtros globais de empresa e período."""
    saida = df
    if empresas:
        saida = saida[saida["CODNEG"].isin(empresas)]
    if data_inicial is not None:
        saida = saida[saida["DATPRG"] >= pd.Timestamp(data_inicial)]
    if data_final is not None:
        saida = saida[saida["DATPRG"] <= pd.Timestamp(data_final)]
    return saida.copy()
