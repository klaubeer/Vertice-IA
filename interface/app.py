"""
Aplicação principal Streamlit — Vértice IA.
Navegação entre as 3 telas do sistema.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Vértice IA",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #6C5CE7;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #636e72;
        margin-top: 0;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #6C5CE7;
    }
    .confidence-high { color: #00b894; font-weight: bold; }
    .confidence-medium { color: #fdcb6e; font-weight: bold; }
    .confidence-low { color: #e17055; font-weight: bold; }
    .agent-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Normaliza fontes dentro das mensagens do chat */
    [data-testid="stChatMessage"] h1 {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        margin: 6px 0 4px 0 !important;
    }
    [data-testid="stChatMessage"] h2 {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        margin: 6px 0 4px 0 !important;
    }
    [data-testid="stChatMessage"] h3 {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        margin: 4px 0 2px 0 !important;
    }
    [data-testid="stChatMessage"] p {
        font-size: 0.88rem !important;
        margin: 3px 0 !important;
        line-height: 1.5 !important;
    }
    [data-testid="stChatMessage"] li {
        font-size: 0.88rem !important;
        line-height: 1.5 !important;
    }
    [data-testid="stChatMessage"] table {
        font-size: 0.82rem !important;
    }
</style>
""", unsafe_allow_html=True)

PAGINAS = [
    "🏠 Início",
    "💬 Chat com Agente",
    "📦 Estoque e Políticas",
    "📊 Dashboard BI",
]


@st.cache_resource(show_spinner="Carregando modelos de IA...")
def _pre_carregar_pipeline():
    """Carrega o pipeline RAG (embeddings + reranker) uma única vez por processo."""
    from rag.pipeline import obter_pipeline
    return obter_pipeline()


# Pré-carrega na tela inicial para evitar espera ao entrar no Chat
_pre_carregar_pipeline()

# Garante que a sessão inicia na página Início
if "pagina" not in st.session_state:
    st.session_state.pagina = "🏠 Início"

# Sidebar — navegação
with st.sidebar:
    st.markdown("## 🔷 Vértice IA")
    st.markdown("Sistema Multi-Agente de Atendimento")
    st.divider()

    st.markdown("**🗂️ Navegue por aqui**")
    pagina = st.radio(
        "Navegação",
        PAGINAS,
        key="pagina",
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown(
        "<small>Powered by <strong>Klauber Fischer</strong></small>",
        unsafe_allow_html=True,
    )


def _ir_para(destino: str):
    st.session_state.pagina = destino


def renderizar_inicio():
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem 0;">
        <p style="font-size:3rem; margin:0;">🔷</p>
        <h1 style="font-size:2.4rem; font-weight:800; color:#6C5CE7; margin:0.2rem 0;">Vértice IA</h1>
        <p style="font-size:1.1rem; color:#636e72; margin:0.3rem 0 0.1rem 0;">
            Sistema Multi-Agente de Atendimento Autônomo
        </p>
        <p style="font-size:0.85rem; color:#b2bec3;">
            Moda urbana · 20 lojas · ~1.000 funcionários · R$ 900M/ano
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Cards das 3 telas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="border:2px solid #6C5CE7; border-radius:12px; padding:1.2rem; min-height:200px;">
            <p style="font-size:2rem; margin:0;">💬</p>
            <h3 style="color:#6C5CE7; margin:0.3rem 0;">Chat com Agente</h3>
            <p style="font-size:0.85rem; color:#636e72; margin:0.5rem 0 1rem 0;">
                Converse com agentes especializados em atendimento ao cliente, estoque, RH e métricas.
                Guardrails ativos e score de confiança em tempo real.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Abrir Chat →", key="btn_chat", use_container_width=True,
                  on_click=_ir_para, args=("💬 Chat com Agente",))

    with col2:
        st.markdown("""
        <div style="border:2px solid #0984E3; border-radius:12px; padding:1.2rem; min-height:200px;">
            <p style="font-size:2rem; margin:0;">📦</p>
            <h3 style="color:#0984E3; margin:0.3rem 0;">Estoque e Políticas</h3>
            <p style="font-size:0.85rem; color:#636e72; margin:0.5rem 0 1rem 0;">
                Consulte o estoque em tempo real por produto, tamanho, cor e loja.
                Visualize as políticas de devolução, envio e garantia.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Ver Estoque →", key="btn_estoque", use_container_width=True,
                  on_click=_ir_para, args=("📦 Estoque e Políticas",))

    with col3:
        st.markdown("""
        <div style="border:2px solid #E17055; border-radius:12px; padding:1.2rem; min-height:200px;">
            <p style="font-size:2rem; margin:0;">📊</p>
            <h3 style="color:#E17055; margin:0.3rem 0;">Dashboard BI</h3>
            <p style="font-size:0.85rem; color:#636e72; margin:0.5rem 0 1rem 0;">
                KPIs de atendimento, taxa de resolução autônoma, estoque crítico e
                performance por agente — alimentado pelos atendimentos reais.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Ver Dashboard →", key="btn_bi", use_container_width=True,
                  on_click=_ir_para, args=("📊 Dashboard BI",))

    st.divider()

    # Sobre o projeto
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown("### 🧠 Como funciona")
        st.markdown("""
O usuário faz uma pergunta em linguagem natural. O **Agente Roteador** classifica a intenção e
delega ao agente especializado correto:

| Agente | Método | Casos de uso |
|---|---|---|
| 🟣 **Cliente** | RAG Híbrido | Devoluções, envio, garantia |
| 🔵 **Estoque** | Tool Calling (SQL) | Disponibilidade por loja/tamanho |
| 🟢 **RH** | RAG Híbrido | Férias, benefícios, normas |
| 🟠 **BI** | Tool Calling (SQL) | KPIs, métricas, atendimentos |

Guardrails bloqueiam **prompt injection** e mascaram **dados sensíveis (PII)** antes de
qualquer chamada ao LLM.
        """)

    with col_b:
        st.markdown("### ⚙️ Stack Técnica")
        st.markdown("""
**LLM**
Claude API · Haiku 3.5

**RAG**
ChromaDB · BM25 · RRF
Cross-Encoder Reranking
Embeddings Multilingual

**Dados**
SQLite · 15 SKUs × 20 lojas
Políticas em Markdown

**Frontend**
Streamlit · Plotly

**Segurança**
Detecção de Injection
Filtro de PII
Validação de Resposta
        """)

    st.divider()

    # Seção de integrações
    st.markdown("### 🔌 Pronto para Integração")
    st.caption("Os agentes expõem uma API REST simples e podem ser conectados a qualquer canal de atendimento.")

    ci1, ci2, ci3, ci4, ci5 = st.columns(5)
    with ci1:
        st.markdown("📱\n\n**WhatsApp**")
    with ci2:
        st.markdown("✈️\n\n**Telegram**")
    with ci3:
        st.markdown("💼\n\n**Slack**")
    with ci4:
        st.markdown("🏢\n\n**Omnichannel**")
    with ci5:
        st.markdown("⚙️\n\n**API própria**")

    st.caption("A lógica de roteamento, RAG e guardrails é independente do canal — o Streamlit é apenas um dos possíveis clientes.")

    st.divider()
    st.markdown(
        "<p style='text-align:center; color:#b2bec3; font-size:0.8rem;'>"
        "Projeto de portfólio · Dados fictícios · "
        "Powered by <strong>Klauber Fischer</strong></p>",
        unsafe_allow_html=True,
    )


# Roteamento de páginas
if pagina == "🏠 Início":
    renderizar_inicio()
elif pagina == "💬 Chat com Agente":
    from interface.pagina_chat import renderizar
    renderizar()
elif pagina == "📦 Estoque e Políticas":
    from interface.pagina_estoque import renderizar
    renderizar()
elif pagina == "📊 Dashboard BI":
    from interface.pagina_dashboard import renderizar
    renderizar()
