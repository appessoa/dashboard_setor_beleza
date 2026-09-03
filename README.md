# Análise Exploratória: Tendências e Evolução do Setor de Beleza no Mercado Financeiro

Infográfico analítico interativo (Streamlit) construído a partir das **Séries
Históricas da B3** (arquivos COTAHIST, 2025–2026). É a conversão, em aplicação
web, do notebook `notebook/notebook_original.ipynb`.

## Sobre

O estudo isola seis ativos ligados a beleza, farma e varejo de saúde listados na
B3 e faz uma leitura exploratória de como a **Natura (NTCO3)** se comporta frente
a esse grupo comparável: dispersão de preços, distribuição de retornos, evolução
indexada, volume/liquidez, correlações, risco × retorno, drawdown e um módulo de
sazonalidade da NTCO3.

Dois eventos societários reais são tratados nos dados antes de qualquer
comparação (metodologia preservada do notebook):

- **NTCO3 → NATU3 (01/07/2025):** troca de ticker (mesma empresa, conversão 1:1).
  Os registros de NATU3 são unidos à série da NTCO3.
- **Grupamento 10:1 da ESPA3 (15/06/2026):** preços anteriores ao grupamento são
  multiplicados por 10 e a quantidade negociada dividida por 10, deixando a série
  comparável.

Empresas analisadas: `NTCO3` (foco), `COTY34`, `HYPE3`, `PNVL3`, `RADL3`, `ESPA3`.

## Tecnologias

Python · Pandas · NumPy · SciPy · Plotly · Streamlit

## Fonte dos dados

B3 — Séries Históricas (mercado à vista):
<https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/series-historicas/>

## Execução local

```bash
# 1. criar e ativar o ambiente virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# 2. instalar dependências
pip install -r requirements.txt

# 3. (opcional) gerar o dataset processado a partir dos COTAHIST
#    O repositório já traz data/beleza.parquet pronto. Rode isto apenas
#    se quiser regenerá-lo a partir dos arquivos brutos da B3.
python scripts/preprocess_data.py
#    ou apontando a pasta dos TXT:
python scripts/preprocess_data.py --raw "C:/caminho/para/os/COTAHIST"

# 4. rodar o app
streamlit run app.py
```

O app abre em <http://localhost:8501>.

## Estrutura

```
dashboard_setor_beleza/
├── app.py                     # aplicação Streamlit (narrativa do infográfico)
├── src/
│   ├── config.py              # caminhos relativos, tickers, paleta, temas, rodapé
│   ├── data.py                # parser COTAHIST + tratamentos societários + carga do parquet
│   ├── analysis.py            # todos os cálculos do notebook (KPIs, retornos, correlação…)
│   ├── charts.py              # gráficos Plotly (versão interativa dos gráficos do notebook)
│   ├── components.py          # header, blocos de leitura, KPIs, ilustrações, footer
│   ├── styles.py              # CSS do infográfico editorial (tema claro/escuro)
│   └── formatting.py          # formatação de moeda/percentual (padrão brasileiro)
├── scripts/
│   └── preprocess_data.py     # COTAHIST_A*.TXT  ->  data/beleza.parquet
├── assets/                    # imagem_01.png, imagem_02.png, imagem_03.png, logo_natura.png
├── data/
│   ├── raw/                   # arquivos brutos da B3 (NÃO versionados)
│   └── beleza.parquet         # dataset processado (versionado)
├── .streamlit/config.toml     # tema base do Streamlit
├── notebook/notebook_original.ipynb   # notebook original, preservado
├── requirements.txt
├── .env.example
└── .gitignore
```

## Imagens

Coloque em `assets/`:

| Arquivo               | Uso no infográfico                          |
|-----------------------|--------------------------------------------|
| `imagem_01.png`       | seção "Visão geral"                         |
| `imagem_02.png`       | seção "Evolução ao longo do tempo"          |
| `imagem_03.png`       | seção "Risco e retorno"                     |
| `logo_natura.png`     | logo no header (opcional)                   |

Se `logo_natura.png` não existir, o header mostra um fallback textual elegante
("Natura"). As três ilustrações já acompanham o projeto.

## Dataset

Os arquivos brutos `COTAHIST_A2025.TXT` / `COTAHIST_A2026.TXT` (~1,4 GB no total)
**não são versionados** (`.gitignore`). O dashboard **não** os lê diretamente:
`scripts/preprocess_data.py` faz uma varredura eficiente, filtra apenas os
tickers da análise, aplica os tratamentos e grava `data/beleza.parquet`
(~2,4 mil linhas), que **é** versionado e é o único arquivo de dados que o app
carrega (com `@st.cache_data`).

## Publicação no Streamlit Community Cloud

1. Suba o projeto para um repositório no GitHub (ver abaixo).
2. Acesse <https://share.streamlit.io> e faça login com o GitHub.
3. **New app** → selecione o repositório, o branch `main` e o arquivo
   principal `app.py` (caminho: `dashboard_setor_beleza/app.py` se o projeto
   estiver em subpasta; ou apenas `app.py` se for a raiz do repositório).
4. **Deploy**. O Streamlit instala o `requirements.txt` automaticamente.
5. A aplicação fica disponível em uma URL no formato
   `https://<usuario>-<repo>-<hash>.streamlit.app`.

Como todos os caminhos no código são relativos (`Path(__file__).resolve().parent`),
o app funciona sem alterações tanto localmente quanto no Streamlit Cloud.

## GitHub

```bash
git init
git add .
git commit -m "feat: cria dashboard interativo do setor de beleza"
git branch -M main
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```

---

Séries Históricas B3 (2025-2026) · Professor: Eronides da Silva Neto ·
Curso: Especialização em Engenharia de Dados · Aluno: Ana Paula Ferreira Pessoa
