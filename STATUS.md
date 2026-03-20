# Status do Projeto — Vértice IA

**Última atualização**: 2026-03-20

## Visão Geral

| Item | Status |
|---|---|
| Arquitetura definida | ✅ Concluído |
| README documentado | ✅ Concluído |
| Estrutura de pastas | ✅ Concluído |
| Dados fictícios criados | ✅ Concluído |
| Políticas detalhadas | ✅ Concluído |
| Banco de dados (SQLite) | ✅ Concluído |
| Pipeline RAG | ✅ Concluído |
| Guardrails | ✅ Concluído |
| Agentes (5 agentes) | ✅ Concluído |
| Observabilidade (LangFuse) | ✅ Concluído |
| Interface Streamlit (3 telas) | ✅ Concluído |
| Dataset de avaliação (30 perguntas) | ✅ Concluído |
| Métricas de avaliação RAG | ✅ Concluído |
| Testes automatizados | ✅ Concluído |
| Docker Compose | ✅ Concluído |
| Screenshots/GIFs no README | ⏳ Pendente |
| README_EN.md (versão inglês) | ⏳ Pendente |
| Testes de integração end-to-end | ⏳ Pendente |

## Detalhamento por Módulo

### Dados e Documentos
- [x] `base_estoque.csv` — 15 referências × tamanhos × 8 lojas (~150 registros)
- [x] `base_funcionarios.csv` — 50 funcionários representativos
- [x] `sobre_empresa.md` — Empresa detalhada (plantas, lojas, organograma, financeiro)
- [x] `manual_rh.md` — Jornada, benefícios, férias, código de conduta
- [x] `politica_devolucao.md` — Expandida com detalhes de reembolso por tipo de pagamento
- [x] `politica_envio.md` — Expandida com prazos regionais e embalagem
- [x] `politica_garantia.md` — Expandida com exemplos concretos de cobertura

### Pipeline RAG
- [x] Indexador com chunking por seções markdown
- [x] Recuperador híbrido (vetorial ChromaDB + BM25)
- [x] Reciprocal Rank Fusion para fusão de rankings
- [x] Reranqueador com cross-encoder (ms-marco-MiniLM)
- [x] Score de confiança com normalização sigmoid
- [x] Pipeline orquestrado com métricas de latência

### Agentes
- [x] Roteador (classificação via Claude + fallback por palavras-chave)
- [x] Agente Cliente (RAG + geração fundamentada)
- [x] Agente Estoque (tool calling com 3 ferramentas SQL)
- [x] Agente RH (RAG + geração fundamentada)
- [x] Agente BI (tool calling com 6 ferramentas de métricas)

### Guardrails
- [x] Detector de prompt injection (30+ padrões PT-BR e EN)
- [x] Validador de fundamentação (score, fontes, alucinação)
- [x] Filtro de PII (CPF, email, telefone, cartão, CEP, RG)

### Interface
- [x] Tela 1: Chat com agente (badge do agente, fontes, confiança, feedback)
- [x] Tela 2: Estoque (filtros, tabela, gráfico) + Políticas (busca textual)
- [x] Tela 3: Dashboard BI (KPIs, gráficos por agente/perfil, gauge de satisfação, estoque crítico)

### Avaliação
- [x] Dataset com 30 perguntas cobrindo todos os domínios
- [x] Métricas: fidelidade, relevância, correção, fundamentação
- [x] Avaliação de roteamento (precisão)
- [x] Script automatizado com output formatado (rich)

### Testes
- [x] `teste_guardrails.py` — 15 testes (injection, validação, PII)
- [x] `teste_roteador.py` — 8 testes (classificação por fallback)
- [x] `teste_estoque.py` — 9 testes (consultas SQL)
- [x] `teste_rag.py` — 7 testes (recuperação, fusão, reranqueamento)

## Próximos Passos

1. Rodar o sistema localmente e gerar screenshots/GIFs para o README
2. Criar README_EN.md (versão completa em inglês)
3. Testes end-to-end com API real
4. Refinar prompts dos agentes com base nos resultados da avaliação
5. Publicar no GitHub com tags e release notes
