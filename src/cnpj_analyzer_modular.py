#!/usr/bin/env python3
"""
Analisador de Impacto CNPJ Alfanumérico - Versão Modular
Versão: 2.0
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

from .analyzer_factory import AnalyzerFactory

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

    def analyze_project(self, project_path: Path, project_type: Optional[str] = None) -> Dict[str, Any]:
        """Analisa um projeto usando o analisador apropriado"""
        try:
            # Detectar tipo de projeto se não especificado
            if project_type is None:
                project_type = self.factory.detect_project_type(project_path)
            
            self.console.print(f"[blue]Tipo detectado: {project_type}[/blue]")
            
            # Usar factory para criar analisador apropriado
            result = self.factory.analyze_project(project_path, project_type)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar projeto {project_path}: {e}")
            return {
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

    def analyze_all_projects(self, projects_folder: Path, output_dir: Path) -> List[Dict[str, Any]]:
        """Analisa todos os projetos em uma pasta"""
        projects = self.discover_projects(projects_folder)
        results = []
        
        if not projects:
            self.console.print("[red]Nenhum projeto encontrado[/red]")
            return results
        
        self.console.print(f"[blue]Iniciando análise de {len(projects)} projetos...[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            for project in projects:
                project_path = Path(project['path'])
                task = progress.add_task(f"Analisando {project['name']}...", total=None)
                
                try:
                    result = self.analyze_project(project_path, project['type'])
                    result['project_name'] = project['name']
                    result['project_path'] = project['path']
                    results.append(result)
                    
                    # Determinar impacto geral
                    impact = self._determine_overall_impact(result)
                    self.console.print(f"✓ {project['name']} - Impacto: {impact.value}")
                    
                    # Salvar relatório individual
                    self._save_individual_report(result, output_dir)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao analisar {project['name']}: {e}")
                    self.console.print(f"✗ {project['name']} - Erro: {e}")
                
                progress.remove_task(task)
        
        self.console.print(f"✓ Análise concluída para {len(results)} projetos")
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
            if hasattr(field, 'impact_level'):
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
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=str, ensure_ascii=False)
            
            # Salvar Markdown
            md_file = output_dir / f"{project_name}_analysis.md"
            self._generate_markdown_report(result, md_file)
            
            self.console.print(f"Relatório salvo em: {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório: {e}")

    def _generate_markdown_report(self, result: Dict[str, Any], output_file: Path):
        """Gera relatório Markdown"""
        try:
            project_name = result.get('project_name', 'Unknown')
            project_type = result.get('project_type', 'Unknown')
            total_files = result.get('total_files_scanned', 0)
            cnpj_fields = result.get('cnpj_fields_found', [])
            validations = result.get('validations', [])
            masks = result.get('frontend_masks', [])
            
            impact = self._determine_overall_impact(result)
            
            report_content = f"""# Relatório de Análise CNPJ Alfanumérico

## Informações do Projeto
- **Nome**: {project_name}
- **Tipo**: {project_type}
- **Data da Análise**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Arquivos Escaneados**: {total_files}
- **Impacto Geral**: {impact.value.upper()}

## Campos CNPJ Encontrados
"""
            
            if cnpj_fields:
                report_content += """
| Arquivo | Linha | Campo | Tipo | Tamanho | Impacto | Status | Ação Necessária |
|---------|-------|-------|------|---------|---------|--------|-----------------|
"""
                for field in cnpj_fields:
                    if hasattr(field, 'file_path'):
                        report_content += f"| {field.file_path} | {field.line_number} | {field.field_name} | {field.field_type} | {field.field_size or 'N/A'} | {field.impact_level.value} | {field.status.value} | {field.action_needed} |\n"
            else:
                report_content += "Nenhum campo CNPJ encontrado.\n"
            
            report_content += f"""
## Validações Encontradas
Total: {len(validations)}

"""
            
            if validations:
                for validation in validations[:10]:  # Limitar a 10 para não ficar muito longo
                    report_content += f"- {validation.get('file_path', 'Unknown')}:{validation.get('line_number', '?')} - {validation.get('line', 'Unknown')}\n"
            
            report_content += f"""
## Máscaras Frontend Encontradas
Total: {len(masks)}

"""
            
            if masks:
                for mask in masks[:10]:  # Limitar a 10
                    report_content += f"- {mask.get('file_path', 'Unknown')}:{mask.get('line_number', '?')} - {mask.get('line', 'Unknown')}\n"
            
            # Salvar arquivo
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório Markdown: {e}")

    def get_supported_types(self) -> Dict[str, str]:
        """Retorna os tipos de projeto suportados"""
        return self.factory.get_supported_types()

# Instância global
analyzer = CNPJAnalyzerModular()

@app.command()
def analyze(
    project_path: str = typer.Argument(..., help="Caminho para o projeto a ser analisado"),
    project_type: Optional[str] = typer.Option(None, help="Tipo de projeto (detectado automaticamente se não especificado)"),
    output: str = typer.Option("reports/", help="Diretório de saída para relatórios")
):
    """Analisa um projeto específico"""
    project_path = Path(project_path)
    output_dir = Path(output)
    
    if not project_path.exists():
        console.print(f"[red]Projeto não encontrado: {project_path}[/red]")
        raise typer.Exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = analyzer.analyze_project(project_path, project_type)
    analyzer._save_individual_report(result, output_dir)

@app.command()
def analyze_all(
    projects_folder: Optional[str] = typer.Option(None, help="Pasta contendo projetos (usa PROJECTS_FOLDER se não especificado)"),
    output: str = typer.Option("reports/", help="Diretório de saída para relatórios")
):
    """Analisa todos os projetos em uma pasta"""
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
    
    results = analyzer.analyze_all_projects(projects_folder, output_dir)

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

if __name__ == "__main__":
    app()
