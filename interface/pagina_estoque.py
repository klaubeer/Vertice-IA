"""
Tela 2 — Consulta de Estoque e Políticas.
Visualização tabular do estoque e leitura das políticas.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from ferramentas.consulta_estoque import (
    consultar_estoque, obter_estoque_critico, resumo_estoque_por_loja
)
from configuracao.config import CAMINHO_DOCUMENTOS


def renderizar():
    """Renderiza a página de estoque e políticas."""
    st.markdown('<p class="main-header">📦 Estoque e Políticas</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Consulte o estoque das lojas e as políticas da empresa</p>',
        unsafe_allow_html=True,
    )

    tab_estoque, tab_politicas = st.tabs(["📦 Estoque", "📋 Políticas"])

    # ========================================
    # Tab Estoque
    # ========================================
    with tab_estoque:
        st.subheader("Filtros")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            filtro_categoria = st.selectbox(
                "Categoria",
                ["Todas", "camiseta", "calca", "bone"],
            )
        with col2:
            filtro_tamanho = st.selectbox(
                "Tamanho",
                ["Todos", "PP", "P", "M", "G", "GG", "U"],
            )
        with col3:
            from configuracao.config import LOJAS
            filtro_loja = st.selectbox(
                "Loja",
                ["Todas"] + LOJAS,
            )
        with col4:
            apenas_critico = st.checkbox("Apenas estoque crítico", value=False)

        # Consulta
        params = {}
        if filtro_categoria != "Todas":
            params["categoria"] = filtro_categoria
        if filtro_tamanho != "Todos":
            params["tamanho"] = filtro_tamanho
        if filtro_loja != "Todas":
            params["loja"] = filtro_loja

        if apenas_critico:
            dados = obter_estoque_critico(loja=params.get("loja"))
            if dados:
                df = pd.DataFrame(dados)
                st.warning(f"⚠️ {len(df)} itens com estoque crítico")
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "deficit": st.column_config.NumberColumn(
                            "Déficit",
                            help="Unidades abaixo do mínimo",
                        ),
                    },
                )
            else:
                st.success("✅ Nenhum item com estoque crítico nos filtros selecionados.")
        else:
            dados = consultar_estoque(**params)
            if dados:
                df = pd.DataFrame(dados)

                # Destaca estoque crítico
                st.info(f"📊 {len(df)} registros encontrados")
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "preco": st.column_config.NumberColumn(
                            "Preço (R$)", format="R$ %.2f"
                        ),
                        "estoque_critico": st.column_config.CheckboxColumn(
                            "Crítico?", default=False
                        ),
                    },
                )
            else:
                st.info("Nenhum resultado para os filtros selecionados.")

        # Resumo por loja
        st.divider()
        st.subheader("Resumo por Loja")

        resumo = resumo_estoque_por_loja()
        if resumo:
            df_resumo = pd.DataFrame(resumo)
            col_a, col_b = st.columns([2, 1])

            with col_a:
                st.dataframe(
                    df_resumo,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "valor_total": st.column_config.NumberColumn(
                            "Valor Total (R$)", format="R$ %.2f"
                        ),
                    },
                )

            with col_b:
                import plotly.express as px
                fig = px.bar(
                    df_resumo,
                    x="loja",
                    y="total_pecas",
                    title="Total de Peças por Loja",
                    color="total_pecas",
                    color_continuous_scale="Viridis",
                )
                fig.update_layout(
                    xaxis_tickangle=-45,
                    height=350,
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

    # ========================================
    # Tab Políticas
    # ========================================
    with tab_politicas:
        st.subheader("Documentos da Empresa")

        politica_selecionada = st.selectbox(
            "Selecione o documento",
            [
                "politica_devolucao",
                "politica_envio",
                "politica_garantia",
                "sobre_empresa",
                "manual_rh",
            ],
            format_func=lambda x: {
                "politica_devolucao": "📋 Política de Devolução e Troca",
                "politica_envio": "🚚 Política de Envio",
                "politica_garantia": "🛡️ Política de Garantia",
                "sobre_empresa": "🏢 Sobre a Empresa",
                "manual_rh": "👥 Manual de RH",
            }.get(x, x),
        )

        # Busca textual
        busca = st.text_input("🔍 Buscar no documento", placeholder="Digite para filtrar...")

        # Carrega e exibe
        caminho = CAMINHO_DOCUMENTOS / f"{politica_selecionada}.md"
        if caminho.exists():
            conteudo = caminho.read_text(encoding="utf-8")

            if busca:
                # Filtra parágrafos que contêm o termo
                paragrafos = conteudo.split("\n\n")
                filtrados = [
                    p for p in paragrafos
                    if busca.lower() in p.lower()
                ]
                if filtrados:
                    st.success(f"{len(filtrados)} trecho(s) encontrado(s)")
                    st.markdown("\n\n---\n\n".join(filtrados))
                else:
                    st.warning(f'Nenhum resultado para "{busca}"')
            else:
                st.markdown(conteudo)
        else:
            st.error(f"Documento não encontrado: {caminho}")
