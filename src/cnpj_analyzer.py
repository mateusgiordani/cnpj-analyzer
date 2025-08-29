#!/usr/bin/env python3
"""
Analisador de Impacto CNPJ Alfanumérico
Versão: 1.0
Data: 2025-01-27
Objetivo: Identificar impactos da mudança do CNPJ de numérico para alfanumérico em projetos
"""

import os
import re
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from jinja2 import Template

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cnpj_analyzer.log'),
        logging.StreamHandler()
    ]
)

console = Console()
app = typer.Typer()

class ProjectType(Enum):
    """Tipos de projeto suportados"""
    PHP_LARAVEL = "php_laravel"
    PHP_SYMFONY = "php_symfony"
    NODE_NEST = "node_nest"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    PYTHON_DJANGO = "python_django"
    PYTHON_FLASK = "python_flask"
    JAVA_SPRING = "java_spring"
    DOTNET = "dotnet"

class ImpactLevel(Enum):
    """Níveis de impacto"""
    LOW = "baixo"
    MEDIUM = "medio"
    HIGH = "alto"
    CRITICAL = "critico"

class Status(Enum):
    """Status de compatibilidade"""
    COMPATIBLE = "compativel"
    ATTENTION = "atencao"
    INCOMPATIBLE = "incompativel"
    NEEDS_ANALYSIS = "precisa_analise"

@dataclass
class CNPJField:
    """Representa um campo CNPJ encontrado"""
    file_path: str
    line_number: int
    field_name: str
    field_type: str
    field_size: Optional[int]
    context: str
    project_type: ProjectType
    impact_level: ImpactLevel
    status: Status
    action_needed: str
    estimated_effort: str

@dataclass
class ProjectAnalysis:
    """Resultado da análise de um projeto"""
    project_name: str
    project_path: str
    project_type: ProjectType
    total_files_scanned: int
    cnpj_fields_found: List[CNPJField]
    database_tables: List[Dict]
    migrations: List[Dict]
    validations: List[Dict]
    frontend_masks: List[Dict]
    overall_impact: ImpactLevel
    recommendations: List[str]
    analysis_date: datetime

class CNPJAnalyzer:
    """Analisador principal para identificar impactos do CNPJ alfanumérico"""
    
    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger(__name__)
        
        # Padrões de busca para CNPJ
        self.cnpj_patterns = {
            'field_names': [
                r'cnpj',
                r'cpf_cnpj',
                r'nr_documento',
                r'documento',
                r'numero_documento',
                r'cnpj_cpf',
                r'documento_fiscal'
            ],
            'validation_patterns': [
                r'cnpj.*validat',
                r'validat.*cnpj',
                r'cpf.*cnpj.*validat',
                r'documento.*validat'
            ],
            'mask_patterns': [
                r'cnpj.*mask',
                r'mask.*cnpj',
                r'format.*cnpj',
                r'cnpj.*format'
            ],
            'database_patterns': [
                r'VARCHAR\s*\(\s*(\d+)\s*\)',
                r'CHAR\s*\(\s*(\d+)\s*\)',
                r'TEXT',
                r'BIGINT',
                r'INT'
            ]
        }
        
        # Extensões de arquivo por tipo de projeto
        self.file_extensions = {
            ProjectType.PHP_LARAVEL: ['.php', '.sql'],
            ProjectType.PHP_SYMFONY: ['.php', '.sql', '.yml', '.yaml'],
            ProjectType.NODE_NEST: ['.ts', '.js', '.json'],
            ProjectType.REACT: ['.tsx', '.ts', '.jsx', '.js'],
            ProjectType.VUE: ['.vue', '.ts', '.js'],
            ProjectType.ANGULAR: ['.ts', '.js', '.html'],
            ProjectType.PYTHON_DJANGO: ['.py', '.sql'],
            ProjectType.PYTHON_FLASK: ['.py', '.sql'],
            ProjectType.JAVA_SPRING: ['.java', '.xml', '.sql'],
            ProjectType.DOTNET: ['.cs', '.sql', '.xml']
        }

    def get_projects_folder(self) -> Optional[Path]:
        """Obtém a pasta de projetos da variável de ambiente"""
        projects_folder = os.getenv('PROJECTS_FOLDER')
        if projects_folder:
            path = Path(projects_folder)
            if path.exists() and path.is_dir():
                return path
            else:
                self.logger.warning(f"PROJECTS_FOLDER não é um diretório válido: {projects_folder}")
        return None

    def discover_projects(self, projects_folder: Path) -> List[Dict]:
        """Descobre projetos automaticamente na pasta especificada"""
        projects = []
        
        self.console.print(f"[blue]Descobrindo projetos em: {projects_folder}[/blue]")
        
        for item in projects_folder.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                project_type = self.detect_project_type(item)
                if project_type:
                    projects.append({
                        'name': item.name,
                        'path': str(item),
                        'type': project_type.value,
                        'priority': 'medium',
                        'description': f'Projeto descoberto automaticamente: {item.name}',
                        'enabled': True
                    })
                    self.console.print(f"  [green]✓[/green] {item.name} ({project_type.value})")
                else:
                    self.console.print(f"  [yellow]⚠[/yellow] {item.name} (tipo não detectado)")
        
        return projects

    def detect_project_type(self, project_path: Path) -> ProjectType:
        """Detecta o tipo de projeto baseado na estrutura de arquivos"""
        project_path = Path(project_path)
        
        # Verificar arquivos específicos de cada framework
        if (project_path / 'composer.json').exists():
            return ProjectType.PHP_LARAVEL
        elif (project_path / 'package.json').exists():
            try:
                with open(project_path / 'package.json') as f:
                    package_data = json.load(f)
                    dependencies = package_data.get('dependencies', {})
                    dev_dependencies = package_data.get('devDependencies', {})
                    all_deps = {**dependencies, **dev_dependencies}
                    
                    # Verificar se alguma dependência contém '@nestjs'
                    if any('@nestjs' in dep for dep in all_deps.keys()):
                        return ProjectType.NODE_NEST
                    elif any('react' in dep for dep in all_deps.keys()):
                        return ProjectType.REACT
                    elif any('vue' in dep for dep in all_deps.keys()):
                        return ProjectType.VUE
                    elif any('@angular' in dep for dep in all_deps.keys()):
                        return ProjectType.ANGULAR
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        elif (project_path / 'requirements.txt').exists():
            return ProjectType.PYTHON_DJANGO
        elif (project_path / 'pom.xml').exists():
            return ProjectType.JAVA_SPRING
        elif list(project_path.glob('*.csproj')):
            return ProjectType.DOTNET
            
        return None

    def scan_database_files(self, project_path: Path, project_type: ProjectType) -> List[Dict]:
        """Escaneia arquivos de banco de dados"""
        database_files = []
        
        # Buscar arquivos de migração e SQL
        sql_patterns = ['*.sql', 'migrations/*.php', 'migrations/*.py', 'db/migrations/*']
        
        for pattern in sql_patterns:
            for file_path in project_path.rglob(pattern):
                if file_path.is_file():
                    database_files.append({
                        'file_path': str(file_path),
                        'content': file_path.read_text(encoding='utf-8', errors='ignore')
                    })
        
        return database_files

    def scan_code_files(self, project_path: Path, project_type: ProjectType) -> List[Dict]:
        """Escaneia arquivos de código"""
        code_files = []
        extensions = self.file_extensions.get(project_type, ['.php', '.ts', '.js', '.py'])
        
        for ext in extensions:
            for file_path in project_path.rglob(f'*{ext}'):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        code_files.append({
                            'file_path': str(file_path),
                            'content': content,
                            'extension': ext
                        })
                    except Exception as e:
                        self.logger.warning(f"Erro ao ler arquivo {file_path}: {e}")
        
        return code_files

    def _should_skip_file(self, file_path: Path) -> bool:
        """Verifica se o arquivo deve ser ignorado"""
        skip_patterns = [
            'node_modules', 'vendor', '.git', '__pycache__', 
            '.venv', 'venv', 'dist', 'build', '.next', '.nuxt'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def find_cnpj_fields(self, files: List[Dict], project_type: ProjectType) -> List[CNPJField]:
        """Encontra campos relacionados a CNPJ nos arquivos"""
        cnpj_fields = []
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.cnpj_patterns['field_names']:
                    if re.search(pattern, line, re.IGNORECASE):
                        field = self._analyze_cnpj_field(
                            file_path, line_num, line, project_type
                        )
                        if field:
                            cnpj_fields.append(field)
        
        return cnpj_fields

    def _analyze_cnpj_field(self, file_path: str, line_num: int, line: str, project_type: ProjectType) -> Optional[CNPJField]:
        """Analisa um campo CNPJ específico"""
        # Extrair nome do campo
        field_match = re.search(r'(\w+cnpj\w*|\w+documento\w*)', line, re.IGNORECASE)
        if not field_match:
            return None
            
        field_name = field_match.group(1)
        
        # Determinar tipo e tamanho do campo
        field_type, field_size = self._extract_field_type_and_size(line)
        
        # Determinar impacto e status
        impact_level, status, action_needed = self._assess_impact(field_type, field_size, project_type)
        
        return CNPJField(
            file_path=file_path,
            line_number=line_num,
            field_name=field_name,
            field_type=field_type,
            field_size=field_size,
            context=line.strip(),
            project_type=project_type,
            impact_level=impact_level,
            status=status,
            action_needed=action_needed,
            estimated_effort=self._estimate_effort(impact_level, project_type)
        )

    def _extract_field_type_and_size(self, line: str) -> tuple:
        """Extrai tipo e tamanho do campo da linha"""
        # Padrões para diferentes tipos de campo
        varchar_match = re.search(r'VARCHAR\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
        char_match = re.search(r'CHAR\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
        text_match = re.search(r'TEXT', line, re.IGNORECASE)
        int_match = re.search(r'INT|BIGINT', line, re.IGNORECASE)
        
        if varchar_match:
            return 'VARCHAR', int(varchar_match.group(1))
        elif char_match:
            return 'CHAR', int(char_match.group(1))
        elif text_match:
            return 'TEXT', None
        elif int_match:
            return 'INTEGER', None
        else:
            return 'UNKNOWN', None

    def _assess_impact(self, field_type: str, field_size: Optional[int], project_type: ProjectType) -> tuple:
        """Avalia o impacto da mudança do CNPJ alfanumérico"""
        if field_type == 'INTEGER':
            return ImpactLevel.HIGH, Status.INCOMPATIBLE, "Alterar tipo para VARCHAR(18)"
        elif field_type == 'VARCHAR' and field_size and field_size < 18:
            return ImpactLevel.MEDIUM, Status.ATTENTION, f"Aumentar tamanho de {field_size} para 18"
        elif field_type == 'VARCHAR' and field_size and field_size >= 18:
            return ImpactLevel.LOW, Status.COMPATIBLE, "Nenhuma alteração necessária"
        elif field_type == 'CHAR' and field_size and field_size < 18:
            return ImpactLevel.MEDIUM, Status.ATTENTION, f"Alterar para VARCHAR(18) ou aumentar CHAR para 18"
        elif field_type == 'TEXT':
            return ImpactLevel.LOW, Status.COMPATIBLE, "Nenhuma alteração necessária"
        else:
            return ImpactLevel.MEDIUM, Status.NEEDS_ANALYSIS, "Análise manual necessária"

    def _estimate_effort(self, impact_level: ImpactLevel, project_type: ProjectType) -> str:
        """Estima o esforço necessário baseado no nível de impacto"""
        effort_map = {
            ImpactLevel.LOW: "1-2 horas",
            ImpactLevel.MEDIUM: "4-8 horas",
            ImpactLevel.HIGH: "1-2 dias",
            ImpactLevel.CRITICAL: "2-5 dias"
        }
        return effort_map.get(impact_level, "A definir")

    def find_validations(self, files: List[Dict]) -> List[Dict]:
        """Encontra validações relacionadas a CNPJ"""
        validations = []
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.cnpj_patterns['validation_patterns']:
                    if re.search(pattern, line, re.IGNORECASE):
                        validations.append({
                            'file_path': file_path,
                            'line_number': line_num,
                            'line': line.strip(),
                            'validation_type': 'CNPJ'
                        })
        
        return validations

    def find_frontend_masks(self, files: List[Dict]) -> List[Dict]:
        """Encontra máscaras de CNPJ no frontend"""
        masks = []
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.cnpj_patterns['mask_patterns']:
                    if re.search(pattern, line, re.IGNORECASE):
                        masks.append({
                            'file_path': file_path,
                            'line_number': line_num,
                            'line': line.strip(),
                            'mask_type': 'CNPJ'
                        })
        
        return masks

    def analyze_project(self, project_path: str, output_dir: str = "reports") -> ProjectAnalysis:
        """Analisa um projeto completo"""
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise FileNotFoundError(f"Projeto não encontrado: {project_path}")
        
        self.console.print(f"[blue]Analisando projeto: {project_path.name}[/blue]")
        
        # Detectar tipo do projeto
        project_type = self.detect_project_type(project_path)
        if not project_type:
            project_type = ProjectType.PHP_LARAVEL  # Default
        self.console.print(f"[green]Tipo detectado: {project_type.value}[/green]")
        
        # Escanear arquivos
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task1 = progress.add_task("Escaneando arquivos de banco...", total=None)
            database_files = self.scan_database_files(project_path, project_type)
            progress.update(task1, completed=True)
            
            task2 = progress.add_task("Escaneando arquivos de código...", total=None)
            code_files = self.scan_code_files(project_path, project_type)
            progress.update(task2, completed=True)
            
            task3 = progress.add_task("Analisando campos CNPJ...", total=None)
            cnpj_fields = self.find_cnpj_fields(database_files + code_files, project_type)
            progress.update(task3, completed=True)
            
            task4 = progress.add_task("Buscando validações...", total=None)
            validations = self.find_validations(code_files)
            progress.update(task4, completed=True)
            
            task5 = progress.add_task("Buscando máscaras frontend...", total=None)
            masks = self.find_frontend_masks(code_files)
            progress.update(task5, completed=True)
        
        # Determinar impacto geral
        overall_impact = self._determine_overall_impact(cnpj_fields)
        
        # Gerar recomendações
        recommendations = self._generate_recommendations(cnpj_fields, validations, masks)
        
        # Criar análise
        analysis = ProjectAnalysis(
            project_name=project_path.name,
            project_path=str(project_path),
            project_type=project_type,
            total_files_scanned=len(database_files) + len(code_files),
            cnpj_fields_found=cnpj_fields,
            database_tables=self._extract_database_tables(database_files),
            migrations=self._extract_migrations(database_files),
            validations=validations,
            frontend_masks=masks,
            overall_impact=overall_impact,
            recommendations=recommendations,
            analysis_date=datetime.now()
        )
        
        # Salvar relatório
        self._save_report(analysis, output_dir)
        
        return analysis

    def analyze_all_projects(self, projects_folder: Path, output_dir: str = "reports") -> List[ProjectAnalysis]:
        """Analisa todos os projetos em uma pasta"""
        projects = self.discover_projects(projects_folder)
        
        if not projects:
            self.console.print("[yellow]Nenhum projeto encontrado na pasta especificada[/yellow]")
            return []
        
        self.console.print(f"[blue]Iniciando análise de {len(projects)} projetos...[/blue]")
        
        analyses = []
        for project in projects:
            try:
                analysis = self.analyze_project(project['path'], output_dir)
                analyses.append(analysis)
                self.console.print(f"[green]✓[/green] {project['name']} - Impacto: {analysis.overall_impact.value}")
            except Exception as e:
                self.console.print(f"[red]✗[/red] {project['name']} - Erro: {e}")
                self.logger.error(f"Erro ao analisar {project['name']}: {e}")
        
        return analyses

    def _determine_overall_impact(self, cnpj_fields: List[CNPJField]) -> ImpactLevel:
        """Determina o impacto geral baseado nos campos encontrados"""
        if not cnpj_fields:
            return ImpactLevel.LOW
            
        impact_counts = {
            ImpactLevel.LOW: 0,
            ImpactLevel.MEDIUM: 0,
            ImpactLevel.HIGH: 0,
            ImpactLevel.CRITICAL: 0
        }
        
        for field in cnpj_fields:
            impact_counts[field.impact_level] += 1
        
        # Determinar impacto geral
        if impact_counts[ImpactLevel.CRITICAL] > 0:
            return ImpactLevel.CRITICAL
        elif impact_counts[ImpactLevel.HIGH] > 0:
            return ImpactLevel.HIGH
        elif impact_counts[ImpactLevel.MEDIUM] > 0:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW

    def _generate_recommendations(self, cnpj_fields: List[CNPJField], validations: List[Dict], masks: List[Dict]) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recommendations = []
        
        # Recomendações para campos de banco
        incompatible_fields = [f for f in cnpj_fields if f.status == Status.INCOMPATIBLE]
        if incompatible_fields:
            recommendations.append(f"Alterar {len(incompatible_fields)} campos de tipo INTEGER para VARCHAR(18)")
        
        attention_fields = [f for f in cnpj_fields if f.status == Status.ATTENTION]
        if attention_fields:
            recommendations.append(f"Revisar {len(attention_fields)} campos que precisam de ajuste de tamanho")
        
        # Recomendações para validações
        if validations:
            recommendations.append(f"Atualizar {len(validations)} validações para aceitar CNPJ alfanumérico")
        
        # Recomendações para máscaras
        if masks:
            recommendations.append(f"Atualizar {len(masks)} máscaras frontend para CNPJ alfanumérico")
        
        if not recommendations:
            recommendations.append("Projeto compatível com CNPJ alfanumérico")
        
        return recommendations

    def _extract_database_tables(self, database_files: List[Dict]) -> List[Dict]:
        """Extrai informações de tabelas dos arquivos de banco"""
        tables = []
        
        for file_info in database_files:
            content = file_info['content']
            # Buscar definições de tabela
            table_matches = re.finditer(r'CREATE\s+TABLE\s+(\w+)', content, re.IGNORECASE)
            for match in table_matches:
                tables.append({
                    'table_name': match.group(1),
                    'file_path': file_info['file_path']
                })
        
        return tables

    def _extract_migrations(self, database_files: List[Dict]) -> List[Dict]:
        """Extrai informações de migrações"""
        migrations = []
        
        for file_info in database_files:
            file_path = file_info['file_path']
            if 'migration' in file_path.lower():
                migrations.append({
                    'file_path': file_path,
                    'migration_type': 'database'
                })
        
        return migrations

    def _save_report(self, analysis: ProjectAnalysis, output_dir: str):
        """Salva o relatório de análise"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Salvar relatório JSON
        json_path = output_path / f"{analysis.project_name}_analysis.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(analysis), f, indent=2, default=str)
        
        # Salvar relatório Markdown
        md_path = output_path / f"{analysis.project_name}_analysis.md"
        self._generate_markdown_report(analysis, md_path)
        
        self.console.print(f"[green]Relatório salvo em: {output_path}[/green]")

    def _generate_markdown_report(self, analysis: ProjectAnalysis, output_path: Path):
        """Gera relatório em Markdown"""
        template_content = self._get_report_template()
        template = Template(template_content)
        
        # Preparar dados para o template
        template_data = {
            'analysis': analysis,
            'cnpj_fields': analysis.cnpj_fields_found,
            'validations': analysis.validations,
            'masks': analysis.frontend_masks,
            'tables': analysis.database_tables,
            'migrations': analysis.migrations
        }
        
        report_content = template.render(**template_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

    def _get_report_template(self) -> str:
        """Retorna o template do relatório"""
        return """
# Análise de Impacto CNPJ Alfanumérico - {{ analysis.project_name }}

**Data:** {{ analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S') }}  
**Projeto:** {{ analysis.project_name }}  
**Tipo:** {{ analysis.project_type.value }}  
**Caminho:** {{ analysis.project_path }}

## Resumo Executivo

### Impacto Geral: {{ analysis.overall_impact.value.upper() }}

- **Total de arquivos escaneados:** {{ analysis.total_files_scanned }}
- **Campos CNPJ encontrados:** {{ analysis.cnpj_fields_found|length }}
- **Validações encontradas:** {{ analysis.validations|length }}
- **Máscaras frontend encontradas:** {{ analysis.frontend_masks|length }}

## Análise Detalhada

### 1. Campos CNPJ Identificados

{% if analysis.cnpj_fields_found %}
| Arquivo | Linha | Campo | Tipo | Tamanho | Status | Impacto | Ação Necessária |
|---------|-------|-------|------|---------|---------|---------|-----------------|
{% for field in analysis.cnpj_fields_found %}
| {{ field.file_path }} | {{ field.line_number }} | {{ field.field_name }} | {{ field.field_type }} | {{ field.field_size or 'N/A' }} | {{ field.status.value }} | {{ field.impact_level.value }} | {{ field.action_needed }} |
{% endfor %}
{% else %}
Nenhum campo CNPJ encontrado.
{% endif %}

### 2. Validações Encontradas

{% if analysis.validations %}
| Arquivo | Linha | Validação |
|---------|-------|-----------|
{% for validation in analysis.validations %}
| {{ validation.file_path }} | {{ validation.line_number }} | {{ validation.line }} |
{% endfor %}
{% else %}
Nenhuma validação específica encontrada.
{% endif %}

### 3. Máscaras Frontend

{% if analysis.frontend_masks %}
| Arquivo | Linha | Máscara |
|---------|-------|---------|
{% for mask in analysis.frontend_masks %}
| {{ mask.file_path }} | {{ mask.line_number }} | {{ mask.line }} |
{% endfor %}
{% else %}
Nenhuma máscara específica encontrada.
{% endif %}

## Recomendações

{% for recommendation in analysis.recommendations %}
- {{ recommendation }}
{% endfor %}

## Próximos Passos

1. **Revisar campos incompatíveis** - {{ analysis.cnpj_fields_found|selectattr('status', 'equalto', 'incompativel')|list|length }} campos precisam de alteração
2. **Atualizar validações** - {{ analysis.validations|length }} validações precisam ser revisadas
3. **Ajustar máscaras frontend** - {{ analysis.frontend_masks|length }} máscaras precisam ser atualizadas

---

**Status:** {{ analysis.overall_impact.value.upper() }}  
**Data da Análise:** {{ analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S') }}
"""

# Comandos CLI
@app.command()
def analyze(
    project_path: str = typer.Argument(..., help="Caminho para o projeto a ser analisado"),
    output: str = typer.Option("reports/", "--output", "-o", help="Diretório de saída para relatórios")
):
    """Analisa um projeto específico"""
    analyzer = CNPJAnalyzer()
    try:
        analysis = analyzer.analyze_project(project_path, output)
        analyzer.console.print(f"[green]✓ Análise concluída para {analysis.project_name}[/green]")
    except Exception as e:
        analyzer.console.print(f"[red]Erro na análise: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def analyze_all(
    projects_folder: str = typer.Option(None, "--projects-folder", "-f", help="Pasta com projetos para analisar"),
    output: str = typer.Option("reports/", "--output", "-o", help="Diretório de saída para relatórios")
):
    """Analisa todos os projetos em uma pasta"""
    analyzer = CNPJAnalyzer()
    
    # Usar variável de ambiente se não especificada
    if not projects_folder:
        projects_folder = analyzer.get_projects_folder()
        if not projects_folder:
            analyzer.console.print("[red]Erro: Especifique PROJECTS_FOLDER ou use --projects-folder[/red]")
            analyzer.console.print("[yellow]Exemplo: export PROJECTS_FOLDER=/caminho/para/projetos[/yellow]")
            raise typer.Exit(1)
    else:
        projects_folder = Path(projects_folder)
    
    try:
        analyses = analyzer.analyze_all_projects(projects_folder, output)
        analyzer.console.print(f"[green]✓ Análise concluída para {len(analyses)} projetos[/green]")
    except Exception as e:
        analyzer.console.print(f"[red]Erro na análise: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def discover_projects(
    projects_folder: str = typer.Option(None, "--projects-folder", "-f", help="Pasta com projetos para descobrir")
):
    """Descobre projetos em uma pasta"""
    analyzer = CNPJAnalyzer()
    
    # Usar variável de ambiente se não especificada
    if not projects_folder:
        projects_folder = analyzer.get_projects_folder()
        if not projects_folder:
            analyzer.console.print("[red]Erro: Especifique PROJECTS_FOLDER ou use --projects-folder[/red]")
            raise typer.Exit(1)
    else:
        projects_folder = Path(projects_folder)
    
    try:
        projects = analyzer.discover_projects(projects_folder)
        analyzer.console.print(f"[green]✓ Encontrados {len(projects)} projetos[/green]")
        
        # Mostrar tabela de projetos
        table = Table(title=f"Projetos Descobertos em {projects_folder}")
        table.add_column("Nome", style="cyan")
        table.add_column("Tipo", style="green")
        table.add_column("Caminho", style="yellow")
        
        for project in projects:
            table.add_row(project['name'], project['type'], project['path'])
        
        analyzer.console.print(table)
        
    except Exception as e:
        analyzer.console.print(f"[red]Erro na descoberta: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def quick_scan(
    project_path: str = typer.Argument(..., help="Caminho para o projeto")
):
    """Escaneamento rápido de um projeto"""
    analyzer = CNPJAnalyzer()
    project_path = Path(project_path)
    
    if not project_path.exists():
        analyzer.console.print(f"[red]Projeto não encontrado: {project_path}[/red]")
        raise typer.Exit(1)
    
    # Escaneamento rápido
    project_type = analyzer.detect_project_type(project_path)
    if not project_type:
        project_type = ProjectType.PHP_LARAVEL  # Default
    code_files = analyzer.scan_code_files(project_path, project_type)
    cnpj_fields = analyzer.find_cnpj_fields(code_files, project_type)
    
    # Exibir resultados
    table = Table(title=f"Escaneamento Rápido - {project_path.name}")
    table.add_column("Arquivo", style="cyan")
    table.add_column("Campo", style="green")
    table.add_column("Tipo", style="yellow")
    table.add_column("Status", style="red")
    
    for field in cnpj_fields:
        status_icon = "✅" if field.status == Status.COMPATIBLE else "⚠️" if field.status == Status.ATTENTION else "❌"
        table.add_row(
            field.file_path,
            field.field_name,
            field.field_type,
            f"{status_icon} {field.status.value}"
        )
    
    analyzer.console.print(table)

@app.command()
def validate_cnpj(
    project_path: str = typer.Argument(..., help="Caminho para o projeto")
):
    """Valida estrutura de CNPJ em um projeto"""
    analyzer = CNPJAnalyzer()
    project_path = Path(project_path)
    
    if not project_path.exists():
        analyzer.console.print(f"[red]Projeto não encontrado: {project_path}[/red]")
        raise typer.Exit(1)
    
    # Buscar validações específicas
    project_type = analyzer.detect_project_type(project_path)
    if not project_type:
        project_type = ProjectType.PHP_LARAVEL  # Default
    code_files = analyzer.scan_code_files(project_path, project_type)
    validations = analyzer.find_validations(code_files)
    
    analyzer.console.print(f"[blue]Validações CNPJ encontradas em {project_path.name}:[/blue]")
    for validation in validations:
        analyzer.console.print(f"  📄 {validation['file_path']}:{validation['line_number']} - {validation['line']}")

@app.command()
def find_migrations(
    project_path: str = typer.Argument(..., help="Caminho para o projeto")
):
    """Encontra migrações relacionadas a CNPJ"""
    analyzer = CNPJAnalyzer()
    project_path = Path(project_path)
    
    if not project_path.exists():
        analyzer.console.print(f"[red]Projeto não encontrado: {project_path}[/red]")
        raise typer.Exit(1)
    
    # Buscar migrações
    project_type = analyzer.detect_project_type(project_path)
    if not project_type:
        project_type = ProjectType.PHP_LARAVEL  # Default
    database_files = analyzer.scan_database_files(project_path, project_type)
    
    analyzer.console.print(f"[blue]Migrações encontradas em {project_path.name}:[/blue]")
    for file_info in database_files:
        if 'migration' in file_info['file_path'].lower():
            analyzer.console.print(f"  📄 {file_info['file_path']}")

@app.command()
def find_validations(
    project_path: str = typer.Argument(..., help="Caminho para o projeto")
):
    """Encontra validações de CNPJ"""
    validate_cnpj(project_path)

@app.command()
def find_masks(
    project_path: str = typer.Argument(..., help="Caminho para o projeto")
):
    """Encontra máscaras de CNPJ no frontend"""
    analyzer = CNPJAnalyzer()
    project_path = Path(project_path)
    
    if not project_path.exists():
        analyzer.console.print(f"[red]Projeto não encontrado: {project_path}[/red]")
        raise typer.Exit(1)
    
    # Buscar máscaras
    project_type = analyzer.detect_project_type(project_path)
    if not project_type:
        project_type = ProjectType.PHP_LARAVEL  # Default
    code_files = analyzer.scan_code_files(project_path, project_type)
    masks = analyzer.find_frontend_masks(code_files)
    
    analyzer.console.print(f"[blue]Máscaras CNPJ encontradas em {project_path.name}:[/blue]")
    for mask in masks:
        analyzer.console.print(f"  🎭 {mask['file_path']}:{mask['line_number']} - {mask['line']}")

if __name__ == "__main__":
    app()
