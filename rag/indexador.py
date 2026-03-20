"""
Indexador de documentos para o pipeline RAG.
Realiza chunking dos documentos e indexa no ChromaDB com embeddings multilíngues.
Uso: python -m rag.indexador
"""

import hashlib
import re
from pathlib import Path
from typing import List, Dict

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from configuracao.config import (
    CAMINHO_DOCUMENTOS, CAMINHO_CHROMA,
    MODELO_EMBEDDINGS, TAMANHO_CHUNK, SOBREPOSICAO_CHUNK
)

NOME_COLECAO = "vertice_documentos"


def carregar_documentos(caminho: Path = CAMINHO_DOCUMENTOS) -> List[Dict]:
    """Carrega todos os documentos .md da pasta de documentos."""
    documentos = []
    for arquivo in sorted(caminho.glob("*.md")):
        conteudo = arquivo.read_text(encoding="utf-8")
        documentos.append({
            "nome": arquivo.stem,
            "arquivo": arquivo.name,
            "conteudo": conteudo,
        })
        print(f"  [+] {arquivo.name} ({len(conteudo)} caracteres)")
    return documentos


def dividir_em_chunks(texto: str, nome_doc: str,
                       tamanho: int = TAMANHO_CHUNK,
                       sobreposicao: int = SOBREPOSICAO_CHUNK) -> List[Dict]:
    """
    Divide o texto em chunks com sobreposição.
    Tenta dividir em seções markdown (##) primeiro, e depois por tamanho.
    """
    # Divide por seções markdown (## )
    secoes = re.split(r'\n(?=## )', texto)
    chunks = []

    for secao in secoes:
        secao = secao.strip()
        if not secao:
            continue

        # Extrai título da seção se houver
        titulo_secao = ""
        linhas = secao.split("\n")
        if linhas and linhas[0].startswith("#"):
            titulo_secao = linhas[0].lstrip("#").strip()

        # Se a seção é menor que o tamanho do chunk, usa inteira
        if len(secao) <= tamanho:
            chunk_id = hashlib.md5(secao.encode()).hexdigest()[:12]
            chunks.append({
                "id": f"{nome_doc}_{chunk_id}",
                "texto": secao,
                "documento": nome_doc,
                "secao": titulo_secao,
            })
        else:
            # Divide em sub-chunks com sobreposição
            palavras = secao.split()
            inicio = 0
            palavras_por_chunk = tamanho // 5  # ~5 chars por palavra em PT

            while inicio < len(palavras):
                fim = min(inicio + palavras_por_chunk, len(palavras))
                trecho = " ".join(palavras[inicio:fim])
                chunk_id = hashlib.md5(trecho.encode()).hexdigest()[:12]

                chunks.append({
                    "id": f"{nome_doc}_{chunk_id}",
                    "texto": trecho,
                    "documento": nome_doc,
                    "secao": titulo_secao,
                })
                inicio = fim - (sobreposicao // 5) if fim < len(palavras) else fim

    return chunks


def criar_indice(documentos: List[Dict]) -> int:
    """Cria o índice vetorial no ChromaDB."""
    CAMINHO_CHROMA.parent.mkdir(parents=True, exist_ok=True)

    # Inicializa o modelo de embeddings
    print(f"\n[...] Carregando modelo de embeddings: {MODELO_EMBEDDINGS}")
    modelo = SentenceTransformer(MODELO_EMBEDDINGS)

    # Inicializa ChromaDB
    cliente = chromadb.PersistentClient(path=str(CAMINHO_CHROMA))

    # Remove coleção existente se houver
    try:
        cliente.delete_collection(NOME_COLECAO)
    except Exception:
        pass

    colecao = cliente.create_collection(
        name=NOME_COLECAO,
        metadata={"hnsw:space": "cosine"}
    )

    # Processa todos os documentos
    todos_chunks = []
    for doc in documentos:
        chunks = dividir_em_chunks(doc["conteudo"], doc["nome"])
        todos_chunks.extend(chunks)

    print(f"\n[...] Indexando {len(todos_chunks)} chunks...")

    # Gera embeddings e insere no ChromaDB
    textos = [c["texto"] for c in todos_chunks]
    ids = [c["id"] for c in todos_chunks]
    metadados = [{"documento": c["documento"], "secao": c["secao"]} for c in todos_chunks]

    embeddings = modelo.encode(textos, show_progress_bar=True).tolist()

    colecao.add(
        documents=textos,
        embeddings=embeddings,
        metadatas=metadados,
        ids=ids,
    )

    print(f"[OK] {len(todos_chunks)} chunks indexados no ChromaDB")
    return len(todos_chunks)


def indexar():
    """Pipeline completo de indexação."""
    print("=" * 50)
    print("Indexador de Documentos — Vértice IA")
    print("=" * 50)

    print(f"\n[1/3] Carregando documentos de {CAMINHO_DOCUMENTOS}...")
    documentos = carregar_documentos()

    if not documentos:
        print("[AVISO] Nenhum documento encontrado!")
        return

    print(f"\n[2/3] Dividindo em chunks...")
    total = 0
    for doc in documentos:
        chunks = dividir_em_chunks(doc["conteudo"], doc["nome"])
        total += len(chunks)
        print(f"  {doc['arquivo']}: {len(chunks)} chunks")

    print(f"\n[3/3] Criando índice vetorial...")
    total_indexado = criar_indice(documentos)

    print(f"\n{'=' * 50}")
    print(f"[OK] Indexação concluída: {total_indexado} chunks indexados")
    print(f"     Documentos: {len(documentos)}")
    print(f"     Caminho ChromaDB: {CAMINHO_CHROMA}")


if __name__ == "__main__":
    indexar()
