"""
Tela 3 — Dashboard BI para Gestores.
Métricas de atendimento, performance e estoque.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ferramentas.consulta_metricas import (
    resumo_atendimentos, atendimentos_por_agente,
    atendimentos_por_perfil, perguntas_frequentes
)
from ferramentas.consulta_estoque import obter_estoque_critico, resumo_estoque_por_loja


def renderizar():
    """Renderiza o dashboard BI."""
    st.markdown('<p class="main-header">📊 Dashboard BI</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Métricas de atendimento e performance do sistema</p>',
        unsafe_allow_html=True,
    )

    # Filtro de período
    dias = st.selectbox(
        "Período",
        [7, 15, 30, 60, 90],
        index=2,
        format_func=lambda x: f"Últimos {x} dias",
    )

    st.divider()

    # ========================================
    # KPIs Principais
    # ========================================
    resumo = resumo_atendimentos(dias=dias)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Atendimentos",
            resumo.get("total_atendimentos", 0),
        )
    with col2:
        taxa = resumo.get("taxa_resolucao", 0)
        st.metric(
            "Taxa de Resolução",
            f"{taxa}%",
            delta="autonomo" if taxa > 80 else None,
        )
    with col3:
        st.metric(
            "Encaminhados p/ Humano",
            resumo.get("encaminhados_humano", 0),
        )
    with col4:
        duracao = resumo.get("duracao_media_segundos", 0)
        st.metric(
            "Tempo Médio (s)",
            f"{duracao:.0f}s",
        )
    with col5:
        score = resumo.get("score_confianca_medio", 0)
        st.metric(
            "Score Médio",
            f"{score:.2f}",
        )

    st.divider()

    # ========================================
    # Gráficos
    # ========================================
    col_a, col_b = st.columns(2)

    # Atendimentos por agente
    with col_a:
        st.subheader("Atendimentos por Agente")
        dados_agente = atendimentos_por_agente(dias=dias)
        if dados_agente:
            df_agente = pd.DataFrame(dados_agente)
            fig = px.pie(
                df_agente,
                values="total",
                names="agente",
                color="agente",
                color_discrete_map={
                    "cliente": "#6C5CE7",
                    "estoque": "#0984E3",
                    "rh": "#00B894",
                    "bi": "#E17055",
                },
                hole=0.4,
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de atendimentos no período.")

    # Atendimentos por perfil
    with col_b:
        st.subheader("Atendimentos por Perfil")
        dados_perfil = atendimentos_por_perfil(dias=dias)
        if dados_perfil:
            df_perfil = pd.DataFrame(dados_perfil)
            fig = px.bar(
                df_perfil,
                x="perfil",
                y="total",
                color="perfil",
                color_discrete_map={
                    "cliente": "#6C5CE7",
                    "vendedor": "#0984E3",
                    "gerente": "#00B894",
                    "rh": "#E17055",
                    "sac": "#FDCB6E",
                },
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de atendimentos no período.")

    st.divider()

    # ========================================
    # Feedbacks e Perguntas Frequentes
    # ========================================
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Feedbacks")
        positivos = resumo.get("feedbacks_positivos", 0)
        negativos = resumo.get("feedbacks_negativos", 0)
        total_fb = positivos + negativos

        if total_fb > 0:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=positivos / total_fb * 100,
                title={"text": "Satisfação (%)"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#00B894"},
                    "steps": [
                        {"range": [0, 50], "color": "#FFE4E4"},
                        {"range": [50, 75], "color": "#FFF3CD"},
                        {"range": [75, 100], "color": "#D4EDDA"},
                    ],
                },
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem feedbacks registrados no período.")

    with col_d:
        st.subheader("Perguntas Recentes")
        perguntas = perguntas_frequentes(dias=dias, top_k=5)
        if perguntas:
            for i, p in enumerate(perguntas, 1):
                st.markdown(f"**{i}.** {p['mensagem']}")
                if p.get("agente"):
                    st.caption(f"Agente: {p['agente']}")
        else:
            st.info("Sem perguntas registradas no período.")

    st.divider()

    # ========================================
    # Estoque Crítico
    # ========================================
    st.subheader("⚠️ Estoque Crítico")
    criticos = obter_estoque_critico()
    if criticos:
        df_crit = pd.DataFrame(criticos)
        st.warning(f"{len(df_crit)} itens com estoque abaixo do mínimo")

        # Top 10 mais críticos
        df_top = df_crit.head(10)
        fig = px.bar(
            df_top,
            x="nome",
            y="deficit",
            color="loja",
            title="Top 10 — Maior Déficit de Estoque",
            labels={"deficit": "Unidades abaixo do mínimo", "nome": "Produto"},
        )
        fig.update_layout(xaxis_tickangle=-45, height=350)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Ver todos os itens críticos"):
            st.dataframe(df_crit, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Nenhum item com estoque crítico!")

    # Resumo por loja
    st.subheader("Resumo de Estoque por Loja")
    resumo_lojas = resumo_estoque_por_loja()
    if resumo_lojas:
        df_lojas = pd.DataFrame(resumo_lojas)
        fig = px.bar(
            df_lojas,
            x="loja",
            y="valor_total",
            title="Valor em Estoque por Loja (R$)",
            color="valor_total",
            color_continuous_scale="Blues",
        )
        fig.update_layout(xaxis_tickangle=-45, height=350)
        st.plotly_chart(fig, use_container_width=True)
