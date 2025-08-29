# Makefile para Análise de Impacto CNPJ Alfanumérico
# Versão: 1.0
# Data: 2025-01-27

.PHONY: help install setup analyze report clean

# Variáveis
PYTHON = venv/bin/python3
PIP = venv/bin/pip
PROJECT_NAME = cnpj-alfanumerico-analyzer
ANALYZER_SCRIPT = cnpj_analyzer_modular.py
REPORT_TEMPLATE = templates/report_template.md

# Cores para output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(BLUE)=== $(PROJECT_NAME) - Análise de Impacto CNPJ Alfanumérico ===$(NC)"
	@echo ""
	@echo "$(YELLOW)Comandos disponíveis:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Exemplos de uso:$(NC)"
	@echo "  make setup                    # Instala dependências e configura ambiente"
	@echo "  make analyze PROJECT=./meu-projeto  # Analisa um projeto específico"
	@echo "  make analyze-all              # Analisa todos os projetos configurados"
	@echo "  make report                   # Gera relatório consolidado"

install: ## Instala dependências Python
	@echo "$(BLUE)Instalando dependências...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependências instaladas com sucesso$(NC)"

setup: ## Configura ambiente virtual e instala dependências
	@echo "$(BLUE)Configurando ambiente virtual...$(NC)"
	python3 -m venv venv
	@echo "$(BLUE)Ativando ambiente virtual...$(NC)"
	. venv/bin/activate
	@echo "$(BLUE)Instalando dependências...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(BLUE)Configurando permissões...$(NC)"
	chmod +x src/cnpj_analyzer.py
	chmod +x cnpj_analyzer_modular.py
	@if [ -d "scripts" ]; then chmod +x scripts/*.sh; fi
	@if [ -f "*.sh" ]; then chmod +x *.sh; fi
	@echo "$(BLUE)Criando diretórios...$(NC)"
	@mkdir -p src templates reports logs
	@mkdir -p config/projects
	@echo "$(GREEN)✓ Ambiente configurado com sucesso!$(NC)"
	@echo "$(YELLOW)Dica: Execute 'source venv/bin/activate' para ativar o ambiente$(NC)"

analyze: ## Analisa um projeto específico (use PROJECT=./caminho/do/projeto)
	@if [ -z "$(PROJECT)" ]; then \
		echo "$(RED)Erro: Especifique o projeto com PROJECT=./caminho/do/projeto$(NC)"; \
		echo "Exemplo: make analyze PROJECT=./meu-projeto"; \
		exit 1; \
	fi
	@echo "$(BLUE)Analisando projeto: $(PROJECT)$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) analyze --project-path $(PROJECT) --output reports/

analyze-all: ## Analisa todos os projetos configurados
	@echo "$(BLUE)Analisando todos os projetos configurados...$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) analyze-all --output reports/

analyze-folder: ## Analisa todos os projetos em uma pasta (use FOLDER=./caminho/da/pasta)
	@if [ -z "$(FOLDER)" ]; then \
		echo "$(RED)Erro: Especifique a pasta com FOLDER=./caminho/da/pasta$(NC)"; \
		echo "Exemplo: make analyze-folder FOLDER=./projetos"; \
		exit 1; \
	fi
	@echo "$(BLUE)Analisando projetos em: $(FOLDER)$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) analyze-all --projects-folder $(FOLDER) --output reports/

discover-projects: ## Descobre projetos em uma pasta (use FOLDER=./caminho/da/pasta)
	@if [ -z "$(FOLDER)" ]; then \
		echo "$(RED)Erro: Especifique a pasta com FOLDER=./caminho/da/pasta$(NC)"; \
		echo "Exemplo: make discover-projects FOLDER=./projetos"; \
		exit 1; \
	fi
	@echo "$(BLUE)Descobrindo projetos em: $(FOLDER)$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) discover-projects --projects-folder $(FOLDER)

report: ## Gera relatório consolidado
	@echo "$(BLUE)Gerando relatório consolidado...$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) report --input reports/ --output reports/consolidated_report.md

quick-scan: ## Escaneamento rápido de um projeto
	@if [ -z "$(PROJECT)" ]; then \
		echo "$(RED)Erro: Especifique o projeto com PROJECT=./caminho/do/projeto$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Escaneamento rápido: $(PROJECT)$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) quick-scan --project-path $(PROJECT)

validate-cnpj: ## Valida estrutura de CNPJ em um projeto
	@if [ -z "$(PROJECT)" ]; then \
		echo "$(RED)Erro: Especifique o projeto com PROJECT=./caminho/do/projeto$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Validando CNPJ em: $(PROJECT)$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) validate-cnpj --project-path $(PROJECT)

find-migrations: ## Encontra migrações relacionadas a CNPJ
	@if [ -z "$(PROJECT)" ]; then \
		echo "$(RED)Erro: Especifique o projeto com PROJECT=./caminho/do/projeto$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Buscando migrações em: $(PROJECT)$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) find-migrations --project-path $(PROJECT)

find-validations: ## Encontra validações de CNPJ
	@if [ -z "$(PROJECT)" ]; then \
		echo "$(RED)Erro: Especifique o projeto com PROJECT=./caminho/do/projeto$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Buscando validações em: $(PROJECT)$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) find-validations --project-path $(PROJECT)

find-masks: ## Encontra máscaras de CNPJ no frontend
	@if [ -z "$(PROJECT)" ]; then \
		echo "$(RED)Erro: Especifique o projeto com PROJECT=./caminho/do/projeto$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Buscando máscaras em: $(PROJECT)$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) find-masks --project-path $(PROJECT)

test: ## Executa testes
	@echo "$(BLUE)Executando testes...$(NC)"
	$(PYTHON) -m pytest tests/ -v

clean: ## Limpa arquivos temporários e relatórios
	@echo "$(BLUE)Limpando arquivos temporários...$(NC)"
	rm -rf reports/*.md
	rm -rf logs/*.log
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	@echo "$(GREEN)✓ Limpeza concluída$(NC)"

clean-all: clean ## Limpa tudo incluindo dependências
	@echo "$(BLUE)Removendo dependências...$(NC)"
	$(PIP) uninstall -r requirements.txt -y || true
	@echo "$(GREEN)✓ Limpeza completa concluída$(NC)"

# Comandos de desenvolvimento
dev-setup: setup ## Configuração para desenvolvimento
	@echo "$(BLUE)Configurando ambiente de desenvolvimento...$(NC)"
	$(PIP) install -r requirements-dev.txt || true
	@echo "$(GREEN)✓ Ambiente de desenvolvimento configurado$(NC)"

lint: ## Executa linting do código
	@echo "$(BLUE)Executando linting...$(NC)"
	$(PYTHON) -m flake8 src/ --max-line-length=120
	@echo "$(GREEN)✓ Linting concluído$(NC)"

format: ## Formata o código
	@echo "$(BLUE)Formatando código...$(NC)"
	$(PYTHON) -m black src/ --line-length=120
	@echo "$(GREEN)✓ Formatação concluída$(NC)"

# Comandos de documentação
docs: ## Gera documentação
	@echo "$(BLUE)Gerando documentação...$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) generate-docs --output docs/
	@echo "$(GREEN)✓ Documentação gerada$(NC)"

# Comandos de backup
backup: ## Cria backup dos relatórios
	@echo "$(BLUE)Criando backup...$(NC)"
	tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz reports/ config/
	@echo "$(GREEN)✓ Backup criado$(NC)"

# Comandos de monitoramento
monitor: ## Monitora mudanças em projetos
	@echo "$(BLUE)Iniciando monitoramento...$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) monitor --config config/projects.yaml

# Comandos de exportação
export-json: ## Exporta resultados em JSON
	@echo "$(BLUE)Exportando resultados em JSON...$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) export --format json --input reports/ --output exports/

export-csv: ## Exporta resultados em CSV
	@echo "$(BLUE)Exportando resultados em CSV...$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) export --format csv --input reports/ --output exports/

# Comandos de configuração
init-config: ## Inicializa arquivo de configuração
	@echo "$(BLUE)Criando arquivo de configuração...$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) init-config --output config/projects.yaml
	@echo "$(GREEN)✓ Configuração inicializada$(NC)"

validate-config: ## Valida arquivo de configuração
	@echo "$(BLUE)Validando configuração...$(NC)"
	$(PYTHON) $(ANALYZER_SCRIPT) validate-config --config config/projects.yaml
	@echo "$(GREEN)✓ Configuração válida$(NC)"
