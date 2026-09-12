"""
Análise Exploratória: Tendências e Evolução do Setor de Beleza no Mercado Financeiro
Infográfico analítico interativo (Streamlit) — conversão do notebook
``notebook/notebook_original.ipynb``.

Executar:  streamlit run app.py
"""

from __future__ import annotations

import html  # NOVO: escape de texto na barra "Mercado agora" (HTML custom)

import pandas as pd
import streamlit as st

# NOVO (item 3): yfinance é usado no painel de cotações ao vivo.
# É opcional — se não estiver instalado, o painel cai para valores mockados.
# Instale com:  pip install yfinance
try:
    import yfinance as yf

    _YFINANCE_OK = True
except Exception:  # pragma: no cover
    _YFINANCE_OK = False

from src import analysis, charts, config
from src.components import (
    espaco,
    insight_list,
    kpi_row,
    paragrafo,
    reading,
    render_footer,
    render_header,
    render_illustration,
    section,
)
from src.styles import css

st.set_page_config(
    page_title="Setor de Beleza na B3 — Análise Exploratória",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# NOVO (item 3) — Painel de cotações ao vivo (ticker)
# --------------------------------------------------------------------------- #
# Índices/ações exibidos no topo. `ticker` é o símbolo no Yahoo Finance;
# `mock` é o valor de reserva usado quando o yfinance falha ou não tem o índice
# (caso do ISEE e do ICON, que não têm símbolo público estável no Yahoo).
# NATU3 e IBOV usam dados reais do yfinance; o `mock` deles só aparece se a
# API estiver fora do ar (assim o layout nunca fica vazio numa demo).
# Obs.: no Yahoo Finance o papel da Natura hoje é NATU3.SA (a antiga NTCO3.SA
# ficou sem dados após a troca de ticker de 01/07/2025).
INDICADORES_MERCADO = [
    {"rotulo": "NATU3 · Natura", "ticker": "NATU3.SA",
     "mock": {"valor": 12.34, "variacao_pct": 0.0}},
    {"rotulo": "IBOV · Ibovespa", "ticker": "^BVSP",
     "mock": {"valor": 132500.00, "variacao_pct": 0.0}},
    {"rotulo": "ISEE · Sustentabilidade", "ticker": "^ISEE",
     "mock": {"valor": 4383.04, "variacao_pct": 0.41}},
    {"rotulo": "ICON · Consumo", "ticker": "^ICON",
     "mock": {"valor": 2954.96, "variacao_pct": -0.23}},
]


@st.cache_data(ttl=300, show_spinner=False)  # cache de 5 min p/ não bater na API a cada rerun
def _buscar_cotacao(ticker: str) -> dict | None:
    """
    Busca o último fechamento e a variação % vs. o pregão anterior via yfinance.
    Retorna None se a lib não estiver instalada ou o ticker não retornar dados.
    """
    if not _YFINANCE_OK:
        return None
    try:
        hist = yf.Ticker(ticker).history(period="5d", interval="1d")
        if hist is None or hist.empty or len(hist) < 2:
            return None
        atual = float(hist["Close"].iloc[-1])
        anterior = float(hist["Close"].iloc[-2])
        variacao = (atual - anterior) / anterior * 100 if anterior else 0.0
        return {"valor": atual, "variacao_pct": variacao}
    except Exception:
        return None


def _formatar_reais(valor: float) -> str:
    """Formata no padrão brasileiro: 1.234,56."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_painel_cotacoes() -> None:
    """
    CORREÇÃO (item 2): faixa "Mercado agora" como uma barra horizontal única,
    no estilo do site de RI da Natura.

    Trocamos o st.metric (que gera cartões separados) por HTML/CSS injetado:
    fundo azul-escuro (#062b33), tickers lado a lado, texto branco e a
    variação % em verde (alta) / vermelho (baixa), com fonte um pouco menor.
    As classes CSS (.ticker-bar / .ticker-*) estão em src/styles.py.
    """
    blocos = []
    for indicador in INDICADORES_MERCADO:
        # dados reais do yfinance; se vier None, usa o mock (ou traço, se não houver)
        dados = _buscar_cotacao(indicador["ticker"]) or indicador["mock"]
        codigo = html.escape(indicador["rotulo"].split(" · ")[0])  # só "NTCO3", "IBOV"...

        if not dados:
            valor_txt, var_html = "—", ""
        else:
            valor_txt = _formatar_reais(dados["valor"])
            pct = dados["variacao_pct"]
            cor = "#2ecc71" if pct >= 0 else "#e74c3c"   # verde/vermelho de mercado
            seta = "▲" if pct >= 0 else "▼"     # ▲ / ▼
            var_html = f"<span class='ticker-var' style='color:{cor}'>{seta} {pct:+.2f}%</span>"

        blocos.append(
            "<div class='ticker-item'>"
            f"<span class='ticker-nome'>{codigo}</span>"
            f"<span class='ticker-valor'>{html.escape(valor_txt)}</span>"
            f"{var_html}"
            "</div>"
        )

    st.markdown("<div class='ticker-bar'>" + "".join(blocos) + "</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Dados
# --------------------------------------------------------------------------- #
from src.data import carregar_dataset, empresas_disponiveis, filtrar, intervalo_datas

try:
    df_full = carregar_dataset()
except FileNotFoundError as erro:
    st.error(str(erro))
    st.info(
        "No terminal, dentro da pasta do projeto, rode:\n\n"
        "```\npython scripts/preprocess_data.py\n```"
    )
    st.stop()


data_min, data_max = intervalo_datas(df_full)
empresas_todas = empresas_disponiveis(df_full)


# --------------------------------------------------------------------------- #
# Controles (tema + filtros globais)
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### Controles")
    tema_nome = st.radio(
        "Tema", options=["claro", "escuro"], horizontal=True,
        format_func=lambda x: "☀️ Claro" if x == "claro" else "🌙 Escuro",
    )
    st.divider()

    periodo = st.date_input(
        "Período de análise",
        value=(data_min.date(), data_max.date()),
        min_value=data_min.date(),
        max_value=data_max.date(),
        format="DD/MM/YYYY",
    )
    if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        data_ini, data_fim = periodo
    else:
        data_ini, data_fim = data_min.date(), data_max.date()

    opcoes_empresa = ["Todas"] + empresas_todas
    escolha = st.multiselect(
        "Empresas", options=opcoes_empresa, default=["Todas"],
        help="Escolha 'Todas' ou selecione tickers específicos.",
    )
    if not escolha or "Todas" in escolha:
        empresas_sel = empresas_todas
    else:
        empresas_sel = [e for e in empresas_todas if e in escolha]

    st.divider()
    st.caption(
        "Tickers da análise: NTCO3 (foco), COTY34, HYPE3, PNVL3, RADL3, ESPA3. "
        "NATU3 é tratada como NTCO3 (troca de ticker em 01/07/2025); a ESPA3 tem "
        "ajuste retroativo do grupamento 10:1 de 15/06/2026."
    )

tema = config.tema(tema_nome)
st.markdown(css(tema), unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Recorte + estruturas base
# --------------------------------------------------------------------------- #
df = filtrar(df_full, empresas_sel, pd.Timestamp(data_ini), pd.Timestamp(data_fim))

if df.empty:
    render_header("Sem dados para o recorte selecionado.")
    st.warning("Ajuste o período ou a seleção de empresas na barra lateral.")
    st.stop()

pivot = analysis.precos_pivot(df)
retornos = analysis.retornos_diarios(pivot)
kpis = analysis.kpis_editoriais(df, empresas_sel)


# --------------------------------------------------------------------------- #
# HEADER
# --------------------------------------------------------------------------- #
render_header(
    "Como a Natura (NTCO3) se comporta frente a um grupo comparável de empresas "
    "de beleza, farma e varejo de saúde listadas na B3 — leitura exploratória "
    "das séries históricas de 2025 a 2026."
)

subtitulo_recorte = (
    f"Recorte atual: {kpis['periodo_completo']} · "
    f"{kpis['empresas_analisadas']} empresa(s) · {kpis['pregoes']} pregões"
)
st.caption(subtitulo_recorte)

# NOVO (item 3): faixa de cotações ao vivo, logo abaixo do cabeçalho/logo.
espaco("sm")
st.markdown("<div class='ig-section-num'>MERCADO AGORA</div>", unsafe_allow_html=True)
render_painel_cotacoes()
if not _YFINANCE_OK:
    st.caption("⚠️ `yfinance` não instalado — cotações exibidas são exemplos. Rode `pip install yfinance`.")
else:
    st.caption("Fonte: Yahoo Finance (atualiza a cada 5 min). ISEE e ICON são ilustrativos.")
espaco("md")


# --------------------------------------------------------------------------- #
# INTRODUÇÃO
# --------------------------------------------------------------------------- #
espaco("sm")
col_txt, col_img = st.columns([2, 1], vertical_alignment="center")
with col_txt:
    section(
        "01",
        "Visão geral",
        "O estudo parte das séries históricas de negociação da B3 (arquivos "
        "COTAHIST) e isola seis ativos ligados a beleza e cuidados pessoais. "
        "Dois eventos societários reais precisaram ser tratados nos dados antes "
        "de qualquer comparação: a troca de ticker NTCO3→NATU3 e o grupamento "
        "10:1 da ESPA3 — sem esses ajustes, a comparação entre as empresas "
        "ficaria distorcida.",
    )
with col_img:
    render_illustration("imagem_01", "Setor de beleza e cuidados pessoais")

kpi_row(kpis)
paragrafo(
    "Os números acima são recalculados a cada mudança de período ou de seleção "
    "de empresas. A 'evolução mediana do grupo' é a mediana do crescimento "
    "acumulado (preço de fechamento) das empresas no recorte."
)

espaco("md")

# --- Dispersão de preços (boxplot) ---
disp = analysis.dispersao_precos(df, empresas_sel)
st.plotly_chart(
    charts.boxplot_precos(df, empresas_sel, tema, "Dispersão do preço de fechamento por empresa"),
    use_container_width=True,
)
reading(disp["leitura"])


# --------------------------------------------------------------------------- #
# DISTRIBUIÇÃO DOS RETORNOS
# --------------------------------------------------------------------------- #
espaco("lg")
section(
    "02",
    "Distribuição dos retornos diários",
    "A variação percentual diária do preço de fechamento revela o 'temperamento' "
    "de cada ação: quanto mais larga a distribuição, mais volátil o ativo.",
)
vol = analysis.volatilidade_retornos(retornos, empresas_sel)
st.plotly_chart(
    charts.histograma_retornos(retornos, empresas_sel, tema, "Densidade dos retornos diários (%)"),
    use_container_width=True,
)
reading(vol["leitura"], variante="alt")


# --------------------------------------------------------------------------- #
# EVOLUÇÃO TEMPORAL
# --------------------------------------------------------------------------- #
espaco("lg")
section(
    "03",
    "Evolução ao longo do tempo",
    "Para comparar empresas com preços absolutos muito diferentes, cada série é "
    "indexada em base 100 no início do período. A referência do grupo é a "
    "mediana das comparáveis (menos sensível a extremos do que a média, com "
    "apenas cinco comparáveis).",
)
evo = analysis.evolucao_indexada(pivot, empresas_sel)
st.plotly_chart(
    charts.evolucao_indexada_linhas(
        evo["indexado"], evo["mediana_grupo"], empresas_sel, tema,
        "Evolução indexada (base 100) — NTCO3 vs. mediana do grupo",
    ),
    use_container_width=True,
)
reading(evo["leitura"])

espaco("md")
col_img2, col_chart = st.columns([1, 2], vertical_alignment="center")
with col_img2:
    render_illustration("imagem_02", "Liquidez e volume negociado")
with col_chart:
    vol_mensal = analysis.volume_mensal(df, empresas_sel)
    st.plotly_chart(
        charts.volume_mensal_barras(vol_mensal, empresas_sel, tema, "Volume financeiro negociado por mês"),
        use_container_width=True,
    )
tend = analysis.tendencia_volume_foco(vol_mensal)
if tend:
    reading(tend, variante="alt")


# --------------------------------------------------------------------------- #
# COMPARAÇÃO ENTRE EMPRESAS
# --------------------------------------------------------------------------- #
espaco("lg")
section(
    "04",
    "Comparação entre empresas",
    "Cada indicador é reportado individualmente — não há score combinado. A "
    "tabela é ordenada pelo retorno acumulado; volatilidade, drawdown máximo e "
    "correlação com a NTCO3 complementam a leitura.",
)
ranking = analysis.ranking_multidimensional(df, retornos, pivot, empresas_sel)
if not ranking.empty:
    def _destacar_foco(linha):
        if linha.name == config.EMPRESA_FOCO:
            return [f"background-color: {tema['bege']}; font-weight: 700"] * len(linha)
        return [""] * len(linha)

    estilo = (
        ranking.style.format("{:.2f}")
        .apply(_destacar_foco, axis=1)
        .bar(subset=["Retorno Acumulado (%)"], color=[tema["terracota"], tema["verde"]], align=0)
    )
    st.dataframe(estilo, use_container_width=True)

# Layout 2 colunas (65% gráfico / 35% textos): no mobile o Streamlit já
# empilha `st.columns` automaticamente (gráfico primeiro, textos depois),
# então a mesma estrutura serve para desktop e mobile.
col_grafico, col_textos = st.columns([65, 35], vertical_alignment="center")
with col_grafico:
    share = analysis.share_liquidez(df, empresas_sel)
    # título + legenda já fazem parte da própria figura Plotly (ver
    # charts.pizza_share / _aplicar_tema); use_container_width faz o gráfico
    # ocupar 100% da largura desta coluna.
    st.plotly_chart(
        charts.pizza_share(share["volume"], empresas_sel, tema, "Share de liquidez no período"),
        use_container_width=True,
    )

ab = analysis.teste_ab(retornos)
with col_textos:
    # As duas "caixas de texto" empilhadas — vertical_alignment="center" no
    # st.columns acima já centraliza este bloco em relação à altura do gráfico.
    reading(share["leitura"])
    if ab:
        reading(
            f"Teste t de Welch dos retornos diários: p-valor = {ab['p_value']:.4f} "
            f"({ab['conclusao_curta']}). Média diária {ab['grupo_a']}: "
            f"{ab['media_a']:.4f}% · {ab['grupo_b']}: {ab['media_b']:.4f}%.",
            rotulo="Teste A/B (estatístico)",
            variante="warn",
        )
    else:
        st.info("Selecione NTCO3 e RADL3 para ver o teste A/B do notebook.")

if ab:
    # Gráfico de apoio do teste A/B (NTCO3 vs. RADL3): full-width abaixo do
    # grid principal, já que não é nem o "gráfico de rosca" nem um "texto".
    st.plotly_chart(
        charts.boxplot_precos(df[df["CODNEG"].isin([ab["grupo_a"], ab["grupo_b"]])],
                              [ab["grupo_a"], ab["grupo_b"]], tema,
                              f"{ab['grupo_a']} vs. {ab['grupo_b']} — fechamento"),
        use_container_width=True,
    )


# --------------------------------------------------------------------------- #
# RELAÇÕES / CORRELAÇÕES
# --------------------------------------------------------------------------- #
espaco("lg")
section(
    "05",
    "Relações e correlações",
    "A correlação dos retornos diários mostra quais ações tendem a se mover "
    "juntas. A linha e a coluna da NTCO3 estão destacadas.",
)
corr = analysis.matriz_correlacao(retornos, empresas_sel)
st.plotly_chart(
    charts.heatmap_correlacao(corr["correlacao"], tema, "Correlação dos retornos diários"),
    use_container_width=True,
)
reading(corr["leitura"])


# --------------------------------------------------------------------------- #
# RISCO E RETORNO
# --------------------------------------------------------------------------- #
espaco("lg")
section(
    "06",
    "Risco e retorno",
    "No plano risco × retorno, cada ponto é uma empresa: eixo horizontal = "
    "volatilidade diária, eixo vertical = retorno médio diário. As linhas "
    "pontilhadas marcam a mediana do grupo comparável.",
)
rr = analysis.risco_retorno(retornos, empresas_sel)
col_rr, col_dd = st.columns(2)
with col_rr:
    st.plotly_chart(
        charts.scatter_risco_retorno(
            rr["tabela"], rr["ref_retorno"], rr["ref_volatilidade"], empresas_sel, tema,
            "Risco × retorno diário",
        ),
        use_container_width=True,
    )
with col_dd:
    dd = analysis.drawdown(pivot, empresas_sel)
    st.plotly_chart(
        charts.drawdown_linhas(dd["drawdown"], empresas_sel, tema, "Drawdown frente ao pico anterior"),
        use_container_width=True,
    )
reading(rr["leitura"])
reading(dd["leitura"], variante="alt")

espaco("md")
_c1, _c2 = st.columns([2, 1], vertical_alignment="center")
with _c1:
    paragrafo(
        "A combinação de retorno abaixo da mediana com volatilidade acima da "
        "mediana é o quadrante menos favorável do gráfico de dispersão. O "
        "drawdown mede a maior queda de cada ação frente ao seu próprio pico."
    )
with _c2:
    render_illustration("imagem_03", "Risco, volatilidade e retorno")


# --------------------------------------------------------------------------- #
# SAZONALIDADE (NTCO3)
# --------------------------------------------------------------------------- #
espaco("lg")
section(
    "07",
    "Módulo de sazonalidade — NTCO3",
    "Investiga se há meses em que o comportamento da NTCO3 se diferencia, "
    "possivelmente associado a datas comerciais (Dia das Mães, Namorados, Pais, "
    "Black Friday, Natal). Sazonalidade só é afirmada com evidência de "
    "recorrência entre anos — as faixas de fundo são hipóteses, não causas.",
)
base_saz = analysis.preparar_sazonalidade(df)
if base_saz.empty or "NTCO3" not in empresas_sel:
    st.info("Inclua a NTCO3 na seleção (e um período com dados dela) para o módulo de sazonalidade.")
else:
    mensal = analysis.serie_mensal_sazonalidade(base_saz)
    consolidado = analysis.consolidado_mensal_sazonalidade(mensal)
    st.plotly_chart(
        charts.sazonalidade_preco_volume(mensal, tema, "NTCO3 — preço médio mensal × quantidade negociada"),
        use_container_width=True,
    )
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.plotly_chart(
            charts.sazonalidade_ano_a_ano(mensal, tema, "Preço médio mensal, ano a ano"),
            use_container_width=True,
        )
    with col_s2:
        st.plotly_chart(
            charts.sazonalidade_consolidada(consolidado, tema, "Comportamento médio por mês do ano"),
            use_container_width=True,
        )
    saz = analysis.insights_sazonalidade(mensal, consolidado)
    reading(saz["conclusao"], rotulo="Conclusão sobre sazonalidade", variante="warn")


# --------------------------------------------------------------------------- #
# INSIGHTS
# --------------------------------------------------------------------------- #
espaco("lg")
section(
    "08",
    "Insights",
    "Síntese da leitura exploratória para o recorte selecionado. Todos os "
    "valores vêm dos dados — nenhuma conclusão é assumida de antemão.",
)

insights = []
df_kpis = analysis.calcular_kpis(df, empresas_sel)
if not df_kpis.empty and "NTCO3" in df_kpis.index:
    ranking_cresc = df_kpis["Crescimento Acumulado (%)"].sort_values(ascending=False)
    pos_foco = list(ranking_cresc.index).index("NTCO3") + 1
    insights.append(
        f"No recorte atual, a NTCO3 ocupa a {pos_foco}ª posição de "
        f"{len(ranking_cresc)} em crescimento acumulado "
        f"({ranking_cresc['NTCO3']:.2f}%)."
    )
insights.append(evo["leitura"])
insights.append(rr["leitura"])
insights.append(corr["leitura"])
insights.append(dd["leitura"])
if "NTCO3" in empresas_sel and not base_saz.empty:
    saz = analysis.insights_sazonalidade(
        analysis.serie_mensal_sazonalidade(base_saz),
        analysis.consolidado_mensal_sazonalidade(analysis.serie_mensal_sazonalidade(base_saz)),
    )
    insights.extend(saz["insights"][:2])

insight_list([i for i in insights if i])

espaco("md")
paragrafo(
    "Nota de transparência (do notebook): os números são calculados a partir "
    "dos arquivos COTAHIST_A2025.TXT e COTAHIST_A2026.TXT. O dataset processado "
    "cobre os pregões reais das seis empresas do comparativo, com os dois "
    "tratamentos societários já aplicados."
)


# --------------------------------------------------------------------------- #
# FOOTER
# --------------------------------------------------------------------------- #
render_footer()
