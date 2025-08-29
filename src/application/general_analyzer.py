"""
Analisador Geral - Resumo de Todos os Projetos
Versão: 1.0
Data: 2025-08-29
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

from .base_analyzer import ImpactLevel, Status


@dataclass
class ProjectSummary:
    """Resumo de um projeto"""
    name: str
    path: str
    type: str
    total_fields: int
    critical_fields: int
    high_impact_fields: int
    medium_impact_fields: int
    low_impact_fields: int
    overall_impact: str
    needs_attention: bool
    categories: Dict[str, int]
    critical_details: List[Dict[str, Any]]


class GeneralAnalyzer:
    """Analisador geral que processa múltiplos projetos"""
    
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.projects = []
    
    def analyze_all_projects(self, projects_folder: str) -> Dict[str, Any]:
        """Analisa todos os projetos em uma pasta"""
        projects_path = Path(projects_folder)
        
        if not projects_path.exists():
            raise FileNotFoundError(f"Pasta de projetos não encontrada: {projects_folder}")
        
        # Encontrar todos os projetos
        project_dirs = [d for d in projects_path.iterdir() if d.is_dir()]
        
        print(f"🔍 Encontrados {len(project_dirs)} projetos para análise...")
        
        summaries = []
        critical_projects = []
        
        for project_dir in project_dirs:
            try:
                summary = self._analyze_single_project(project_dir)
                if summary:
                    summaries.append(summary)
                    if summary.needs_attention:
                        critical_projects.append(summary)
            except Exception as e:
                print(f"⚠️ Erro ao analisar {project_dir.name}: {e}")
        
        # Ordenar por impacto (crítico primeiro)
        critical_projects.sort(key=lambda x: (x.critical_fields, x.high_impact_fields), reverse=True)
        
        return {
            'total_projects': len(summaries),
            'critical_projects': len(critical_projects),
            'analysis_date': datetime.now().isoformat(),
            'projects_folder': str(projects_folder),
            'critical_projects_details': [self._project_to_dict(p) for p in critical_projects],
            'all_projects_summary': [self._project_to_dict(p) for p in summaries],
            'statistics': self._calculate_statistics(summaries)
        }
    
    def _analyze_single_project(self, project_path: Path) -> ProjectSummary:
        """Analisa um projeto individual"""
        project_name = project_path.name
        
        # Procurar relatório JSON
        json_report = self.reports_dir / f"{project_name}_analysis.json"
        
        if not json_report.exists():
            print(f"⚠️ Relatório não encontrado para {project_name}")
            return None
        
        try:
            with open(json_report, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Contar campos por impacto
            fields = data.get('cnpj_fields_found', [])
            critical_fields = sum(1 for f in fields if f.get('impact_level') == 'critico')
            high_impact_fields = sum(1 for f in fields if f.get('impact_level') == 'alto')
            medium_impact_fields = sum(1 for f in fields if f.get('impact_level') == 'medio')
            low_impact_fields = sum(1 for f in fields if f.get('impact_level') == 'baixo')
            
            # Detalhes dos campos críticos
            critical_details = [
                {
                    'field_name': f.get('field_name'),
                    'file_path': f.get('file_path'),
                    'line_number': f.get('line_number'),
                    'field_type': f.get('field_type'),
                    'field_size': f.get('field_size'),
                    'action_needed': f.get('action_needed')
                }
                for f in fields if f.get('impact_level') == 'critico'
            ]
            
            # Determinar se precisa atenção
            needs_attention = critical_fields > 0 or high_impact_fields > 0
            
            return ProjectSummary(
                name=project_name,
                path=str(project_path),
                type=data.get('project_type', 'unknown'),
                total_fields=len(fields),
                critical_fields=critical_fields,
                high_impact_fields=high_impact_fields,
                medium_impact_fields=medium_impact_fields,
                low_impact_fields=low_impact_fields,
                overall_impact=data.get('overall_impact', 'unknown'),
                needs_attention=needs_attention,
                categories=data.get('categories', {}),
                critical_details=critical_details
            )
            
        except Exception as e:
            print(f"⚠️ Erro ao processar relatório de {project_name}: {e}")
            return None
    
    def _project_to_dict(self, project: ProjectSummary) -> Dict[str, Any]:
        """Converte ProjectSummary para dicionário"""
        return {
            'name': project.name,
            'path': project.path,
            'type': project.type,
            'total_fields': project.total_fields,
            'critical_fields': project.critical_fields,
            'high_impact_fields': project.high_impact_fields,
            'medium_impact_fields': project.medium_impact_fields,
            'low_impact_fields': project.low_impact_fields,
            'overall_impact': project.overall_impact,
            'needs_attention': project.needs_attention,
            'categories': project.categories,
            'critical_details': project.critical_details
        }
    
    def _calculate_statistics(self, projects: List[ProjectSummary]) -> Dict[str, Any]:
        """Calcula estatísticas gerais"""
        if not projects:
            return {}
        
        total_critical = sum(p.critical_fields for p in projects)
        total_high = sum(p.high_impact_fields for p in projects)
        total_medium = sum(p.medium_impact_fields for p in projects)
        total_low = sum(p.low_impact_fields for p in projects)
        total_fields = sum(p.total_fields for p in projects)
        
        # Contar por tipo de projeto
        project_types = {}
        for p in projects:
            project_type = p.type
            if project_type not in project_types:
                project_types[project_type] = {
                    'count': 0,
                    'critical_fields': 0,
                    'high_impact_fields': 0
                }
            project_types[project_type]['count'] += 1
            project_types[project_type]['critical_fields'] += p.critical_fields
            project_types[project_type]['high_impact_fields'] += p.high_impact_fields
        
        return {
            'total_fields': total_fields,
            'total_critical_fields': total_critical,
            'total_high_impact_fields': total_high,
            'total_medium_impact_fields': total_medium,
            'total_low_impact_fields': total_low,
            'projects_with_critical_fields': len([p for p in projects if p.critical_fields > 0]),
            'projects_with_high_impact_fields': len([p for p in projects if p.high_impact_fields > 0]),
            'projects_needing_attention': len([p for p in projects if p.needs_attention]),
            'project_types': project_types
        }
    
    def generate_markdown_report(self, analysis_data: Dict[str, Any], output_file: str = None) -> str:
        """Gera relatório Markdown"""
        if output_file is None:
            output_file = self.reports_dir / "general_analysis.md"
        
        markdown = self._generate_markdown_content(analysis_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        return str(output_file)
    
    def _generate_markdown_content(self, data: Dict[str, Any]) -> str:
        """Gera conteúdo Markdown"""
        stats = data.get('statistics', {})
        critical_projects = data.get('critical_projects_details', [])
        
        markdown = f"""# Relatório Geral de Análise CNPJ Alfanumérico

## 📋 RESUMO EXECUTIVO

### Informações Gerais
- **Data da Análise**: {data.get('analysis_date', 'N/A')}
- **Pasta Analisada**: {data.get('projects_folder', 'N/A')}
- **Total de Projetos**: {data.get('total_projects', 0)}
- **Projetos com Pontos Críticos**: {data.get('critical_projects', 0)}

### Estatísticas Gerais
- **Total de Campos CNPJ**: {stats.get('total_fields', 0)}
- **Campos Críticos**: {stats.get('total_critical_fields', 0)}
- **Campos de Alto Impacto**: {stats.get('total_high_impact_fields', 0)}
- **Projetos que Precisam Atenção**: {stats.get('projects_needing_attention', 0)}

### Distribuição por Tipo de Projeto
"""
        
        # Adicionar estatísticas por tipo
        project_types = stats.get('project_types', {})
        for project_type, type_stats in project_types.items():
            markdown += f"- **{project_type}**: {type_stats['count']} projetos, {type_stats['critical_fields']} campos críticos, {type_stats['high_impact_fields']} campos de alto impacto\n"
        
        if critical_projects:
            markdown += f"""
## 🚨 PROJETOS QUE PRECISAM ATENÇÃO

### Projetos com Campos Críticos
"""
            
            for project in critical_projects:
                markdown += f"""
#### 📁 {project['name']} ({project['type']})
- **Campos Críticos**: {project['critical_fields']}
- **Campos de Alto Impacto**: {project['high_impact_fields']}
- **Total de Campos**: {project['total_fields']}
- **Impacto Geral**: {project['overall_impact']}

**Campos Críticos Encontrados:**
"""
                
                for detail in project['critical_details']:
                    markdown += f"- **{detail['field_name']}** ({detail['field_type']}{f'({detail['field_size']})' if detail['field_size'] else ''}) - {detail['action_needed']}\n"
                    markdown += f"  - Arquivo: {detail['file_path']}:{detail['line_number']}\n"
        else:
            markdown += "\n## ✅ NENHUM PROJETO COM CAMPOS CRÍTICOS\n\nTodos os projetos estão em conformidade ou precisam apenas de ajustes menores."
        
        markdown += f"""
## 📊 RESUMO COMPLETO DE TODOS OS PROJETOS

| Projeto | Tipo | Total | Crítico | Alto | Médio | Baixo | Precisa Atenção |
|---------|------|-------|---------|------|-------|-------|-----------------|
"""
        
        all_projects = data.get('all_projects_summary', [])
        for project in all_projects:
            attention = "🔴 SIM" if project['needs_attention'] else "🟢 NÃO"
            markdown += f"| {project['name']} | {project['type']} | {project['total_fields']} | {project['critical_fields']} | {project['high_impact_fields']} | {project['medium_impact_fields']} | {project['low_impact_fields']} | {attention} |\n"
        
        return markdown
