"""
Pré-processamento dos arquivos COTAHIST da B3 -> data/beleza.parquet

Por que este script existe
--------------------------
Os arquivos ``COTAHIST_A2025.TXT`` / ``COTAHIST_A2026.TXT`` têm ~1,4 GB e ~5,7
milhões de linhas (TODAS as ações da B3). Ler o arquivo inteiro toda vez que o
Streamlit inicia é inviável. Este script:

1. localiza os arquivos COTAHIST (ver ``_localizar_arquivos``);
2. faz uma varredura linha a linha, mantendo apenas registros de cotação
   (``TIPREG == '01'``) dos tickers usados na análise — sem carregar o arquivo
   inteiro na memória;
3. aplica o mesmo parser do notebook (``processar_cotahist`` /
   ``parse_linhas_cotahist``);
4. aplica os tratamentos societários (NTCO3->NATU3, grupamento 10:1 da ESPA3);
5. grava um dataset enxuto em ``data/beleza.parquet``.

Uso
---
    python scripts/preprocess_data.py
    python scripts/preprocess_data.py --raw "C:/caminho/para/os/COTAHIST"
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

# Permite executar como script solto (python scripts/preprocess_data.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402
from src.data import aplicar_tratamentos_societarios, parse_linhas_cotahist  # noqa: E402

# Offsets (0-indexados) do layout COTAHIST usados no pré-filtro.
_TIPREG = slice(0, 2)
_CODNEG = slice(12, 24)

TICKERS_ALVO = set(config.EMPRESAS_BELEZA) | set(config.TICKER_RENOMEADO.keys())


def _localizar_arquivos(raw_dir: Path | None) -> list[Path]:
    """
    Procura arquivos COTAHIST em, na ordem:

    * ``--raw`` / ``RAW_DATA_PATH`` (se informado);
    * ``data/raw/`` do projeto;
    * a pasta-pai do projeto (onde ficam os TXT originais deste trabalho);
    * o diretório atual.
    """
    locais = []
    if raw_dir:
        locais.append(Path(raw_dir))
    locais += [
        config.RAW_DATA_PATH,
        config.BASE_DIR.parent,
        Path.cwd(),
    ]

    encontrados: list[Path] = []
    vistos: set[Path] = set()
    for pasta in locais:
        if not pasta or not pasta.exists():
            continue
        for padrao in ("COTAHIST_A*.TXT", "COTAHIST_A*.txt", "COTAHIST*.TXT"):
            for arquivo in sorted(pasta.glob(padrao)):
                chave = arquivo.resolve()
                if chave not in vistos:
                    vistos.add(chave)
                    encontrados.append(arquivo)
        if encontrados:
            break
    return encontrados


def _filtrar_linhas(caminho: Path) -> list[str]:
    """Varre o arquivo linha a linha e retorna apenas as linhas de interesse."""
    linhas: list[str] = []
    total = 0
    t0 = time.time()
    with open(caminho, "r", encoding="latin-1") as fh:
        for linha in fh:
            total += 1
            if linha[_TIPREG] != "01":
                continue
            if linha[_CODNEG].strip() in TICKERS_ALVO:
                linhas.append(linha)
    print(
        f"  {caminho.name}: {total:,} linhas varridas, "
        f"{len(linhas):,} registros mantidos ({time.time() - t0:.1f}s)"
    )
    return linhas


def preprocessar(raw_dir: Path | None = None, destino: Path | None = None) -> Path:
    destino = destino or config.DATA_PATH
    arquivos = _localizar_arquivos(raw_dir)
    if not arquivos:
        raise FileNotFoundError(
            "Nenhum arquivo COTAHIST encontrado. Coloque os arquivos "
            "'COTAHIST_A2025.TXT' / 'COTAHIST_A2026.TXT' em 'data/raw/' "
            "ou informe a pasta com --raw."
        )

    print(f"Arquivos COTAHIST encontrados: {[a.name for a in arquivos]}")
    partes = []
    for arquivo in arquivos:
        linhas = _filtrar_linhas(arquivo)
        parte = parse_linhas_cotahist(linhas)
        if not parte.empty:
            partes.append(parte)

    if not partes:
        raise RuntimeError("Nenhum registro dos tickers-alvo foi encontrado nos arquivos.")

    df_historico = pd.concat(partes, ignore_index=True)
    df_beleza = aplicar_tratamentos_societarios(df_historico)

    colunas = [c for c in config.COLUNAS_DATASET if c in df_beleza.columns]
    df_final = (
        df_beleza[colunas]
        .dropna(subset=["DATPRG", "CODNEG", "PREULT"])
        .drop_duplicates(subset=["DATPRG", "CODNEG"])
        .sort_values(["CODNEG", "DATPRG"])
        .reset_index(drop=True)
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_parquet(destino, index=False)

    print("\nDataset processado gravado em:", destino)
    print("Dimensões:", df_final.shape)
    print("Registros por empresa:")
    print(df_final["CODNEG"].value_counts().to_string())
    print(
        "Período:",
        df_final["DATPRG"].min().date(),
        "->",
        df_final["DATPRG"].max().date(),
    )
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera data/beleza.parquet a partir dos COTAHIST da B3.")
    parser.add_argument("--raw", type=str, default=None, help="Pasta com os arquivos COTAHIST_A*.TXT")
    parser.add_argument("--out", type=str, default=None, help="Caminho do parquet de saída")
    args = parser.parse_args()

    preprocessar(
        raw_dir=Path(args.raw) if args.raw else None,
        destino=Path(args.out) if args.out else None,
    )


if __name__ == "__main__":
    main()
