#!/bin/bash

# Script de Demonstração - Analisador CNPJ Alfanumérico
# Versão: 1.0
# Data: 2025-01-27

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  DEMONSTRAÇÃO - ANALISADOR CNPJ      ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Configurando ambiente virtual...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo -e "${GREEN}✓ Ambiente virtual já configurado${NC}"
    source venv/bin/activate
fi

echo ""

# 1. Mostrar ajuda
echo -e "${BLUE}1. Mostrando ajuda da ferramenta:${NC}"
echo ""
venv/bin/python src/cnpj_analyzer.py --help
echo ""

# 2. Escaneamento rápido do projeto exemplo
echo -e "${BLUE}2. Escaneamento rápido do projeto exemplo:${NC}"
echo ""
venv/bin/python src/cnpj_analyzer.py quick-scan exemplo-projeto
echo ""

# 3. Análise completa
echo -e "${BLUE}3. Análise completa do projeto exemplo:${NC}"
echo ""
venv/bin/python src/cnpj_analyzer.py analyze exemplo-projeto --output reports/
echo ""

# 4. Buscar validações específicas
echo -e "${BLUE}4. Buscando validações de CNPJ:${NC}"
echo ""
venv/bin/python src/cnpj_analyzer.py find-validations exemplo-projeto
echo ""

# 5. Buscar máscaras frontend
echo -e "${BLUE}5. Buscando máscaras frontend:${NC}"
echo ""
venv/bin/python src/cnpj_analyzer.py find-masks exemplo-projeto
echo ""

# 6. Mostrar relatórios gerados
echo -e "${BLUE}6. Relatórios gerados:${NC}"
echo ""
ls -la reports/
echo ""

# 7. Mostrar conteúdo do relatório Markdown
echo -e "${BLUE}7. Resumo do relatório gerado:${NC}"
echo ""
head -20 reports/exemplo-projeto_analysis.md
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Próximos passos:${NC}"
echo "1. Configure seus projetos em config/projects.yaml"
echo "2. Execute: make analyze-all"
echo "3. Gere relatório consolidado: make report"
echo "4. Exporte resultados: make export-json"
echo ""
echo -e "${BLUE}Para mais informações, consulte o README.md${NC}"
