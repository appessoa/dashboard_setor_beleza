"""
Camada de visualização (Plotly).

Todos os gráficos do notebook foram reconstruídos em Plotly para permitir
hover, zoom e leitura interativa dos valores, preservando a mesma metodologia
(mesmas variáveis, mesmas referências de grupo). A paleta das marcas e a regra
de destaque da empresa foco (NTCO3) vêm de ``config`` / ``analysis``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from . import config
from .analysis import EMPRESA_FOCO, ordenar_empresas
from .formatting import formatar_moeda, formatar_percentual, formatar_numero

COR_TEXTO_SECUNDARIO = "#8A8A8A"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def cor_empresa(empresa: str, empresas_selecionadas: list[str], contexto: str = "comparativo") -> str:
    """
    Regra de cor do notebook:

    * NTCO3 (foco) → tom 'escuro' (destaque);
    * demais → tom 'claro' (secundário);
    * contexto='unico' → tom 'principal'.
    """
    marca = config.CORES_MARCAS.get(empresa, {"escuro": "#666", "principal": "#999", "claro": "#ccc"})
    if contexto == "unico":
        return marca["principal"]
    if empresa == EMPRESA_FOCO and EMPRESA_FOCO in empresas_selecionadas:
        return marca["escuro"]
    return marca["claro"]


def _aplicar_tema(fig: go.Figure, tema: dict, altura: int = 420) -> go.Figure:
    fig.update_layout(
        template=tema["plotly_template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=tema["texto"], size=13),
        margin=dict(l=10, r=10, t=48, b=10),
        height=altura,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        title=dict(font=dict(size=15, color=tema["texto"])),
        hoverlabel=dict(font_size=12),
    )
    fig.update_xaxes(gridcolor=tema["grid"], zeroline=False)
    fig.update_yaxes(gridcolor=tema["grid"], zeroline=False)
    return fig


# --------------------------------------------------------------------------- #
# 1. Boxplot de dispersão de preços
# --------------------------------------------------------------------------- #
def boxplot_precos(df: pd.DataFrame, empresas: list[str], tema: dict, titulo: str = "") -> go.Figure:
    empresas = ordenar_empresas(empresas)
    fig = go.Figure()
    for empresa in empresas:
        serie = df[df["CODNEG"] == empresa]["PREULT"].dropna()
        if serie.empty:
            continue
        fig.add_trace(
            go.Box(
                y=serie,
                name=empresa,
                marker_color=cor_empresa(empresa, empresas),
                boxmean=True,
                hovertemplate="%{y:.2f}<extra>" + empresa + "</extra>",
            )
        )
    fig.update_layout(title=titulo, showlegend=False, yaxis_title="Preço de fechamento (R$)")
    return _aplicar_tema(fig, tema)


# --------------------------------------------------------------------------- #
# 2. Histograma / densidade dos retornos diários
# --------------------------------------------------------------------------- #
def histograma_retornos(retornos: pd.DataFrame, empresas: list[str], tema: dict, titulo: str = "") -> go.Figure:
    empresas = ordenar_empresas([e for e in empresas if e in retornos.columns])
    fig = go.Figure()
    for empresa in empresas:
        serie = retornos[empresa].dropna()
        if serie.empty:
            continue
        eh_foco = empresa == EMPRESA_FOCO
        fig.add_trace(
            go.Histogram(
                x=serie,
                name=empresa,
                histnorm="probability density",
                opacity=0.75 if eh_foco else 0.45,
                marker_color=cor_empresa(empresa, empresas),
                nbinsx=60,
            )
        )
    fig.update_layout(
        title=titulo,
        barmode="overlay",
        xaxis_title="Variação diária (%)",
        yaxis_title="Densidade",
    )
    return _aplicar_tema(fig, tema)


# --------------------------------------------------------------------------- #
# 3. Heatmap de correlação dos retornos
# --------------------------------------------------------------------------- #
def heatmap_correlacao(corr: pd.DataFrame, tema: dict, titulo: str = "") -> go.Figure:
    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=list(corr.columns),
            y=list(corr.index),
            zmin=-1,
            zmax=1,
            colorscale="RdBu",
            reversescale=True,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
            colorbar=dict(title="Correlação"),
            hovertemplate="%{y} × %{x}: %{z:.2f}<extra></extra>",
        )
    )
    fig.update_layout(title=titulo)
    if EMPRESA_FOCO in corr.columns:
        pos = list(corr.columns).index(EMPRESA_FOCO)
        for shape in (
            dict(type="rect", x0=pos - 0.5, x1=pos + 0.5, y0=-0.5, y1=len(corr) - 0.5),
            dict(type="rect", x0=-0.5, x1=len(corr) - 0.5, y0=pos - 0.5, y1=pos + 0.5),
        ):
            fig.add_shape(
                **shape,
                line=dict(color=config.CORES_MARCAS[EMPRESA_FOCO]["escuro"], width=3),
                fillcolor="rgba(0,0,0,0)",
            )
    return _aplicar_tema(fig, tema, altura=460)


# --------------------------------------------------------------------------- #
# 4a. Volume mensal negociado (barras empilhadas)
# --------------------------------------------------------------------------- #
def volume_mensal_barras(vol_mensal: pd.DataFrame, empresas: list[str], tema: dict, titulo: str = "") -> go.Figure:
    fig = go.Figure()
    for empresa in vol_mensal.columns:
        fig.add_trace(
            go.Bar(
                x=list(vol_mensal.index),
                y=vol_mensal[empresa],
                name=empresa,
                marker_color=cor_empresa(empresa, empresas),
                hovertemplate="%{x}<br>" + empresa + ": R$ %{y:,.0f}<extra></extra>",
            )
        )
    fig.update_layout(title=titulo, barmode="stack", yaxis_title="Volume financeiro (R$)")
    return _aplicar_tema(fig, tema)


# --------------------------------------------------------------------------- #
# 4b. Share de liquidez no período (rosca)
# --------------------------------------------------------------------------- #
def pizza_share(volume: pd.Series, empresas: list[str], tema: dict, titulo: str = "") -> go.Figure:
    fig = go.Figure(
        data=go.Pie(
            labels=list(volume.index),
            values=list(volume.values),
            hole=0.45,
            marker=dict(colors=[cor_empresa(e, empresas) for e in volume.index]),
            textinfo="label+percent",
            textposition="inside",
            insidetextorientation="radial",
            hovertemplate="%{label}: R$ %{value:,.0f} (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(title=titulo, showlegend=True, uniformtext_minsize=9, uniformtext_mode="hide")
    return _aplicar_tema(fig, tema)


# --------------------------------------------------------------------------- #
# 5. Evolução temporal indexada (base 100) vs. mediana do grupo
# --------------------------------------------------------------------------- #
def evolucao_indexada_linhas(
    indexado: pd.DataFrame, mediana_grupo: pd.Series | None, empresas: list[str], tema: dict, titulo: str = ""
) -> go.Figure:
    empresas = ordenar_empresas([e for e in empresas if e in indexado.columns])
    fig = go.Figure()
    for empresa in empresas:
        if empresa == EMPRESA_FOCO:
            continue
        fig.add_trace(
            go.Scatter(
                x=indexado.index,
                y=indexado[empresa],
                name=empresa,
                mode="lines",
                line=dict(color=cor_empresa(empresa, empresas), width=1.3),
                opacity=0.65,
                hovertemplate="%{x|%d/%m/%Y}<br>" + empresa + ": %{y:.1f}<extra></extra>",
            )
        )
    if mediana_grupo is not None:
        fig.add_trace(
            go.Scatter(
                x=mediana_grupo.index,
                y=mediana_grupo.values,
                name="Mediana do grupo comparável",
                mode="lines",
                line=dict(color=COR_TEXTO_SECUNDARIO, width=2, dash="dash"),
            )
        )
    if EMPRESA_FOCO in indexado.columns and EMPRESA_FOCO in empresas:
        fig.add_trace(
            go.Scatter(
                x=indexado.index,
                y=indexado[EMPRESA_FOCO],
                name=EMPRESA_FOCO,
                mode="lines",
                line=dict(color=config.CORES_MARCAS[EMPRESA_FOCO]["escuro"], width=3.2),
                hovertemplate="%{x|%d/%m/%Y}<br>" + EMPRESA_FOCO + ": %{y:.1f}<extra></extra>",
            )
        )
    fig.add_hline(y=100, line_dash="dot", line_color=COR_TEXTO_SECUNDARIO, opacity=0.5)
    fig.update_layout(title=titulo, yaxis_title="Índice (base 100 no início do período)")
    return _aplicar_tema(fig, tema, altura=440)


# --------------------------------------------------------------------------- #
# 6. Dispersão risco × retorno
# --------------------------------------------------------------------------- #
def scatter_risco_retorno(
    tabela: pd.DataFrame, ref_retorno: float | None, ref_vol: float | None, empresas: list[str], tema: dict, titulo: str = ""
) -> go.Figure:
    empresas = ordenar_empresas([e for e in empresas if e in tabela.index])
    fig = go.Figure()
    for empresa in empresas:
        eh_foco = empresa == EMPRESA_FOCO
        linha = tabela.loc[empresa]
        fig.add_trace(
            go.Scatter(
                x=[linha["volatilidade_diaria"]],
                y=[linha["retorno_medio_diario"]],
                mode="markers+text",
                text=[empresa],
                textposition="top center",
                textfont=dict(color=cor_empresa(empresa, empresas), size=12),
                marker=dict(
                    size=26 if eh_foco else 16,
                    color=cor_empresa(empresa, empresas),
                    line=dict(color=tema["bg"], width=2),
                ),
                name=empresa,
                hovertemplate=(
                    empresa
                    + "<br>Volatilidade: %{x:.2f}%<br>Retorno médio: %{y:.3f}%<extra></extra>"
                ),
            )
        )
    if ref_retorno is not None:
        fig.add_hline(y=ref_retorno, line_dash="dot", line_color=COR_TEXTO_SECUNDARIO, opacity=0.6)
    if ref_vol is not None:
        fig.add_vline(x=ref_vol, line_dash="dot", line_color=COR_TEXTO_SECUNDARIO, opacity=0.6)
    fig.update_layout(
        title=titulo,
        showlegend=False,
        xaxis_title="Volatilidade diária — desvio padrão dos retornos (%)",
        yaxis_title="Retorno médio diário (%)",
    )
    return _aplicar_tema(fig, tema, altura=460)


# --------------------------------------------------------------------------- #
# 7. Drawdown
# --------------------------------------------------------------------------- #
def drawdown_linhas(dd: pd.DataFrame, empresas: list[str], tema: dict, titulo: str = "") -> go.Figure:
    empresas = ordenar_empresas([e for e in empresas if e in dd.columns])
    fig = go.Figure()
    for empresa in empresas:
        if empresa == EMPRESA_FOCO:
            continue
        fig.add_trace(
            go.Scatter(
                x=dd.index,
                y=dd[empresa],
                name=empresa,
                mode="lines",
                line=dict(color=cor_empresa(empresa, empresas), width=1.1),
                opacity=0.6,
            )
        )
    if EMPRESA_FOCO in dd.columns and EMPRESA_FOCO in empresas:
        fig.add_trace(
            go.Scatter(
                x=dd.index,
                y=dd[EMPRESA_FOCO],
                name=EMPRESA_FOCO,
                mode="lines",
                line=dict(color=config.CORES_MARCAS[EMPRESA_FOCO]["escuro"], width=2.6),
                fill="tozeroy",
                fillcolor="rgba(184,117,15,0.15)",
            )
        )
    fig.update_layout(title=titulo, yaxis_title="Drawdown em relação ao pico anterior (%)")
    return _aplicar_tema(fig, tema, altura=440)


# --------------------------------------------------------------------------- #
# 8. Sazonalidade — preço médio mensal × quantidade negociada
# --------------------------------------------------------------------------- #
def sazonalidade_preco_volume(mensal: pd.DataFrame, tema: dict, titulo: str = "") -> go.Figure:
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.09)
    marca = config.CORES_MARCAS[EMPRESA_FOCO]
    fig.add_trace(
        go.Scatter(
            x=mensal["Rotulo"], y=mensal["Preco_Medio"], mode="lines+markers",
            name="Preço médio mensal", line=dict(color=marca["escuro"], width=2.6),
            hovertemplate="%{x}<br>R$ %{y:.2f}<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=mensal["Rotulo"], y=mensal["Quantidade_Negociada"], mode="lines+markers",
            name="Quantidade negociada", line=dict(color=marca["principal"], width=2.2),
            hovertemplate="%{x}<br>%{y:,.0f} ações<extra></extra>",
        ),
        row=2, col=1,
    )
    # Faixas discretas de fundo para datas comemorativas (hipóteses de investigação).
    for i, num_mes in enumerate(mensal["NumMes"]):
        if num_mes in config.MESES_SAZONAIS:
            fig.add_vrect(
                x0=i - 0.4, x1=i + 0.4, fillcolor=tema["laranja"], opacity=0.08,
                line_width=0, layer="below",
            )
    fig.update_yaxes(title_text="Preço médio (R$)", row=1, col=1)
    fig.update_yaxes(title_text="Quantidade (ações)", row=2, col=1)
    fig.update_xaxes(tickangle=-45, row=2, col=1)
    fig.update_layout(title=titulo)
    return _aplicar_tema(fig, tema, altura=560)


# --------------------------------------------------------------------------- #
# 9. Sazonalidade — mesmo mês, ano a ano
# --------------------------------------------------------------------------- #
def sazonalidade_ano_a_ano(mensal: pd.DataFrame, tema: dict, titulo: str = "") -> go.Figure:
    pivot = mensal.pivot_table(index="NomeMes", columns="Ano", values="Preco_Medio", observed=True)
    pivot = pivot.reindex(config.MESES_PT).dropna(how="all")
    anos = list(pivot.columns)
    marca = config.CORES_MARCAS[EMPRESA_FOCO]
    tons = [marca["claro"], marca["escuro"], marca["principal"]]
    fig = go.Figure()
    for i, ano in enumerate(anos):
        fig.add_trace(
            go.Bar(
                x=list(pivot.index), y=pivot[ano], name=str(ano),
                marker_color=tons[i % len(tons)],
                hovertemplate="%{x}/" + str(ano) + "<br>R$ %{y:.2f}<extra></extra>",
            )
        )
    fig.update_layout(title=titulo, barmode="group", yaxis_title="Preço médio mensal (R$)")
    return _aplicar_tema(fig, tema)


# --------------------------------------------------------------------------- #
# 10. Sazonalidade consolidada — comportamento médio por mês do ano
# --------------------------------------------------------------------------- #
def sazonalidade_consolidada(consolidado: pd.DataFrame, tema: dict, titulo: str = "") -> go.Figure:
    marca = config.CORES_MARCAS[EMPRESA_FOCO]
    media_geral = consolidado["Preco_Medio_Historico"].mean()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(consolidado.index.astype(str)),
            y=consolidado["Preco_Medio_Historico"],
            mode="lines+markers",
            name="Preço médio histórico",
            line=dict(color=marca["escuro"], width=2.6),
            hovertemplate="%{x}<br>R$ %{y:.2f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=media_geral, line_dash="dash", line_color=COR_TEXTO_SECUNDARIO,
        annotation_text="Média geral do período", annotation_position="top left",
    )
    fig.update_layout(title=titulo, yaxis_title="Preço médio histórico (R$)")
    return _aplicar_tema(fig, tema)
