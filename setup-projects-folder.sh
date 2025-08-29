#!/bin/bash

# Script para Configurar Pasta de Projetos - Analisador CNPJ Alfanumérico
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
echo -e "${BLUE}  CONFIGURAÇÃO DE PASTA DE PROJETOS   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar se o argumento foi fornecido
if [ -z "$1" ]; then
    echo -e "${RED}Erro: Especifique o caminho para a pasta de projetos${NC}"
    echo ""
    echo -e "${YELLOW}Uso:${NC}"
    echo "  ./setup-projects-folder.sh /caminho/para/projetos"
    echo ""
    echo -e "${YELLOW}Exemplos:${NC}"
    echo "  ./setup-projects-folder.sh /home/usuario/projetos"
    echo "  ./setup-projects-folder.sh ./projetos"
    echo "  ./setup-projects-folder.sh /var/www/projects"
    echo ""
    exit 1
fi

PROJECTS_FOLDER="$1"

# Verificar se a pasta existe
if [ ! -d "$PROJECTS_FOLDER" ]; then
    echo -e "${YELLOW}Aviso: A pasta '$PROJECTS_FOLDER' não existe.${NC}"
    read -p "Deseja criar esta pasta? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "$PROJECTS_FOLDER"
        echo -e "${GREEN}✓ Pasta criada: $PROJECTS_FOLDER${NC}"
    else
        echo -e "${RED}Operação cancelada.${NC}"
        exit 1
    fi
fi

# Configurar variável de ambiente
export PROJECTS_FOLDER="$PROJECTS_FOLDER"

echo -e "${GREEN}✓ Variável PROJECTS_FOLDER configurada: $PROJECTS_FOLDER${NC}"
echo ""

# Verificar se há projetos na pasta
echo -e "${BLUE}Verificando projetos na pasta...${NC}"
if [ -z "$(ls -A "$PROJECTS_FOLDER" 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠ A pasta está vazia. Adicione projetos para análise.${NC}"
else
    echo -e "${GREEN}✓ Projetos encontrados:${NC}"
    for project in "$PROJECTS_FOLDER"/*; do
        if [ -d "$project" ]; then
            project_name=$(basename "$project")
            echo "  📁 $project_name"
        fi
    done
fi

echo ""

# Mostrar comandos disponíveis
echo -e "${BLUE}Comandos disponíveis:${NC}"
echo ""
echo -e "${GREEN}1. Descobrir projetos:${NC}"
echo "   venv/bin/python src/cnpj_analyzer.py discover-projects"
echo "   make discover-projects FOLDER=$PROJECTS_FOLDER"
echo ""
echo -e "${GREEN}2. Analisar todos os projetos:${NC}"
echo "   venv/bin/python src/cnpj_analyzer.py analyze-all"
echo "   make analyze-folder FOLDER=$PROJECTS_FOLDER"
echo ""
echo -e "${GREEN}3. Escaneamento rápido:${NC}"
echo "   venv/bin/python src/cnpj_analyzer.py quick-scan /caminho/do/projeto"
echo "   make quick-scan PROJECT=/caminho/do/projeto"
echo ""

# Salvar configuração no arquivo .env se solicitado
read -p "Deseja salvar esta configuração no arquivo .env? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "PROJECTS_FOLDER=$PROJECTS_FOLDER" > .env
    echo -e "${GREEN}✓ Configuração salva em .env${NC}"
    echo ""
    echo -e "${YELLOW}Para carregar automaticamente, adicione ao seu ~/.bashrc:${NC}"
    echo "  source .env"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  CONFIGURAÇÃO CONCLUÍDA COM SUCESSO  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Próximo passo: Execute 'make discover-projects FOLDER=$PROJECTS_FOLDER'${NC}"

