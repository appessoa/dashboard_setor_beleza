"""
Componentes visuais reutilizáveis do infográfico (Streamlit + HTML/CSS).
"""

from __future__ import annotations

import base64
import html
from pathlib import Path

import streamlit as st

from . import config
from .formatting import formatar_moeda, formatar_percentual


# --------------------------------------------------------------------------- #
# Imagens
# --------------------------------------------------------------------------- #
def load_image(nome: str) -> Path | None:
    """
    Resolve o caminho de uma imagem em ``assets/`` (ou ``ASSETS_PATH``).
    Retorna ``None`` se o arquivo não existir — o app trata o fallback.
    """
    candidatos = [
        config.ASSETS_PATH / nome,
        config.ASSETS_PATH / f"{nome}.png",
    ]
    for caminho in candidatos:
        if caminho.exists():
            return caminho
    return None


def render_illustration(nome: str, legenda: str = "", largura: int | None = None) -> None:
    """Renderiza uma ilustração como elemento de respiro visual (sem virar card)."""
    caminho = load_image(nome)
    if caminho is None:
        st.markdown(
            f"<div class='ig-illus-caption'>[ilustração ausente: "
            f"<code>assets/{html.escape(nome)}.png</code>]</div>",
            unsafe_allow_html=True,
        )
        return
    st.image(str(caminho), width=largura, use_container_width=largura is None)
    if legenda:
        st.markdown(f"<div class='ig-illus-caption'>{html.escape(legenda)}</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
def render_logo() -> None:
    """
    Logo da Natura como imagem (assets/natura-108.png), centralizada.

    CORREÇÃO (item 1): a logo era renderizada à esquerda e quebrava o layout.
    Agora usamos 3 colunas [1, 2, 1] e, na coluna central, injetamos a imagem
    como <img> dentro de um flex container — assim ela fica perfeitamente
    centralizada (o st.image sozinho continuaria "colado" à esquerda da coluna).
    """
    _, col_centro, _ = st.columns([1, 2, 1])
    with col_centro:
        if config.LOGO_PATH.exists():
            dados = base64.b64encode(config.LOGO_PATH.read_bytes()).decode()
            st.markdown(
                f"<div style='display:flex;justify-content:center;margin:0.2rem 0 0.6rem 0'>"
                f"<img src='data:image/png;base64,{dados}' width='150' alt='Natura'></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='ig-logo' style='text-align:center'>Natura</div>",
                unsafe_allow_html=True,
            )


def render_header(subtitulo: str) -> None:
    st.markdown("<div class='ig-header'>", unsafe_allow_html=True)
    render_logo()
    st.markdown(
        f"""
        <div class='ig-kicker'>Análise Exploratória de Dados · B3</div>
        <div class='ig-title'>{html.escape(config.TITULO_APP)}</div>
        <div class='ig-subtitle'>{html.escape(subtitulo)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Seções e textos editoriais
# --------------------------------------------------------------------------- #
def section(numero: str, titulo: str, lead: str = "") -> None:
    st.markdown(
        f"<div class='ig-section-num'>{html.escape(numero)}</div>"
        f"<div class='ig-section-title'>{html.escape(titulo)}</div>",
        unsafe_allow_html=True,
    )
    if lead:
        st.markdown(f"<p class='ig-lead'>{html.escape(lead)}</p>", unsafe_allow_html=True)
    # CORREÇÃO (item 3): respiro entre o cabeçalho da seção e o gráfico logo abaixo,
    # evitando que o título do Plotly encoste no texto da seção.
    st.markdown("<div class='ig-space-sm'></div>", unsafe_allow_html=True)


def reading(texto: str, rotulo: str = "Leitura do gráfico", variante: str = "") -> None:
    """Bloco editorial de 'leitura' (interpretação curta e acadêmica do gráfico)."""
    classe = "ig-reading" + (f" {variante}" if variante else "")
    st.markdown(
        f"<div class='{classe}'><span class='rot'>{html.escape(rotulo)}</span>"
        f"<p>{html.escape(texto)}</p></div>",
        unsafe_allow_html=True,
    )


def paragrafo(texto: str) -> None:
    st.markdown(f"<p class='ig-lead'>{html.escape(texto)}</p>", unsafe_allow_html=True)


def espaco(tamanho: str = "md") -> None:
    st.markdown(f"<div class='ig-space-{tamanho}'></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# KPIs editoriais
# --------------------------------------------------------------------------- #
def kpi_row(kpis: dict) -> None:
    itens = [
        ("Mediana do fechamento", formatar_moeda(kpis["mediana_fechamento"])),
        ("Evolução mediana do grupo", formatar_percentual(kpis["evolucao_mediana_grupo"])),
        ("Empresas analisadas", str(kpis["empresas_analisadas"])),
        ("Período", kpis["periodo"]),
        ("Pregões no recorte", f"{kpis['pregoes']:,}".replace(",", ".")),
    ]
    blocos = "".join(
        f"<div class='ig-kpi'><div class='label'>{html.escape(l)}</div>"
        f"<div class='value'>{html.escape(str(v))}</div></div>"
        for l, v in itens
    )
    st.markdown(f"<div class='ig-kpis'>{blocos}</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Insights
# --------------------------------------------------------------------------- #
def insight_list(insights: list[str]) -> None:
    for i, texto in enumerate(insights, start=1):
        st.markdown(
            f"<div class='ig-insight'><span class='n'>{i:02d}</span>"
            f"<span>{html.escape(texto)}</span></div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------- #
# Footer
# --------------------------------------------------------------------------- #
def render_footer() -> None:
    f = config.FOOTER
    st.markdown(
        f"""
        <div class='ig-footer'>
            <strong>{html.escape(f['linha_1'])}</strong><br>
            Professor: {html.escape(f['professor'])}<br>
            Curso: {html.escape(f['curso'])}<br>
            Dataset: <a href="{f['dataset_url']}" target="_blank" rel="noopener">{f['dataset_url']}</a><br>
            Aluno: {html.escape(f['aluno'])}
        </div>
        """,
        unsafe_allow_html=True,
    )
