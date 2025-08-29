#!/usr/bin/env python3
"""
Analisador de Impacto CNPJ Alfanumérico - Versão Modular
Versão: 2.0
Data: 2025-01-27
Objetivo: Identificar impactos da mudança do CNPJ de numérico para alfanumérico em projetos
"""

import os
import sys
import re
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import concurrent.futures
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from jinja2 import Template

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from analyzer_factory import AnalyzerFactory

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
    project_type: str
    impact_level: ImpactLevel
    status: Status
    action_needed: str
    estimated_effort: str

@dataclass
class ProjectAnalysis:
    """Resultado da análise de um projeto"""
    project_name: str
    project_path: str
    project_type: str
    total_files_scanned: int
    cnpj_fields_found: List[CNPJField]
    validations: List[Dict]
    frontend_masks: List[Dict]
    overall_impact: ImpactLevel
    recommendations: List[str]
    analysis_date: datetime

class CNPJAnalyzerModular:
    """Analisador principal modular para identificar impactos do CNPJ alfanumérico"""
    
    def __init__(self):
        self.factory = AnalyzerFactory()
        self.console = Console()
        self.logger = logging.getLogger(__name__)

    def analyze_project(self, project_path: Path, project_type: Optional[str] = None, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Analisa um projeto usando o analisador apropriado"""
        try:
            # Detectar tipo de projeto se não especificado
            if project_type is None:
                project_type = self.factory.detect_project_type(project_path)
            
            self.console.print(f"[blue]Tipo detectado: {project_type}[/blue]")
            
            # Usar factory para criar analisador apropriado
            result = self.factory.analyze_project(project_path, filters)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar projeto {project_path}: {e}")
            return {
                'project_name': project_path.name,
                'error': str(e),
                'project_path': str(project_path),
                'project_type': project_type or 'unknown'
            }

    def discover_projects(self, projects_folder: Path) -> List[Dict[str, Any]]:
        """Descobre projetos em uma pasta"""
        projects = []
        
        if not projects_folder.exists():
            self.console.print(f"[red]Pasta não encontrada: {projects_folder}[/red]")
            return projects
        
        self.console.print(f"[blue]Descobrindo projetos em: {projects_folder}[/blue]")
        
        for item in projects_folder.iterdir():
            if item.is_dir():
                project_type = self.factory.detect_project_type(item)
                
                projects.append({
                    'name': item.name,
                    'path': str(item),
                    'type': project_type
                })
                
                status_icon = "✓" if project_type != 'unknown' else "⚠"
                self.console.print(f"  {status_icon} {item.name} ({project_type})")
        
        self.console.print(f"✓ Encontrados {len(projects)} projetos")
        return projects

    def analyze_all_projects(self, projects_folder: Path, output_dir: Path, max_workers: int = 4, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Analisa todos os projetos em uma pasta usando multithreading"""
        projects = self.discover_projects(projects_folder)
        results = []
        
        if not projects:
            self.console.print("[red]Nenhum projeto encontrado[/red]")
            return results
        
        self.console.print(f"[blue]Iniciando análise paralela de {len(projects)} projetos com {max_workers} workers...[/blue]")
        if filters:
            self.console.print(f"[yellow]Filtros aplicados: {filters}[/yellow]")
        
        # Lock para thread-safe logging
        lock = threading.Lock()
        
        def analyze_single_project(project):
            """Função para analisar um projeto individual"""
            project_path = Path(project['path'])
            
            try:
                result = self.analyze_project(project_path, filters)
                result['project_name'] = project['name']
                result['project_path'] = project['path']
                
                # Verificar se houve erro na análise
                if 'error' in result and result['error']:
                    with lock:
                        self.logger.error(f"Erro ao analisar {project['name']}: {result['error']}")
                        self.console.print(f"✗ {project['name']} - Erro: {result['error']}")
                else:
                    # Determinar impacto geral
                    try:
                        impact = self._determine_overall_impact(result)
                        impact_str = impact.value if hasattr(impact, 'value') else str(impact)
                        with lock:
                            self.console.print(f"✓ {project['name']} - Impacto: {impact_str}")
                    except Exception as e:
                        with lock:
                            self.logger.error(f"Erro ao determinar impacto para {project['name']}: {e}")
                            self.console.print(f"✓ {project['name']} - Impacto: MEDIUM (erro na determinação)")
                    
                    # Salvar relatório individual
                    self._save_individual_report(result, output_dir)
                
                return result
                
            except Exception as e:
                with lock:
                    self.logger.error(f"Erro ao analisar {project['name']}: {e}")
                    self.console.print(f"✗ {project['name']} - Erro: {e}")
                return None
        
        # Executar análise em paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submeter todas as tarefas
            future_to_project = {executor.submit(analyze_single_project, project): project for project in projects}
            
            # Processar resultados conforme completam
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Analisando projetos...", total=len(projects))
                
                for future in as_completed(future_to_project):
                    project = future_to_project[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        with lock:
                            self.logger.error(f"Erro inesperado ao analisar {project['name']}: {e}")
                    
                    progress.advance(task)
        
        self.console.print(f"✓ Análise paralela concluída para {len(results)} projetos")
        return results

    def _determine_overall_impact(self, result: Dict[str, Any]) -> ImpactLevel:
        """Determina o impacto geral baseado nos campos encontrados"""
        if 'cnpj_fields_found' not in result:
            return ImpactLevel.LOW
        
        cnpj_fields = result['cnpj_fields_found']
        if not cnpj_fields:
            return ImpactLevel.LOW
        
        # Contar campos por nível de impacto
        impact_counts = {
            ImpactLevel.LOW: 0,
            ImpactLevel.MEDIUM: 0,
            ImpactLevel.HIGH: 0,
            ImpactLevel.CRITICAL: 0
        }
        
        for field in cnpj_fields:
            # Verificar se é string (representação) ou objeto
            if isinstance(field, str):
                # Se for string, procurar por padrões de impacto
                if 'CRITICAL' in field or 'critico' in field:
                    impact_counts[ImpactLevel.CRITICAL] += 1
                elif 'HIGH' in field or 'alto' in field:
                    impact_counts[ImpactLevel.HIGH] += 1
                elif 'MEDIUM' in field or 'medio' in field:
                    impact_counts[ImpactLevel.MEDIUM] += 1
                else:
                    impact_counts[ImpactLevel.LOW] += 1
            elif isinstance(field, dict):
                # Se for dicionário (dados serializados)
                impact_level_str = field.get('impact_level', 'MEDIUM').lower()
                if 'critical' in impact_level_str or 'critico' in impact_level_str:
                    impact_counts[ImpactLevel.CRITICAL] += 1
                elif 'high' in impact_level_str or 'alto' in impact_level_str:
                    impact_counts[ImpactLevel.HIGH] += 1
                elif 'medium' in impact_level_str or 'medio' in impact_level_str:
                    impact_counts[ImpactLevel.MEDIUM] += 1
                else:
                    impact_counts[ImpactLevel.LOW] += 1
            elif hasattr(field, 'impact_level'):
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

    def _save_individual_report(self, result: Dict[str, Any], output_dir: Path):
        """Salva relatório individual para um projeto"""
        try:
            project_name = result.get('project_name', 'unknown')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Salvar JSON
            json_file = output_dir / f"{project_name}_analysis.json"
            
            # Preparar dados para serialização
            serializable_result = {}
            for key, value in result.items():
                if key == 'cnpj_fields_found':
                    # Converter campos CNPJ para formato serializável
                    serializable_fields = []
                    for field in value:
                        if isinstance(field, str):
                            # Extrair informações da string
                            serializable_fields.append({
                                'file_path': 'Campo CNPJ',
                                'line_number': '-',
                                'field_name': 'CNPJ',
                                'field_type': 'UNKNOWN',
                                'field_size': None,
                                'impact_level': 'MEDIUM',
                                'status': 'NEEDS_ANALYSIS',
                                'action_needed': 'Análise manual necessária',
                                'estimated_effort': '4-8 horas'
                            })
                        else:
                            serializable_fields.append({
                                'file_path': getattr(field, 'file_path', 'Unknown'),
                                'line_number': getattr(field, 'line_number', 0),
                                'field_name': getattr(field, 'field_name', 'Unknown'),
                                'field_type': getattr(field, 'field_type', 'Unknown'),
                                'field_size': getattr(field, 'field_size', None),
                                'impact_level': getattr(field, 'impact_level', 'MEDIUM').value if hasattr(field, 'impact_level') else 'MEDIUM',
                                'status': getattr(field, 'status', 'NEEDS_ANALYSIS').value if hasattr(field, 'status') else 'NEEDS_ANALYSIS',
                                'action_needed': getattr(field, 'action_needed', 'Análise manual necessária'),
                                'estimated_effort': getattr(field, 'estimated_effort', '4-8 horas')
                            })
                    serializable_result[key] = serializable_fields
                else:
                    serializable_result[key] = value
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, indent=2, ensure_ascii=False)
            
            # Salvar Markdown
            md_file = output_dir / f"{project_name}_analysis.md"
            try:
                self._generate_markdown_report(result, md_file)
            except Exception as e:
                self.logger.error(f"Erro ao gerar Markdown para {project_name}: {e}")
                # Criar um Markdown básico em caso de erro
                basic_content = f"""# Relatório de Análise CNPJ Alfanumérico

## Informações do Projeto
- **Nome**: {project_name}
- **Tipo**: {result.get('project_type', 'Unknown')}
- **Data da Análise**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Arquivos Escaneados**: {result.get('total_files_scanned', 0)}
- **Campos CNPJ Encontrados**: {len(result.get('cnpj_fields_found', []))}

## Erro na Geração
Houve um erro ao gerar o relatório completo: {e}

Consulte o arquivo JSON para mais detalhes.
"""
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(basic_content)
            
            self.console.print(f"Relatório salvo em: {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório: {e}")

    def _generate_markdown_report(self, result: Dict[str, Any], output_file: Path):
        """Gera relatório Markdown formatado com resumo no topo e arquivos categorizados"""
        try:
            project_name = result.get('project_name', 'Unknown')
            project_type = result.get('project_type', 'Unknown')
            total_files = result.get('total_files_scanned', 0)
            cnpj_fields = result.get('cnpj_fields_found', [])
            validations = result.get('validations', [])
            masks = result.get('frontend_masks', [])
            
            try:
                impact = self._determine_overall_impact(result)
                impact_str = impact.value if hasattr(impact, 'value') else str(impact)
            except Exception as e:
                self.logger.error(f"Erro ao determinar impacto: {e}")
                impact_str = "MEDIUM"
            
            # Contar campos por nível de impacto
            impact_counts = {'baixo': 0, 'medio': 0, 'alto': 0, 'critico': 0}
            for field in cnpj_fields:
                if isinstance(field, dict):
                    impact_level = field.get('impact_level', 'medio').lower()
                    impact_counts[impact_level] = impact_counts.get(impact_level, 0) + 1
                elif hasattr(field, 'impact_level'):
                    impact_level = field.impact_level.value.lower()
                    impact_counts[impact_level] = impact_counts.get(impact_level, 0) + 1
            
            # Categorizar campos por tipo de arquivo
            categorized_fields = self._categorize_fields(cnpj_fields)
            
            report_content = f"""# Relatório de Análise CNPJ Alfanumérico

## 📋 RESUMO EXECUTIVO

### Informações do Projeto
- **Nome**: {project_name}
- **Tipo**: {project_type}
- **Data da Análise**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total de Arquivos Escaneados**: {total_files}

### Impacto Geral
- **Nível de Impacto**: {impact_str.upper()}
- **Total de Campos CNPJ**: {len(cnpj_fields)}
- **Validações Encontradas**: {len(validations)}
- **Máscaras Frontend**: {len(masks)}

### Distribuição por Impacto
- **🟢 Baixo**: {impact_counts['baixo']} campos
- **🟡 Médio**: {impact_counts['medio']} campos  
- **🟠 Alto**: {impact_counts['alto']} campos
- **🔴 Crítico**: {impact_counts['critico']} campos

### Categorias de Arquivos
- **📁 Migrações**: {len(categorized_fields.get('migrations', []))} campos
- **💻 Código**: {len(categorized_fields.get('code', []))} campos
- **🧪 Testes**: {len(categorized_fields.get('tests', []))} campos
- **🗄️ ETL**: {len(categorized_fields.get('etl', []))} campos
- **📄 Outros**: {len(categorized_fields.get('others', []))} campos

## 🚨 CAMPOS CRÍTICOS (Requerem Ação Imediata)

"""
            
            # Listar campos críticos primeiro
            critical_fields = []
            for field in cnpj_fields:
                if isinstance(field, dict) and field.get('impact_level', '').lower() == 'critico':
                    critical_fields.append(field)
                elif hasattr(field, 'impact_level') and field.impact_level.value.lower() == 'critico':
                    critical_fields.append(field)
            
            if critical_fields:
                report_content += "| Arquivo | Linha | Campo | Tipo | Tamanho | Status | Ação Necessária |\n"
                report_content += "|---------|-------|-------|------|---------|--------|-----------------|\n"
                
                for field in critical_fields:
                    if isinstance(field, dict):
                        file_path = field.get('file_path', 'Unknown')
                        line_number = field.get('line_number', '?')
                        field_name = field.get('field_name', 'Unknown')
                        field_type = field.get('field_type', 'Unknown')
                        field_size = field.get('field_size', 'N/A')
                        status = field.get('status', 'precisa_analise')
                        action_needed = field.get('action_needed', 'Análise manual necessária')
                    else:
                        file_path = field.file_path
                        line_number = field.line_number
                        field_name = field.field_name
                        field_type = field.field_type
                        field_size = field.field_size or 'N/A'
                        status = field.status.value
                        action_needed = field.action_needed
                    
                    report_content += f"| {file_path} | {line_number} | {field_name} | {field_type} | {field_size} | {status} | {action_needed} |\n"
            else:
                report_content += "*Nenhum campo crítico encontrado.*\n"
            
            # Adicionar campos por categoria
            for category, fields in categorized_fields.items():
                if fields:
                    category_name = {
                        'migrations': '📁 MIGRAÇÕES',
                        'code': '💻 CÓDIGO',
                        'tests': '🧪 TESTES',
                        'etl': '🗄️ ETL',
                        'others': '📄 OUTROS'
                    }.get(category, category.upper())
                    
                    report_content += f"\n## {category_name}\n\n"
                    report_content += "| Arquivo | Linha | Campo | Tipo | Tamanho | Impacto | Status | Ação Necessária | Esforço Estimado |\n"
                    report_content += "|---------|-------|-------|------|---------|---------|--------|-----------------|------------------|\n"
                    
                    for field in fields:
                        if isinstance(field, dict):
                            file_path = field.get('file_path', 'Unknown')
                            line_number = field.get('line_number', '?')
                            field_name = field.get('field_name', 'Unknown')
                            field_type = field.get('field_type', 'Unknown')
                            field_size = field.get('field_size', 'N/A')
                            impact_level = field.get('impact_level', 'medio')
                            status = field.get('status', 'precisa_analise')
                            action_needed = field.get('action_needed', 'Análise manual necessária')
                            estimated_effort = field.get('estimated_effort', 'A definir')
                        else:
                            file_path = field.file_path
                            line_number = field.line_number
                            field_name = field.field_name
                            field_type = field.field_type
                            field_size = field.field_size or 'N/A'
                            impact_level = field.impact_level.value
                            status = field.status.value
                            action_needed = field.action_needed
                            estimated_effort = field.estimated_effort
                        
                        report_content += f"| {file_path} | {line_number} | {field_name} | {field_type} | {field_size} | {impact_level} | {status} | {action_needed} | {estimated_effort} |\n"
            
            # Adicionar validações e máscaras no final
            if validations:
                report_content += "\n## 🔍 VALIDAÇÕES ENCONTRADAS\n\n"
                for validation in validations[:20]:  # Limitar a 20
                    report_content += f"- {validation.get('file_path', 'Unknown')}:{validation.get('line_number', '?')} - {validation.get('line', 'Unknown')}\n"
            
            if masks:
                report_content += "\n## 🎭 MÁSCARAS FRONTEND ENCONTRADAS\n\n"
                for mask in masks[:20]:  # Limitar a 20
                    report_content += f"- {mask.get('file_path', 'Unknown')}:{mask.get('line_number', '?')} - {mask.get('line', 'Unknown')}\n"
            
            # Salvar arquivo
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório Markdown: {e}")

    def _categorize_fields(self, cnpj_fields: List) -> Dict[str, List]:
        """Categoriza campos CNPJ por tipo de arquivo"""
        categorized = {
            'migrations': [],
            'code': [],
            'tests': [],
            'etl': [],
            'others': []
        }
        
        for field in cnpj_fields:
            if isinstance(field, dict):
                file_path = field.get('file_path', '')
            else:
                file_path = field.file_path
            
            file_path_lower = file_path.lower()
            
            # Detectar arquivos de teste primeiro
            if any(test_pattern in file_path_lower for test_pattern in ['test', 'tests', 'spec', 'specs', 'phpunit', 'jest', 'junit']):
                categorized['tests'].append(field)
            elif 'migration' in file_path_lower or 'migrations' in file_path_lower:
                categorized['migrations'].append(field)
            elif any(ext in file_path_lower for ext in ['.ktr', '.kjb', '.xml', 'pentaho', 'etl']):
                categorized['etl'].append(field)
            elif any(ext in file_path_lower for ext in ['.php', '.js', '.ts', '.jsx', '.tsx', '.vue', '.py', '.java']):
                categorized['code'].append(field)
            else:
                categorized['others'].append(field)
        
        return categorized

    def get_supported_types(self) -> Dict[str, str]:
        """Retorna os tipos de projeto suportados"""
        return self.factory.get_supported_types()

# Instância global
analyzer = CNPJAnalyzerModular()

@app.command()
def analyze(
    project_path: str = typer.Argument(..., help="Caminho para o projeto a ser analisado"),
    project_type: Optional[str] = typer.Option(None, help="Tipo de projeto (detectado automaticamente se não especificado)"),
    output: str = typer.Option("reports/", help="Diretório de saída para relatórios"),
    skip_tests: bool = typer.Option(False, help="Ignorar pastas de testes"),
    focus_migrations: bool = typer.Option(False, help="Focar apenas em arquivos de migração")
):
    """Analisa um projeto específico"""
    project_path = Path(project_path)
    output_dir = Path(output)
    
    if not project_path.exists():
        console.print(f"[red]Projeto não encontrado: {project_path}[/red]")
        raise typer.Exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar filtros
    filters = {}
    if skip_tests:
        filters['skip_patterns'] = ['tests', 'Tests', 'test', 'Test']
    if focus_migrations:
        filters['include_patterns'] = ['migration', 'Migration', 'migrations', 'Migrations']
    
    result = analyzer.analyze_project(project_path, project_type, filters)
    analyzer._save_individual_report(result, output_dir)

@app.command()
def analyze_all(
    projects_folder: Optional[str] = typer.Option(None, help="Pasta contendo projetos (usa PROJECTS_FOLDER se não especificado)"),
    output: str = typer.Option("reports/", help="Diretório de saída para relatórios"),
    workers: int = typer.Option(4, help="Número de workers para análise paralela"),
    skip_tests: bool = typer.Option(False, help="Ignorar pastas de testes"),
    focus_migrations: bool = typer.Option(False, help="Focar apenas em arquivos de migração")
):
    """Analisa todos os projetos em uma pasta usando multithreading"""
    if projects_folder is None:
        projects_folder = os.getenv('PROJECTS_FOLDER')
        if not projects_folder:
            console.print("[red]Erro: Especifique --projects-folder ou configure PROJECTS_FOLDER[/red]")
            raise typer.Exit(1)
    
    projects_folder = Path(projects_folder)
    output_dir = Path(output)
    
    if not projects_folder.exists():
        console.print(f"[red]Pasta não encontrada: {projects_folder}[/red]")
        raise typer.Exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar filtros
    filters = {}
    if skip_tests:
        filters['skip_patterns'] = ['tests', 'Tests', 'test', 'Test']
    if focus_migrations:
        filters['include_patterns'] = ['migration', 'Migration', 'migrations', 'Migrations']
    
    results = analyzer.analyze_all_projects(projects_folder, output_dir, workers, filters)

@app.command()
def discover_projects(
    projects_folder: Optional[str] = typer.Option(None, help="Pasta contendo projetos (usa PROJECTS_FOLDER se não especificado)")
):
    """Descobre projetos em uma pasta"""
    if projects_folder is None:
        projects_folder = os.getenv('PROJECTS_FOLDER')
        if not projects_folder:
            console.print("[red]Erro: Especifique --projects-folder ou configure PROJECTS_FOLDER[/red]")
            raise typer.Exit(1)
    
    projects_folder = Path(projects_folder)
    projects = analyzer.discover_projects(projects_folder)
    
    if projects:
        table = Table(title=f"Projetos Descobertos em {projects_folder}")
        table.add_column("Nome", style="cyan")
        table.add_column("Tipo", style="magenta")
        table.add_column("Caminho", style="green")
        
        for project in projects:
            table.add_row(project['name'], project['type'], project['path'])
        
        console.print(table)

@app.command()
def list_types():
    """Lista os tipos de projeto suportados"""
    types = analyzer.get_supported_types()
    
    table = Table(title="Tipos de Projeto Suportados")
    table.add_column("Código", style="cyan")
    table.add_column("Descrição", style="green")
    
    for code, description in types.items():
        table.add_row(code, description)
    
    console.print(table)

@app.command()
def general_analysis(reports_dir: str = typer.Option("reports/", help="Diretório com relatórios de projetos")):
    """Gera relatório geral de todos os projetos analisados"""
    from src.analyzers.general_analyzer import GeneralAnalyzer
    
    print("🔍 Gerando relatório geral...")
    
    # Usar a pasta Azure como padrão
    projects_folder = os.path.expanduser("~/Documents/Azure")
    
    analyzer = GeneralAnalyzer(reports_dir)
    analysis_data = analyzer.analyze_all_projects(projects_folder)
    
    # Gerar relatório Markdown
    output_file = analyzer.generate_markdown_report(analysis_data)
    
    print(f"✅ Relatório geral salvo em: {output_file}")
    
    # Mostrar resumo
    stats = analysis_data.get('statistics', {})
    critical_projects = analysis_data.get('critical_projects', 0)
    
    print(f"\n📊 RESUMO:")
    print(f"   Total de projetos: {analysis_data.get('total_projects', 0)}")
    print(f"   Projetos com pontos críticos: {critical_projects}")
    print(f"   Total de campos CNPJ: {stats.get('total_fields', 0)}")
    print(f"   Campos críticos: {stats.get('total_critical_fields', 0)}")
    print(f"   Campos de alto impacto: {stats.get('total_high_impact_fields', 0)}")

if __name__ == "__main__":
    app()
