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

# Sidebar — navegação
with st.sidebar:
    st.markdown("## 🔷 Vértice IA")
    st.markdown("Sistema Multi-Agente de Atendimento")
    st.divider()

    st.markdown("**🗂️ Navegue por aqui**")
    pagina = st.radio(
        "Navegação",
        [
            "💬 Chat com Agente",
            "📦 Estoque e Políticas",
            "📊 Dashboard BI",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # Mini-README na sidebar
    st.markdown("### 🧠 O que é isso?")
    st.markdown("""
Demonstração de um **sistema multi-agente com RAG** capaz de atender automaticamente clientes, funcionários e gestores — sem intervenção humana.

**Agentes ativos:**
- 🟣 **Cliente** — políticas de devolução, envio e garantia
- 🔵 **Estoque** — consultas em tempo real via SQL
- 🟢 **RH** — benefícios, férias, normas internas
- 🟠 **BI** — métricas de atendimento e performance

**Stack:**
Claude API · RAG Híbrido · BM25 · Reranking · Guardrails · SQLite · ChromaDB
""")

    st.divider()
    st.markdown(
        "<small>Powered by <strong>Klauber Fischer</strong></small>",
        unsafe_allow_html=True,
    )

# Roteamento de páginas
if pagina == "💬 Chat com Agente":
    from interface.pagina_chat import renderizar
    renderizar()
elif pagina == "📦 Estoque e Políticas":
    from interface.pagina_estoque import renderizar
    renderizar()
elif pagina == "📊 Dashboard BI":
    from interface.pagina_dashboard import renderizar
    renderizar()
