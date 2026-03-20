"""
Configurações centrais do Vértice IA.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

# ============================================
# Caminhos
# ============================================
RAIZ_PROJETO = Path(__file__).parent.parent
CAMINHO_DADOS = RAIZ_PROJETO / "dados"
CAMINHO_DOCUMENTOS = CAMINHO_DADOS / "documentos"
CAMINHO_BANCO = RAIZ_PROJETO / os.getenv("CAMINHO_BANCO", "banco/vertice.db")
CAMINHO_CHROMA = RAIZ_PROJETO / os.getenv("CAMINHO_CHROMA", "banco/chroma_db")

# ============================================
# Anthropic / Claude
# ============================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODELO_CLAUDE = os.getenv("MODELO_CLAUDE", "claude-haiku-4-5-20251001")

# ============================================
# RAG
# ============================================
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODELO_RERANQUEADOR = "cross-encoder/ms-marco-MiniLM-L-6-v2"
TAMANHO_CHUNK = 512
SOBREPOSICAO_CHUNK = 64
TOP_K_RECUPERACAO = 10
TOP_K_RERANQUEAMENTO = 5
LIMIAR_CONFIANCA = float(os.getenv("LIMIAR_CONFIANCA", "0.45"))

# ============================================
# LangFuse (Observabilidade)
# ============================================
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# ============================================
# Empresa fictícia
# ============================================
NOME_EMPRESA = "Vértice"
LOJAS = [
    # São Paulo (8)
    "Av. Paulista - SP",
    "Shopping Ibirapuera - SP",
    "Shopping Eldorado - SP",
    "Rua Oscar Freire - SP",
    "Shopping Morumbi - SP",
    "Shopping Center Norte - SP",
    "Jardins - SP",
    "Shopping Anália Franco - SP",
    # Rio de Janeiro (4)
    "Shopping RioSul - RJ",
    "Barra Shopping - RJ",
    "Shopping Tijuca - RJ",
    "Village Mall - RJ",
    # Curitiba (4)
    "Shopping Curitiba - PR",
    "Pátio Batel - PR",
    "Shopping Mueller - PR",
    "Rua XV de Novembro - PR",
    # Florianópolis (4)
    "Shopping Iguatemi - SC",
    "Beiramar Shopping - SC",
    "Shopping Itaguaçu - SC",
    "Norte Shopping Floripa - SC",
]
