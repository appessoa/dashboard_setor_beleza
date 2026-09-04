"""
CSS do infográfico editorial.

``css(tema)`` devolve um bloco ``<style>`` completo, parametrizado pelas cores
do tema (claro/escuro). A ideia é que a página pareça um infográfico impresso —
coluna central estreita, bastante espaço em branco, tipografia editorial — e
não um dashboard corporativo de cartões.
"""

from __future__ import annotations

from . import config


def css(tema: dict) -> str:
    t = tema
    return f"""
<style>
:root {{
    --bg: {t['bg']};
    --bg-bloco: {t['bg_bloco']};
    --bg-bloco-alt: {t['bg_bloco_alt']};
    --texto: {t['texto']};
    --texto-sec: {t['texto_secundario']};
    --verde: {t['verde']};
    --laranja: {t['laranja']};
    --terracota: {t['terracota']};
    --borda: {t['borda']};
}}

.stApp {{ background: var(--bg); }}
section[data-testid="stSidebar"] {{ background: var(--bg-bloco); border-right: 1px solid var(--borda); }}
section[data-testid="stSidebar"] * {{ color: var(--texto); }}
.block-container {{
    max-width: 1120px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}}
.stApp, .stApp p, .stApp li, .stApp span, .stApp label, .stMarkdown {{
    color: var(--texto);
}}

/* ---------- Header ---------- */
.ig-header {{
    border-bottom: 2px solid var(--verde);
    padding-bottom: 1rem;
    margin-bottom: 1.2rem;
}}
.ig-logo {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 1.7rem;
    letter-spacing: 0.42em;
    font-weight: 700;
    color: var(--verde);
    text-transform: uppercase;
}}
.ig-kicker {{
    text-transform: uppercase;
    letter-spacing: 0.22em;
    font-size: 0.72rem;
    color: var(--laranja);
    font-weight: 700;
    margin-top: 0.5rem;
}}
.ig-title {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: clamp(1.6rem, 3.4vw, 2.5rem);
    line-height: 1.16;
    font-weight: 700;
    margin: 0.3rem 0 0.2rem 0;
    color: var(--texto);
}}
.ig-subtitle {{
    color: var(--texto-sec);
    font-size: 0.98rem;
    max-width: 60ch;
}}

/* ---------- Seções ---------- */
.ig-section-num {{
    font-family: Georgia, serif;
    font-size: 0.8rem;
    letter-spacing: 0.2em;
    color: var(--laranja);
    font-weight: 700;
}}
.ig-section-title {{
    font-family: Georgia, serif;
    font-size: clamp(1.3rem, 2.6vw, 1.9rem);
    font-weight: 700;
    margin: 0.1rem 0 0.4rem 0;
    color: var(--texto);
    border-left: 4px solid var(--terracota);
    padding-left: 0.7rem;
}}
.ig-lead {{
    font-size: 1.05rem;
    line-height: 1.6;
    color: var(--texto);
    max-width: 64ch;
}}

/* ---------- Bloco de leitura editorial ---------- */
.ig-reading {{
    background: var(--bg-bloco);
    border-left: 3px solid var(--verde);
    border-radius: 4px;
    padding: 1rem 1.15rem;
    margin: 0.6rem 0 0.4rem 0;
}}
.ig-reading .rot {{
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--laranja);
    display: block;
    margin-bottom: 0.35rem;
}}
.ig-reading p {{
    margin: 0;
    font-size: 0.96rem;
    line-height: 1.55;
    color: var(--texto);
}}
.ig-reading.alt {{ border-left-color: var(--terracota); }}
.ig-reading.warn {{ border-left-color: var(--laranja); }}

/* ---------- KPIs editoriais ---------- */
.ig-kpis {{
    display: flex;
    flex-wrap: wrap;
    gap: 2.2rem;
    margin: 1rem 0 0.5rem 0;
    padding: 1rem 0;
    border-top: 1px solid var(--borda);
    border-bottom: 1px solid var(--borda);
}}
.ig-kpi .label {{
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.66rem;
    color: var(--texto-sec);
    font-weight: 700;
}}
.ig-kpi .value {{
    font-family: Georgia, serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--verde);
    line-height: 1.1;
}}

/* ---------- Insights ---------- */
.ig-insight {{
    display: flex;
    gap: 0.8rem;
    padding: 0.7rem 0;
    border-bottom: 1px dashed var(--borda);
    font-size: 0.98rem;
    line-height: 1.5;
}}
.ig-insight .n {{
    font-family: Georgia, serif;
    font-weight: 700;
    color: var(--terracota);
    font-size: 1.15rem;
    min-width: 1.6rem;
}}

/* ---------- Ilustrações ---------- */
.ig-illus-caption {{
    font-size: 0.78rem;
    color: var(--texto-sec);
    font-style: italic;
    margin-top: 0.3rem;
}}
div[data-testid="stImage"] img {{ border-radius: 6px; }}

/* ---------- Painel de cotações ao vivo (ticker / st.metric) ---------- */
div[data-testid="stMetric"] {{
    background: var(--bg-bloco);
    border: 1px solid var(--borda);
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
    /* evita que valores longos vazem para fora do cartão */
    overflow: hidden;
}}
div[data-testid="stMetric"] * {{ overflow-wrap: anywhere; }}
div[data-testid="stMetricLabel"] p {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--texto-sec);
}}

/* ---------- Correção de sobreposição / quebra de layout ---------- */
/* Respiro vertical entre blocos empilhados do Streamlit */
div[data-testid="stVerticalBlock"] > div {{ margin-bottom: 0.35rem; }}
/* Espaçamento lateral entre colunas para textos/gráficos não se tocarem */
div[data-testid="stHorizontalBlock"] {{ gap: 1.4rem; }}
div[data-testid="column"] {{ padding: 0 0.35rem; }}
/* Gráficos Plotly ocupam 100% da coluna e não estouram a largura */
div[data-testid="stPlotlyChart"], .js-plotly-plot, .plot-container {{
    width: 100% !important;
    max-width: 100%;
    margin: 0.4rem 0 0.8rem 0;
}}
/* Qualquer texto longo quebra em vez de vazar da tela */
.stApp p, .stApp li, .stApp span, .ig-lead, .ig-reading p, .ig-insight span,
.ig-subtitle, .ig-title, .ig-section-title {{
    overflow-wrap: break-word;
    word-break: break-word;
}}
/* KPIs editoriais: permite rolagem horizontal em telas estreitas */
.ig-kpis {{ overflow-x: auto; }}

/* ---------- Footer ---------- */
.ig-footer {{
    margin-top: 3rem;
    padding-top: 1.2rem;
    border-top: 2px solid var(--verde);
    font-size: 0.86rem;
    color: var(--texto-sec);
    line-height: 1.7;
}}
.ig-footer a {{ color: var(--verde); word-break: break-all; }}
.ig-footer strong {{ color: var(--texto); }}

/* ---------- Espaçadores ---------- */
.ig-space-sm {{ height: 1rem; }}
.ig-space-md {{ height: 2.2rem; }}
.ig-space-lg {{ height: 3.6rem; }}

/* ---------- Responsividade ---------- */
@media (max-width: 640px) {{
    .ig-kpis {{ gap: 1.2rem; }}
    .ig-kpi .value {{ font-size: 1.35rem; }}
    .ig-logo {{ font-size: 1.3rem; letter-spacing: 0.3em; }}
}}
</style>
"""


def config_toml_theme() -> dict:
    """Cores base para ``.streamlit/config.toml`` (tema claro do briefing)."""
    return {
        "primaryColor": config.TEMA_CLARO["verde"],
        "backgroundColor": config.TEMA_CLARO["bg"],
        "secondaryBackgroundColor": config.TEMA_CLARO["bege"],
        "textColor": config.TEMA_CLARO["texto"],
    }
