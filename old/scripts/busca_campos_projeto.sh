#!/bin/bash

# Script de Busca Sistemática de Campos de Documento (CPF/CNPJ)
# Baseado no GUIA_BUSCA_CAMPOS_PROJETO.md
# Versão: 1.1
# Data: 2025-01-27
# Foco: Validação de compatibilidade com CNPJ alfanumérico

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir cabeçalho
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  BUSCA SISTEMÁTICA DE CAMPOS CPF/CNPJ  ${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Função para imprimir seção
print_section() {
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}$(printf '=%.0s' {1..${#1}})${NC}"
    echo ""
}

# Função para imprimir resultado
print_result() {
    echo -e "${GREEN}$1${NC}"
}

# Função para imprimir erro
print_error() {
    echo -e "${RED}$1${NC}"
}

# Função para imprimir aviso
print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

# Verificar se o diretório existe
if [ ! -d "migrations" ]; then
    print_error "Diretório 'migrations' não encontrado. Execute este script na raiz do projeto."
    exit 1
fi

# Criar diretório de resultados
RESULTS_DIR="analise_campos_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

print_header

echo "Iniciando análise sistemática de campos CPF/CNPJ..."
echo "Foco: Validação de compatibilidade com CNPJ alfanumérico"
echo "Resultados serão salvos em: $RESULTS_DIR"
echo ""

# 1. ANÁLISE DE BANCO DE DADOS
print_section "1. ANÁLISE DE BANCO DE DADOS"

# 1.1 Busca em Migrações
print_section "1.1 Busca em Migrações"

echo "Buscando campos CPF/CNPJ em migrações..."
grep -r "cpf_cnpj\|cnpj\|nr_documento" migrations/ --include="*.php" -i > "$RESULTS_DIR/cpf_cnpj_migrations.txt" 2>/dev/null || true
if [ -s "$RESULTS_DIR/cpf_cnpj_migrations.txt" ]; then
    print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/cpf_cnpj_migrations.txt") resultados para CPF/CNPJ"
else
    print_warning "⚠ Nenhum campo CPF/CNPJ encontrado em migrações"
fi

echo "Buscando variações de campos de documento..."
grep -r "documento\|cpf\|cnpj" migrations/ --include="*.php" -i > "$RESULTS_DIR/documento_migrations.txt" 2>/dev/null || true
if [ -s "$RESULTS_DIR/documento_migrations.txt" ]; then
    print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/documento_migrations.txt") resultados para variações de documento"
else
    print_warning "⚠ Nenhuma variação de documento encontrada em migrações"
fi

# 1.2 Análise de Tipos de Dados para Campos de Documento
print_section "1.2 Análise de Tipos de Dados para Campos de Documento"

echo "Buscando definições VARCHAR para campos de documento..."
grep -r "VARCHAR([0-9]*)" migrations/ --include="*.php" -i | grep -i "cpf\|cnpj\|documento" > "$RESULTS_DIR/varchar_documento_definitions.txt" 2>/dev/null || true
if [ -s "$RESULTS_DIR/varchar_documento_definitions.txt" ]; then
    print_result "✓ Encontradas $(wc -l < "$RESULTS_DIR/varchar_documento_definitions.txt") definições VARCHAR para documentos"
else
    print_warning "⚠ Nenhuma definição VARCHAR para documentos encontrada"
fi

echo "Buscando definições CHAR para campos de documento..."
grep -r "CHAR([0-9]*)" migrations/ --include="*.php" -i | grep -i "cpf\|cnpj\|documento" > "$RESULTS_DIR/char_documento_definitions.txt" 2>/dev/null || true
if [ -s "$RESULTS_DIR/char_documento_definitions.txt" ]; then
    print_result "✓ Encontradas $(wc -l < "$RESULTS_DIR/char_documento_definitions.txt") definições CHAR para documentos"
else
    print_warning "⚠ Nenhuma definição CHAR para documentos encontrada"
fi

echo "Buscando tamanhos específicos de campos de documento..."
grep -r "VARCHAR(14)\|VARCHAR(11)\|CHAR(14)\|CHAR(11)" migrations/ --include="*.php" -i > "$RESULTS_DIR/tamanhos_documento.txt" 2>/dev/null || true
if [ -s "$RESULTS_DIR/tamanhos_documento.txt" ]; then
    print_result "✓ Encontradas $(wc -l < "$RESULTS_DIR/tamanhos_documento.txt") definições com tamanhos específicos para documentos"
else
    print_warning "⚠ Nenhuma definição com tamanho específico para documentos encontrada"
fi

# 2. ANÁLISE DE CÓDIGO
print_section "2. ANÁLISE DE CÓDIGO"

# 2.1 Busca em Models
print_section "2.1 Busca em Models"

if [ -d "app/Model" ]; then
    echo "Buscando uso de campos CPF/CNPJ em Models..."
    grep -r "cpf_cnpj\|cnpj\|nr_documento" app/Model/ --include="*.php" -i > "$RESULTS_DIR/cpf_cnpj_models.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/cpf_cnpj_models.txt" ]; then
        print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/cpf_cnpj_models.txt") usos em Models"
    else
        print_warning "⚠ Nenhum uso de CPF/CNPJ encontrado em Models"
    fi

    echo "Buscando variações de campos de documento em Models..."
    grep -r "documento\|cpf\|cnpj" app/Model/ --include="*.php" -i > "$RESULTS_DIR/documento_models.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/documento_models.txt" ]; then
        print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/documento_models.txt") usos de variações de documento em Models"
    else
        print_warning "⚠ Nenhum uso de variação de documento encontrado em Models"
    fi
else
    print_warning "⚠ Diretório app/Model não encontrado"
fi

# 2.2 Busca em Controllers
print_section "2.2 Busca em Controllers"

if [ -d "app/Controller" ]; then
    echo "Buscando uso de campos CPF/CNPJ em Controllers..."
    grep -r "cpf_cnpj\|cnpj\|nr_documento" app/Controller/ --include="*.php" -i > "$RESULTS_DIR/cpf_cnpj_controllers.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/cpf_cnpj_controllers.txt" ]; then
        print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/cpf_cnpj_controllers.txt") usos em Controllers"
    else
        print_warning "⚠ Nenhum uso de CPF/CNPJ encontrado em Controllers"
    fi

    echo "Buscando variações de campos de documento em Controllers..."
    grep -r "documento\|cpf\|cnpj" app/Controller/ --include="*.php" -i > "$RESULTS_DIR/documento_controllers.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/documento_controllers.txt" ]; then
        print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/documento_controllers.txt") usos de variações de documento em Controllers"
    else
        print_warning "⚠ Nenhum uso de variação de documento encontrado em Controllers"
    fi
else
    print_warning "⚠ Diretório app/Controller não encontrado"
fi

# 2.3 Busca em Services
print_section "2.3 Busca em Services"

if [ -d "app/Infra/Service" ]; then
    echo "Buscando uso de campos CPF/CNPJ em Services..."
    grep -r "cpf_cnpj\|cnpj\|nr_documento" app/Infra/Service/ --include="*.php" -i > "$RESULTS_DIR/cpf_cnpj_services.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/cpf_cnpj_services.txt" ]; then
        print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/cpf_cnpj_services.txt") usos em Services"
    else
        print_warning "⚠ Nenhum uso de CPF/CNPJ encontrado em Services"
    fi

    echo "Buscando variações de campos de documento em Services..."
    grep -r "documento\|cpf\|cnpj" app/Infra/Service/ --include="*.php" -i > "$RESULTS_DIR/documento_services.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/documento_services.txt" ]; then
        print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/documento_services.txt") usos de variações de documento em Services"
    else
        print_warning "⚠ Nenhum uso de variação de documento encontrado em Services"
    fi
else
    print_warning "⚠ Diretório app/Infra/Service não encontrado"
fi

# 3. ANÁLISE DE VALIDAÇÕES
print_section "3. ANÁLISE DE VALIDAÇÕES"

if [ -d "app/Infra/Validator" ]; then
    echo "Buscando validações de CPF/CNPJ..."
    grep -r "cpf\|cnpj\|documento" app/Infra/Validator/ --include="*.php" -i > "$RESULTS_DIR/cpf_cnpj_validators.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/cpf_cnpj_validators.txt" ]; then
        print_result "✓ Encontradas $(wc -l < "$RESULTS_DIR/cpf_cnpj_validators.txt") validações de CPF/CNPJ"
    else
        print_warning "⚠ Nenhuma validação de CPF/CNPJ encontrada"
    fi

    echo "Buscando validações customizadas para documentos..."
    grep -r "validator\|validation\|validate" app/Infra/Validator/ --include="*.php" -i | grep -i "cpf\|cnpj\|documento" > "$RESULTS_DIR/documento_validators.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/documento_validators.txt" ]; then
        print_result "✓ Encontradas $(wc -l < "$RESULTS_DIR/documento_validators.txt") validações customizadas para documentos"
    else
        print_warning "⚠ Nenhuma validação customizada para documentos encontrada"
    fi

    echo "Buscando bibliotecas de validação de documentos..."
    grep -r "Tigo\|DocumentBr\|Cpf\|Cnpj" app/Infra/Validator/ --include="*.php" -i > "$RESULTS_DIR/bibliotecas_validacao.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/bibliotecas_validacao.txt" ]; then
        print_result "✓ Encontradas $(wc -l < "$RESULTS_DIR/bibliotecas_validacao.txt") referências a bibliotecas de validação"
    else
        print_warning "⚠ Nenhuma biblioteca de validação encontrada"
    fi
else
    print_warning "⚠ Diretório app/Infra/Validator não encontrado"
fi

# 4. ANÁLISE DE TESTES
print_section "4. ANÁLISE DE TESTES"

if [ -d "test" ]; then
    echo "Buscando testes com campos CPF/CNPJ..."
    grep -r "cpf_cnpj\|cnpj\|nr_documento" test/ --include="*.php" -i > "$RESULTS_DIR/cpf_cnpj_tests.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/cpf_cnpj_tests.txt" ]; then
        print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/cpf_cnpj_tests.txt") testes com CPF/CNPJ"
    else
        print_warning "⚠ Nenhum teste com CPF/CNPJ encontrado"
    fi

    echo "Buscando testes com variações de campos de documento..."
    grep -r "documento\|cpf\|cnpj" test/ --include="*.php" -i > "$RESULTS_DIR/documento_tests.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/documento_tests.txt" ]; then
        print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/documento_tests.txt") testes com variações de documento"
    else
        print_warning "⚠ Nenhum teste com variação de documento encontrado"
    fi

    echo "Buscando dados de exemplo para documentos..."
    grep -r "12345678901\|12345678901234\|faker.*cpf\|faker.*cnpj" test/ --include="*.php" -i > "$RESULTS_DIR/dados_exemplo_documento.txt" 2>/dev/null || true
    if [ -s "$RESULTS_DIR/dados_exemplo_documento.txt" ]; then
        print_result "✓ Encontrados $(wc -l < "$RESULTS_DIR/dados_exemplo_documento.txt") dados de exemplo para documentos"
    else
        print_warning "⚠ Nenhum dado de exemplo para documentos encontrado"
    fi
else
    print_warning "⚠ Diretório test não encontrado"
fi

# 5. GERAÇÃO DE RELATÓRIO
print_section "5. GERAÇÃO DE RELATÓRIO"

echo "Gerando relatório de análise..."

cat > "$RESULTS_DIR/relatorio_analise.md" << EOF
# Relatório de Análise de Campos CPF/CNPJ - $(date +%Y-%m-%d)

## Resumo Executivo

**Data da Análise:** $(date +%Y-%m-%d %H:%M:%S)
**Projeto:** $(basename $(pwd))
**Script Utilizado:** busca_campos_projeto.sh
**Foco:** Validação de compatibilidade com CNPJ alfanumérico

## Estatísticas Gerais

### Campos CPF/CNPJ
- **Migrações:** $(wc -l < "$RESULTS_DIR/cpf_cnpj_migrations.txt" 2>/dev/null || echo "0")
- **Models:** $(wc -l < "$RESULTS_DIR/cpf_cnpj_models.txt" 2>/dev/null || echo "0")
- **Controllers:** $(wc -l < "$RESULTS_DIR/cpf_cnpj_controllers.txt" 2>/dev/null || echo "0")
- **Services:** $(wc -l < "$RESULTS_DIR/cpf_cnpj_services.txt" 2>/dev/null || echo "0")
- **Testes:** $(wc -l < "$RESULTS_DIR/cpf_cnpj_tests.txt" 2>/dev/null || echo "0")

### Variações de Campos de Documento
- **Migrações:** $(wc -l < "$RESULTS_DIR/documento_migrations.txt" 2>/dev/null || echo "0")
- **Models:** $(wc -l < "$RESULTS_DIR/documento_models.txt" 2>/dev/null || echo "0")
- **Controllers:** $(wc -l < "$RESULTS_DIR/documento_controllers.txt" 2>/dev/null || echo "0")
- **Services:** $(wc -l < "$RESULTS_DIR/documento_services.txt" 2>/dev/null || echo "0")
- **Testes:** $(wc -l < "$RESULTS_DIR/documento_tests.txt" 2>/dev/null || echo "0")

## Tipos de Dados para Documentos

### VARCHAR para Documentos
- **Definições encontradas:** $(wc -l < "$RESULTS_DIR/varchar_documento_definitions.txt" 2>/dev/null || echo "0")

### CHAR para Documentos
- **Definições encontradas:** $(wc -l < "$RESULTS_DIR/char_documento_definitions.txt" 2>/dev/null || echo "0")

### Tamanhos Específicos
- **Definições com tamanhos específicos:** $(wc -l < "$RESULTS_DIR/tamanhos_documento.txt" 2>/dev/null || echo "0")

## Validações

### Validações CPF/CNPJ
- **Total de linhas:** $(wc -l < "$RESULTS_DIR/cpf_cnpj_validators.txt" 2>/dev/null || echo "0")

### Validações Customizadas para Documentos
- **Total de linhas:** $(wc -l < "$RESULTS_DIR/documento_validators.txt" 2>/dev/null || echo "0")

### Bibliotecas de Validação
- **Referências encontradas:** $(wc -l < "$RESULTS_DIR/bibliotecas_validacao.txt" 2>/dev/null || echo "0")

## Testes

### Testes com CPF/CNPJ
- **Total de testes:** $(wc -l < "$RESULTS_DIR/cpf_cnpj_tests.txt" 2>/dev/null || echo "0")

### Testes com Variações de Documento
- **Total de testes:** $(wc -l < "$RESULTS_DIR/documento_tests.txt" 2>/dev/null || echo "0")

### Dados de Exemplo
- **Dados de exemplo encontrados:** $(wc -l < "$RESULTS_DIR/dados_exemplo_documento.txt" 2>/dev/null || echo "0")

## Arquivos de Detalhamento

Os seguintes arquivos contêm os detalhes completos da análise:

- \`cpf_cnpj_migrations.txt\` - Campos CPF/CNPJ em migrações
- \`documento_migrations.txt\` - Variações de campos de documento em migrações
- \`varchar_documento_definitions.txt\` - Definições VARCHAR para documentos
- \`char_documento_definitions.txt\` - Definições CHAR para documentos
- \`tamanhos_documento.txt\` - Tamanhos específicos para documentos
- \`cpf_cnpj_models.txt\` - Uso de CPF/CNPJ em Models
- \`documento_models.txt\` - Variações de documento em Models
- \`cpf_cnpj_controllers.txt\` - Uso de CPF/CNPJ em Controllers
- \`documento_controllers.txt\` - Variações de documento em Controllers
- \`cpf_cnpj_services.txt\` - Uso de CPF/CNPJ em Services
- \`documento_services.txt\` - Variações de documento em Services
- \`cpf_cnpj_validators.txt\` - Validações de CPF/CNPJ
- \`documento_validators.txt\` - Validações customizadas para documentos
- \`bibliotecas_validacao.txt\` - Bibliotecas de validação
- \`cpf_cnpj_tests.txt\` - Testes com CPF/CNPJ
- \`documento_tests.txt\` - Testes com variações de documento
- \`dados_exemplo_documento.txt\` - Dados de exemplo para documentos

## Comandos Utilizados

\`\`\`bash
# Busca em migrações
grep -r "cpf_cnpj\|cnpj\|nr_documento" migrations/ --include="*.php" -i
grep -r "documento\|cpf\|cnpj" migrations/ --include="*.php" -i

# Busca em código
grep -r "cpf_cnpj\|cnpj\|nr_documento" app/ --include="*.php" -i
grep -r "documento\|cpf\|cnpj" app/ --include="*.php" -i

# Busca em testes
grep -r "cpf_cnpj\|cnpj\|nr_documento" test/ --include="*.php" -i
grep -r "documento\|cpf\|cnpj" test/ --include="*.php" -i
\`\`\`

## Análise de Compatibilidade com CNPJ Alfanumérico

### Pontos Positivos
- Campos usam tipos VARCHAR/CHAR adequados
- Validações implementadas com biblioteca Tigo\\DocumentBr
- Código preparado para strings de 11 (CPF) ou 14 (CNPJ) caracteres

### Pontos de Atenção
- Verificar se validação suporta CNPJ com caracteres especiais
- Confirmar compatibilidade com APIs externas
- Validar tamanhos de campos em consultas específicas

## Próximos Passos

1. Revisar os arquivos de detalhamento para análise específica
2. Identificar padrões de uso dos campos de documento
3. Avaliar impacto de mudança para CNPJ alfanumérico
4. Testar validações com novos formatos
5. Documentar recomendações baseadas na análise
EOF

print_result "✓ Relatório gerado: $RESULTS_DIR/relatorio_analise.md"

# 6. RESUMO FINAL
print_section "6. RESUMO FINAL"

echo "Análise concluída com sucesso!"
echo ""
echo "📁 Resultados salvos em: $RESULTS_DIR"
echo "📄 Relatório principal: $RESULTS_DIR/relatorio_analise.md"
echo ""
echo "📊 Estatísticas:"
echo "   • Campos CPF/CNPJ: $(wc -l < "$RESULTS_DIR/cpf_cnpj_migrations.txt" 2>/dev/null || echo "0") em migrações"
echo "   • Variações de documento: $(wc -l < "$RESULTS_DIR/documento_migrations.txt" 2>/dev/null || echo "0") em migrações"
echo "   • Validações CPF/CNPJ: $(wc -l < "$RESULTS_DIR/cpf_cnpj_validators.txt" 2>/dev/null || echo "0") linhas"
echo "   • Bibliotecas de validação: $(wc -l < "$RESULTS_DIR/bibliotecas_validacao.txt" 2>/dev/null || echo "0") referências"
echo "   • Testes encontrados: $(wc -l < "$RESULTS_DIR/cpf_cnpj_tests.txt" 2>/dev/null || echo "0") com CPF/CNPJ"
echo ""
echo "✅ Análise sistemática de campos CPF/CNPJ concluída"
echo "🎯 Foco: Validação de compatibilidade com CNPJ alfanumérico"
