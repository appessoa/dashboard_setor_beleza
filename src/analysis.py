"""
Camada de análise.

Cada função reproduz um cálculo do notebook original, recebendo um DataFrame já
filtrado (período + empresas) e devolvendo estruturas de dados prontas para os
gráficos e textos. Nenhuma decisão estatística foi alterada:

* preço de referência = ``PREULT`` (fechamento);
* retornos diários = variação percentual do preço de fechamento;
* referência do grupo comparável = **mediana** das empresas, excluindo a foco;
* teste A/B = teste t de Welch (``equal_var=False``);
* drawdown = queda percentual frente ao pico móvel (``cummax``).

As "leituras" (títulos orientados a insight) são calculadas a partir dos dados
— nunca fixadas de antemão —, exatamente como no notebook.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .formatting import formatar_percentual

EMPRESA_FOCO = config.EMPRESA_FOCO


# --------------------------------------------------------------------------- #
# Estruturas base
# --------------------------------------------------------------------------- #
def ordenar_empresas(empresas: list[str]) -> list[str]:
    """Mantém a ordem canônica da análise."""
    return [e for e in config.EMPRESAS_BELEZA if e in empresas] + [
        e for e in empresas if e not in config.EMPRESAS_BELEZA
    ]


def precos_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Pivô de preço de fechamento: índice = data, colunas = ticker."""
    return df.pivot_table(index="DATPRG", columns="CODNEG", values="PREULT").sort_index()


def retornos_diarios(pivot: pd.DataFrame) -> pd.DataFrame:
    """Retornos diários em % (``pct_change`` do preço de fechamento)."""
    return pivot.pct_change() * 100


def tem_foco(empresas: list[str]) -> bool:
    return EMPRESA_FOCO in empresas


# --------------------------------------------------------------------------- #
# KPIs (notebook: tabela de KPIs)
# --------------------------------------------------------------------------- #
def calcular_kpis(df: pd.DataFrame, empresas: list[str]) -> pd.DataFrame:
    """
    Tabela de KPIs por empresa: preço inicial, preço final, mínimo, máximo e
    crescimento acumulado (%) — usando o preço de fechamento (``PREULT``).
    """
    linhas = []
    for empresa in ordenar_empresas(empresas):
        serie = df[df["CODNEG"] == empresa].sort_values("DATPRG")["PREULT"].dropna()
        if serie.empty:
            continue
        preco_inicial = serie.iloc[0]
        preco_final = serie.iloc[-1]
        crescimento = ((preco_final - preco_inicial) / preco_inicial) * 100
        linhas.append(
            {
                "Ativo": empresa,
                "Preço Inicial": preco_inicial,
                "Preço Final": preco_final,
                "Mínimo no Período": serie.min(),
                "Máximo no Período": serie.max(),
                "Crescimento Acumulado (%)": round(crescimento, 2),
            }
        )
    if not linhas:
        return pd.DataFrame(
            columns=[
                "Preço Inicial", "Preço Final", "Mínimo no Período",
                "Máximo no Período", "Crescimento Acumulado (%)",
            ]
        )
    return pd.DataFrame(linhas).set_index("Ativo")


def kpis_editoriais(df: pd.DataFrame, empresas: list[str]) -> dict:
    """
    Indicadores de abertura em formato editorial (poucos números, calculados
    dinamicamente a partir da seleção atual).
    """
    df_kpis = calcular_kpis(df, empresas)
    mediana_fechamento = float(df["PREULT"].median()) if not df.empty else float("nan")

    if not df_kpis.empty:
        evolucao_mediana = float(df_kpis["Crescimento Acumulado (%)"].median())
    else:
        evolucao_mediana = float("nan")

    if not df.empty:
        ini, fim = df["DATPRG"].min(), df["DATPRG"].max()
        anos = sorted({ini.year, fim.year})
        periodo = f"{anos[0]}" if len(anos) == 1 else f"{anos[0]}–{anos[-1]}"
        periodo_completo = f"{ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
    else:
        periodo, periodo_completo = "—", "—"

    return {
        "mediana_fechamento": mediana_fechamento,
        "evolucao_mediana_grupo": evolucao_mediana,
        "empresas_analisadas": int(df["CODNEG"].nunique()) if not df.empty else 0,
        "periodo": periodo,
        "periodo_completo": periodo_completo,
        "pregoes": int(df["DATPRG"].nunique()) if not df.empty else 0,
    }


# --------------------------------------------------------------------------- #
# Dispersão de preços (boxplot) + leitura de maior IQR
# --------------------------------------------------------------------------- #
def dispersao_precos(df: pd.DataFrame, empresas: list[str]) -> dict:
    empresas = ordenar_empresas(empresas)
    iqr = df.groupby("CODNEG")["PREULT"].apply(
        lambda s: s.quantile(0.75) - s.quantile(0.25)
    )
    iqr = iqr.reindex([e for e in empresas if e in iqr.index])
    if iqr.empty:
        return {"iqr": iqr, "empresa_maior_iqr": None, "leitura": "Sem dados no período selecionado."}
    empresa_maior = iqr.idxmax()
    if not tem_foco(empresas):
        leitura = f"{empresa_maior} apresenta a maior dispersão de preços do grupo selecionado."
    elif empresa_maior == EMPRESA_FOCO:
        leitura = f"{EMPRESA_FOCO} apresenta a maior dispersão de preços do grupo."
    else:
        leitura = f"{empresa_maior} apresenta maior dispersão de preços que {EMPRESA_FOCO}."
    return {"iqr": iqr, "empresa_maior_iqr": empresa_maior, "leitura": leitura}


# --------------------------------------------------------------------------- #
# Volatilidade dos retornos (histograma) + leitura
# --------------------------------------------------------------------------- #
def volatilidade_retornos(retornos: pd.DataFrame, empresas: list[str]) -> dict:
    empresas = ordenar_empresas([e for e in empresas if e in retornos.columns])
    vol = retornos[empresas].std()
    leitura = "Selecione ao menos duas empresas para comparar a volatilidade."
    if tem_foco(empresas) and len(empresas) > 1:
        vol_foco = vol[EMPRESA_FOCO]
        vol_media = vol.drop(EMPRESA_FOCO).mean()
        if vol_foco > vol_media:
            leitura = (
                f"{EMPRESA_FOCO} apresenta volatilidade diária acima da média do grupo "
                f"comparável ({formatar_percentual(vol_foco)} vs. {formatar_percentual(vol_media)})."
            )
        else:
            leitura = (
                f"{EMPRESA_FOCO} apresenta volatilidade diária abaixo da média do grupo "
                f"comparável ({formatar_percentual(vol_foco)} vs. {formatar_percentual(vol_media)})."
            )
    return {"volatilidade": vol, "leitura": leitura}


# --------------------------------------------------------------------------- #
# Correlação de retornos + leitura
# --------------------------------------------------------------------------- #
def matriz_correlacao(retornos: pd.DataFrame, empresas: list[str]) -> dict:
    empresas = ordenar_empresas([e for e in empresas if e in retornos.columns])
    corr = retornos[empresas].corr()
    leitura = "Selecione ao menos duas empresas para calcular correlações."
    empresa_mais_correlacionada = None
    if tem_foco(empresas) and len(empresas) > 1:
        corr_foco = corr[EMPRESA_FOCO].drop(EMPRESA_FOCO)
        empresa_mais_correlacionada = corr_foco.idxmax()
        empresa_menos = corr_foco.idxmin()
        leitura = (
            f"{empresa_mais_correlacionada} tem os retornos diários mais parecidos "
            f"com os da {EMPRESA_FOCO} (correlação {corr_foco.max():.2f}); "
            f"{empresa_menos} é a mais descorrelacionada ({corr_foco.min():.2f})."
        )
    elif len(empresas) > 1:
        tri = corr.where(~np.eye(len(corr), dtype=bool))
        media = tri.stack().mean()
        leitura = f"Correlação média entre os retornos das empresas selecionadas: {media:.2f}."
    return {
        "correlacao": corr,
        "empresa_mais_correlacionada": empresa_mais_correlacionada,
        "leitura": leitura,
    }


# --------------------------------------------------------------------------- #
# Volume mensal + share de liquidez
# --------------------------------------------------------------------------- #
def volume_mensal(df: pd.DataFrame, empresas: list[str]) -> pd.DataFrame:
    empresas = ordenar_empresas(empresas)
    tmp = df.copy()
    tmp["AnoMes"] = tmp["DATPRG"].dt.to_period("M").astype(str)
    vol = (
        tmp.groupby(["AnoMes", "CODNEG"])["VOLTOT"].sum().unstack().fillna(0.0)
    )
    return vol.reindex(columns=[e for e in empresas if e in vol.columns])


def share_liquidez(df: pd.DataFrame, empresas: list[str]) -> dict:
    empresas = ordenar_empresas(empresas)
    vol = df.groupby("CODNEG")["VOLTOT"].sum()
    vol = vol.reindex([e for e in empresas if e in vol.index]).dropna()
    leitura = "Sem dados de volume no período selecionado."
    if not vol.empty and tem_foco(empresas):
        share = vol[EMPRESA_FOCO] / vol.sum() * 100
        leitura = (
            f"{EMPRESA_FOCO} responde por {formatar_percentual(share)} do volume "
            f"financeiro negociado no grupo selecionado."
        )
    elif not vol.empty:
        lider = vol.idxmax()
        leitura = (
            f"{lider} concentra a maior fatia de liquidez "
            f"({formatar_percentual(vol[lider] / vol.sum() * 100)}) do grupo selecionado."
        )
    return {"volume": vol, "leitura": leitura}


def tendencia_volume_foco(vol_mensal: pd.DataFrame) -> str:
    if EMPRESA_FOCO not in vol_mensal.columns or len(vol_mensal) < 2:
        return ""
    serie = vol_mensal[EMPRESA_FOCO]
    tendencia = "crescente" if serie.iloc[-1] > serie.iloc[0] else "decrescente"
    return f"Volume mensal negociado da {EMPRESA_FOCO} com tendência {tendencia} no período."


# --------------------------------------------------------------------------- #
# Teste A/B (teste t de Welch) — notebook Etapa 4
# --------------------------------------------------------------------------- #
def teste_ab(
    retornos: pd.DataFrame,
    grupo_a: str = config.TESTE_AB_GRUPO_A,
    grupo_b: str = config.TESTE_AB_GRUPO_B,
) -> dict | None:
    if grupo_a not in retornos.columns or grupo_b not in retornos.columns:
        return None
    try:
        from scipy import stats
    except Exception:  # pragma: no cover
        return None

    dados_a = retornos[grupo_a].dropna()
    dados_b = retornos[grupo_b].dropna()
    if len(dados_a) < 3 or len(dados_b) < 3:
        return None

    t_stat, p_value = stats.ttest_ind(dados_a, dados_b, equal_var=False)
    significativo = p_value < config.TESTE_AB_ALPHA
    if significativo:
        conclusao = (
            "Rejeitamos a hipótese nula: há diferença estatisticamente significativa "
            f"entre os retornos diários médios de {grupo_a} e {grupo_b}."
        )
    else:
        conclusao = (
            "Não há evidência estatística suficiente para afirmar que os retornos "
            f"diários médios de {grupo_a} e {grupo_b} são diferentes."
        )
    return {
        "grupo_a": grupo_a,
        "grupo_b": grupo_b,
        "media_a": float(dados_a.mean()),
        "media_b": float(dados_b.mean()),
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "alpha": config.TESTE_AB_ALPHA,
        "significativo": bool(significativo),
        "conclusao": conclusao,
        "conclusao_curta": (
            "com diferença estatística significativa"
            if significativo
            else "sem diferença estatística significativa"
        ),
    }


# --------------------------------------------------------------------------- #
# Evolução indexada (base 100) vs. mediana do grupo — notebook Etapa 5.1
# --------------------------------------------------------------------------- #
def evolucao_indexada(pivot: pd.DataFrame, empresas: list[str]) -> dict:
    empresas = ordenar_empresas([e for e in empresas if e in pivot.columns])
    sub = pivot[empresas].dropna(how="all")
    primeiro_valido = sub.apply(lambda c: c.dropna().iloc[0] if c.notna().any() else np.nan)
    indexado = sub.divide(primeiro_valido, axis=1) * 100

    mediana_grupo = None
    leitura = "Selecione a NTCO3 e ao menos um comparável para a leitura completa."
    if tem_foco(empresas) and len(empresas) > 1:
        mediana_grupo = indexado.drop(columns=EMPRESA_FOCO).median(axis=1)
        var_foco = indexado[EMPRESA_FOCO].iloc[-1] - 100
        var_grupo = mediana_grupo.iloc[-1] - 100
        if indexado[EMPRESA_FOCO].iloc[-1] > mediana_grupo.iloc[-1]:
            leitura = (
                f"{EMPRESA_FOCO} ({formatar_percentual(var_foco)}) supera a mediana do "
                f"grupo comparável ({formatar_percentual(var_grupo)}) no acumulado do período."
            )
        else:
            leitura = (
                f"{EMPRESA_FOCO} ({formatar_percentual(var_foco)}) fica abaixo da mediana do "
                f"grupo comparável ({formatar_percentual(var_grupo)}) no acumulado do período."
            )
    return {"indexado": indexado, "mediana_grupo": mediana_grupo, "leitura": leitura}


# --------------------------------------------------------------------------- #
# Risco x retorno — notebook Etapa 5.2
# --------------------------------------------------------------------------- #
def risco_retorno(retornos: pd.DataFrame, empresas: list[str]) -> dict:
    empresas = ordenar_empresas([e for e in empresas if e in retornos.columns])
    retorno_medio = retornos[empresas].mean()
    volatilidade = retornos[empresas].std()
    tabela = pd.DataFrame(
        {"retorno_medio_diario": retorno_medio, "volatilidade_diaria": volatilidade}
    )

    ref_retorno = ref_vol = None
    leitura = "Selecione a NTCO3 e comparáveis para a leitura de risco × retorno."
    if tem_foco(empresas) and len(empresas) > 1:
        ref_retorno = retorno_medio.drop(EMPRESA_FOCO).median()
        ref_vol = volatilidade.drop(EMPRESA_FOCO).median()
        ret_foco, vol_foco = retorno_medio[EMPRESA_FOCO], volatilidade[EMPRESA_FOCO]
        if ret_foco >= ref_retorno and vol_foco <= ref_vol:
            leitura = f"{EMPRESA_FOCO} combina retorno e risco iguais ou melhores que a mediana do grupo."
        elif ret_foco >= ref_retorno and vol_foco > ref_vol:
            leitura = f"{EMPRESA_FOCO} tem retorno acima da mediana, mas volatilidade também acima da mediana do grupo."
        elif ret_foco < ref_retorno and vol_foco <= ref_vol:
            leitura = f"{EMPRESA_FOCO} tem risco controlado, porém retorno abaixo da mediana do grupo."
        else:
            leitura = f"{EMPRESA_FOCO} combina retorno abaixo da mediana com volatilidade acima da mediana do grupo."
    return {
        "tabela": tabela,
        "ref_retorno": ref_retorno,
        "ref_volatilidade": ref_vol,
        "leitura": leitura,
    }


# --------------------------------------------------------------------------- #
# Drawdown — notebook Etapa 5.3
# --------------------------------------------------------------------------- #
def drawdown(pivot: pd.DataFrame, empresas: list[str]) -> dict:
    empresas = ordenar_empresas([e for e in empresas if e in pivot.columns])
    sub = pivot[empresas]
    pico_movel = sub.cummax()
    dd = (sub / pico_movel - 1) * 100
    maior_por_empresa = dd.min()

    leitura = "Sem dados suficientes para o cálculo de drawdown."
    if not maior_por_empresa.empty:
        empresa_maior_dd = maior_por_empresa.idxmin()
        if tem_foco(empresas):
            dd_foco = maior_por_empresa[EMPRESA_FOCO]
            if empresa_maior_dd == EMPRESA_FOCO:
                leitura = (
                    f"{EMPRESA_FOCO} teve a maior queda frente ao próprio pico entre as "
                    f"empresas selecionadas ({formatar_percentual(dd_foco)})."
                )
            else:
                leitura = (
                    f"{EMPRESA_FOCO} teve queda máxima de {formatar_percentual(dd_foco)}, "
                    f"menor que a de {empresa_maior_dd} "
                    f"({formatar_percentual(maior_por_empresa[empresa_maior_dd])})."
                )
        else:
            leitura = (
                f"{empresa_maior_dd} registrou a maior queda frente ao próprio pico "
                f"({formatar_percentual(maior_por_empresa[empresa_maior_dd])})."
            )
    return {"drawdown": dd, "maior_por_empresa": maior_por_empresa, "leitura": leitura}


# --------------------------------------------------------------------------- #
# Ranking multidimensional — notebook Etapa 5.4
# --------------------------------------------------------------------------- #
def ranking_multidimensional(
    df: pd.DataFrame, retornos: pd.DataFrame, pivot: pd.DataFrame, empresas: list[str]
) -> pd.DataFrame:
    empresas = ordenar_empresas(empresas)
    df_kpis = calcular_kpis(df, empresas)
    if df_kpis.empty:
        return pd.DataFrame()

    presentes = [e for e in empresas if e in retornos.columns]
    volatilidade = retornos[presentes].std()
    dd = drawdown(pivot, presentes)["maior_por_empresa"]
    corr_foco = (
        matriz_correlacao(retornos, empresas)["correlacao"][EMPRESA_FOCO]
        if tem_foco(empresas)
        else pd.Series(dtype=float)
    )

    tabela = pd.DataFrame(
        {
            "Retorno Acumulado (%)": df_kpis["Crescimento Acumulado (%)"],
            "Volatilidade Diária (%)": volatilidade,
            "Máximo Drawdown (%)": dd,
        }
    )
    if not corr_foco.empty:
        tabela[f"Correlação com {EMPRESA_FOCO}"] = corr_foco

    tabela = tabela.reindex([e for e in empresas if e in tabela.index])
    return tabela.sort_values("Retorno Acumulado (%)", ascending=False)


# --------------------------------------------------------------------------- #
# Módulo de sazonalidade — NTCO3 (notebook, últimas células)
# --------------------------------------------------------------------------- #
def preparar_sazonalidade(df: pd.DataFrame, empresa: str = EMPRESA_FOCO) -> pd.DataFrame:
    base = df[df["CODNEG"] == empresa].copy()
    if base.empty:
        return base
    base["Ano"] = base["DATPRG"].dt.year
    base["NumMes"] = base["DATPRG"].dt.month
    base["NomeMes"] = base["NumMes"].apply(lambda m: config.MESES_PT[m - 1])
    base["NomeMes"] = pd.Categorical(base["NomeMes"], categories=config.MESES_PT, ordered=True)
    base = base.dropna(subset=["PREULT", "QUATOT"])
    base["AnoMes"] = base["DATPRG"].dt.to_period("M")
    return base


def serie_mensal_sazonalidade(base: pd.DataFrame) -> pd.DataFrame:
    if base.empty:
        return base
    mensal = (
        base.groupby("AnoMes")
        .agg(
            Preco_Medio=("PREULT", "mean"),
            Quantidade_Negociada=("QUATOT", "sum"),
            Ano=("Ano", "first"),
            NumMes=("NumMes", "first"),
            NomeMes=("NomeMes", "first"),
        )
        .sort_index()
    )
    mensal["Rotulo"] = mensal["NomeMes"].astype(str) + "/" + mensal["Ano"].astype(str)
    mensal["Var_Preco_%"] = mensal["Preco_Medio"].pct_change() * 100
    mensal["Var_Quantidade_%"] = mensal["Quantidade_Negociada"].pct_change() * 100
    return mensal


def consolidado_mensal_sazonalidade(mensal: pd.DataFrame) -> pd.DataFrame:
    if mensal.empty:
        return mensal
    consolidado = (
        mensal.groupby("NomeMes", observed=True)
        .agg(
            Preco_Medio_Historico=("Preco_Medio", "mean"),
            Quantidade_Media_Historica=("Quantidade_Negociada", "mean"),
            Numero_de_Anos=("Ano", "nunique"),
        )
        .reindex(config.MESES_PT)
        .dropna(how="all")
    )
    return consolidado


def insights_sazonalidade(mensal: pd.DataFrame, consolidado: pd.DataFrame) -> dict:
    if mensal.empty or consolidado.empty:
        return {"insights": [], "conclusao": "Sem dados da NTCO3 no período selecionado.", "correlacao_preco_qtd": float("nan")}

    mes_maior_preco_serie = mensal.loc[mensal["Preco_Medio"].idxmax(), "Rotulo"]
    mes_menor_preco_serie = mensal.loc[mensal["Preco_Medio"].idxmin(), "Rotulo"]
    mes_maior_qtd_serie = mensal.loc[mensal["Quantidade_Negociada"].idxmax(), "Rotulo"]
    mes_menor_qtd_serie = mensal.loc[mensal["Quantidade_Negociada"].idxmin(), "Rotulo"]

    mes_maior_preco = consolidado["Preco_Medio_Historico"].idxmax()
    mes_menor_preco = consolidado["Preco_Medio_Historico"].idxmin()
    mes_maior_qtd = consolidado["Quantidade_Media_Historica"].idxmax()
    mes_menor_qtd = consolidado["Quantidade_Media_Historica"].idxmin()

    correlacao = mensal[["Preco_Medio", "Quantidade_Negociada"]].corr().iloc[0, 1]
    if abs(correlacao) < 0.2:
        leitura_corr = "fraca ou praticamente inexistente"
    elif abs(correlacao) < 0.5:
        leitura_corr = "moderada"
    else:
        leitura_corr = "forte"

    anos_unicos = sorted(mensal["Ano"].unique())
    qtd_anos = len(anos_unicos)

    insights = [
        f"O maior preço médio mensal da {EMPRESA_FOCO} no período foi em {mes_maior_preco_serie}, e o menor em {mes_menor_preco_serie}.",
        f"A maior quantidade negociada mensal ocorreu em {mes_maior_qtd_serie}, e a menor em {mes_menor_qtd_serie}.",
        f"Historicamente (consolidando {qtd_anos} ano(s) disponível(is)), {mes_maior_preco} tem, em média, o maior preço, e {mes_menor_preco} o menor.",
        f"Historicamente, {mes_maior_qtd} concentra, em média, o maior volume negociado, e {mes_menor_qtd} o menor.",
        f"A correlação entre preço médio mensal e quantidade negociada mensal é {leitura_corr} ({correlacao:.2f}) — correlação não implica causalidade.",
    ]

    if qtd_anos < 2:
        conclusao = (
            f"O dataset selecionado cobre apenas {qtd_anos} ano completo/parcial. "
            "Não há dados suficientes para comparar o mesmo mês em anos diferentes — "
            "portanto NÃO é possível concluir que exista sazonalidade recorrente. "
            "O que se observa são padrões de um único período (observação), não um "
            "padrão comprovadamente repetido (conclusão)."
        )
    else:
        ocorrencias = mensal[mensal["NomeMes"] == mes_maior_preco]["Ano"].nunique()
        recorrente = ocorrencias >= 2 and ocorrencias == qtd_anos
        if recorrente:
            conclusao = (
                f"O mês de {mes_maior_preco} apresentou o maior preço médio em todos os "
                f"{qtd_anos} anos disponíveis — evidência (ainda que limitada pelo número "
                "de anos) de possível sazonalidade."
            )
        else:
            conclusao = (
                f"Com {qtd_anos} anos de dados ainda não há evidência consistente de "
                "recorrência: o mês de destaque não se repete de forma clara entre os "
                "anos disponíveis. Seriam necessários mais anos para afirmar sazonalidade "
                "com confiança."
            )

    return {
        "insights": insights,
        "conclusao": conclusao,
        "correlacao_preco_qtd": float(correlacao),
        "mes_maior_preco_hist": mes_maior_preco,
        "mes_menor_preco_hist": mes_menor_preco,
    }
