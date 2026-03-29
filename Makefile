.PHONY: run indexar avaliar testes limpar instalar docker prod-init prod-ssl prod prod-parar prod-logs

# Instalar dependências
instalar:
	pip install -r requirements.txt

# Inicializar banco e indexar documentos
inicializar:
	python -m banco.inicializador
	python -m rag.indexador

# Indexar documentos no RAG
indexar:
	python -m rag.indexador

# Executar aplicação
run:
	streamlit run interface/app.py

# Rodar avaliação do RAG
avaliar:
	python -m avaliacao.avaliar_rag

# Rodar testes
testes:
	pytest testes/ -v

# Limpar banco e índices
limpar:
	rm -f banco/vertice.db
	rm -rf banco/chroma_db

# Docker local (dev)
docker:
	docker-compose up --build

docker-parar:
	docker-compose down

# ── Produção ──────────────────────────────────────────────────────────────────

# Passo 1: sobe Nginx sem SSL para permitir desafio ACME
prod-init:
	cp nginx/conf.d/vertice-init.conf nginx/conf.d/default.conf
	docker-compose -f docker-compose.prod.yml up -d vertice-ia nginx

# Passo 2: obtém certificado SSL via Let's Encrypt
prod-ssl:
	docker-compose -f docker-compose.prod.yml run --rm certbot
	cp nginx/conf.d/vertice.conf nginx/conf.d/default.conf
	docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Passo 3: sobe stack completa com SSL
prod:
	docker-compose -f docker-compose.prod.yml up -d --build

prod-parar:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f vertice-ia nginx
