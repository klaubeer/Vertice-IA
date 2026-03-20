"""
Pipeline de avaliação do RAG.
Executa o dataset de avaliação e calcula métricas agregadas.
Uso: python -m avaliacao.avaliar_rag
"""

import json
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import track

from configuracao.config import CAMINHO_DADOS
from rag.pipeline import obter_pipeline
from agentes.roteador import Roteador
from avaliacao.metricas import (
    avaliar_fidelidade,
    avaliar_relevancia_contexto,
    avaliar_correcao,
    avaliar_fundamentacao,
)

console = Console()


def carregar_dataset() -> list:
    """Carrega o dataset de avaliação."""
    caminho = CAMINHO_DADOS / "dataset_avaliacao.json"
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def avaliar_roteamento(dataset: list) -> dict:
    """Avalia a precisão do roteador."""
    roteador = Roteador()
    acertos = 0
    total = len(dataset)

    for item in track(dataset, description="Avaliando roteamento..."):
        classificacao = roteador.classificar(item["pergunta"])
        agente = classificacao.get("agente", "")
        if agente == item["agente_esperado"]:
            acertos += 1

    return {
        "acertos": acertos,
        "total": total,
        "precisao": round(acertos / total * 100, 1) if total else 0,
    }


def avaliar_pipeline_rag(dataset: list) -> dict:
    """Avalia o pipeline RAG com métricas de qualidade."""
    pipeline = obter_pipeline()

    # Filtra apenas perguntas que usam RAG (não estoque/bi)
    perguntas_rag = [
        item for item in dataset
        if item["agente_esperado"] in ("cliente", "rh")
    ]

    resultados = []

    for item in track(perguntas_rag, description="Avaliando RAG..."):
        resultado_rag = pipeline.executar(item["pergunta"])

        # Avaliar métricas
        fidelidade = avaliar_fidelidade(
            resultado_rag.contexto[:500],  # Simula resposta com contexto
            resultado_rag.contexto,
        )
        relevancia = avaliar_relevancia_contexto(
            item["pergunta"],
            resultado_rag.contexto,
        )
        correcao = avaliar_correcao(
            item["pergunta"],
            resultado_rag.contexto[:500],
            item["resposta_esperada"],
        )
        fundamentacao = avaliar_fundamentacao(
            resultado_rag.contexto[:500],
            resultado_rag.fontes,
        )

        resultados.append({
            "id": item["id"],
            "pergunta": item["pergunta"][:80],
            "fidelidade": fidelidade,
            "relevancia": relevancia,
            "correcao": correcao,
            "fundamentacao": fundamentacao,
            "score_confianca": resultado_rag.score_confianca,
            "latencia_ms": resultado_rag.latencia_total_ms,
            "chunks_recuperados": resultado_rag.total_chunks_recuperados,
        })

    # Calcula médias
    n = len(resultados)
    if n == 0:
        return {"mensagem": "Nenhuma pergunta RAG encontrada."}

    medias = {
        "fidelidade": round(sum(r["fidelidade"] for r in resultados) / n, 4),
        "relevancia": round(sum(r["relevancia"] for r in resultados) / n, 4),
        "correcao": round(sum(r["correcao"] for r in resultados) / n, 4),
        "fundamentacao": round(sum(r["fundamentacao"] for r in resultados) / n, 4),
        "score_confianca_medio": round(sum(r["score_confianca"] for r in resultados) / n, 4),
        "latencia_media_ms": round(sum(r["latencia_ms"] for r in resultados) / n, 1),
        "total_avaliadas": n,
    }

    return {"medias": medias, "detalhes": resultados}


def exibir_resultados(resultado_roteamento: dict, resultado_rag: dict):
    """Exibe resultados formatados no terminal."""
    console.print("\n")
    console.rule("[bold blue]Resultado da Avaliação — Vértice IA[/bold blue]")

    # Roteamento
    console.print("\n[bold]1. Roteamento[/bold]")
    tabela_rot = Table()
    tabela_rot.add_column("Métrica", style="cyan")
    tabela_rot.add_column("Valor", style="green")
    tabela_rot.add_row("Acertos", f'{resultado_roteamento["acertos"]}/{resultado_roteamento["total"]}')
    tabela_rot.add_row("Precisão", f'{resultado_roteamento["precisao"]}%')
    console.print(tabela_rot)

    # RAG
    if "medias" in resultado_rag:
        medias = resultado_rag["medias"]
        console.print("\n[bold]2. Pipeline RAG[/bold]")
        tabela_rag = Table()
        tabela_rag.add_column("Métrica", style="cyan")
        tabela_rag.add_column("Score", style="green")
        tabela_rag.add_column("Meta", style="yellow")
        tabela_rag.add_column("Status", style="bold")

        metricas_meta = {
            "Fidelidade": (medias["fidelidade"], 0.85),
            "Relevância do Contexto": (medias["relevancia"], 0.80),
            "Correção": (medias["correcao"], 0.80),
            "Fundamentação": (medias["fundamentacao"], 0.90),
        }

        for nome, (score, meta) in metricas_meta.items():
            status = "✅" if score >= meta else "❌"
            tabela_rag.add_row(nome, f"{score:.2f}", f"≥ {meta:.2f}", status)

        tabela_rag.add_row("", "", "", "")
        tabela_rag.add_row("Score médio", f'{medias["score_confianca_medio"]:.2f}', "", "")
        tabela_rag.add_row("Latência média", f'{medias["latencia_media_ms"]:.0f}ms', "", "")
        tabela_rag.add_row("Perguntas avaliadas", str(medias["total_avaliadas"]), "", "")

        console.print(tabela_rag)

    console.print("\n")


def main():
    """Executa avaliação completa."""
    console.print("[bold blue]Iniciando avaliação do Vértice IA...[/bold blue]\n")

    dataset = carregar_dataset()
    console.print(f"Dataset: {len(dataset)} perguntas carregadas\n")

    # 1. Avalia roteamento
    resultado_rot = avaliar_roteamento(dataset)

    # 2. Avalia RAG
    resultado_rag = avaliar_pipeline_rag(dataset)

    # 3. Exibe resultados
    exibir_resultados(resultado_rot, resultado_rag)

    # 4. Salva resultados
    saida = {
        "roteamento": resultado_rot,
        "rag": resultado_rag.get("medias", {}),
    }
    caminho_saida = CAMINHO_DADOS / "resultado_avaliacao.json"
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    console.print(f"[green]Resultados salvos em {caminho_saida}[/green]")


if __name__ == "__main__":
    main()
