"""
Factory para Analisadores - Gerencia diferentes tipos de analisadores
Versão: 2.0
Data: 2025-08-28
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from analyzers import (
    BaseAnalyzer,
    PHPAnalyzer,
    UIAnalyzer,
    NestAnalyzer,
    ETLAnalyzer
)

class AnalyzerFactory:
    """Factory para criar analisadores específicos por tipo de projeto"""
    
    def __init__(self):
        self.analyzers = {
            # PHP Projects
            'php_laravel': lambda: PHPAnalyzer('laravel'),
            'php_symfony': lambda: PHPAnalyzer('symfony'),
            'php_hyperf': lambda: PHPAnalyzer('hyperf'),
            'php_generic': lambda: PHPAnalyzer('php'),
            
            # UI Projects
            'ui_react': lambda: UIAnalyzer('react'),
            'ui_react_native': lambda: UIAnalyzer('react_native'),
            'ui_vue': lambda: UIAnalyzer('vue'),
            'ui_angular': lambda: UIAnalyzer('angular'),
            'ui_generic': lambda: UIAnalyzer('ui'),
            
            # NestJS Projects
            'nest_bff': lambda: NestAnalyzer(),
            'nest_generic': lambda: NestAnalyzer(),
            
            # ETL Projects
            'etl_pentaho': lambda: ETLAnalyzer(),
            'etl_sql': lambda: ETLAnalyzer(),
            'etl_python_pandas': lambda: ETLAnalyzer(),
            'etl_python_spark': lambda: ETLAnalyzer(),
            'etl_python_airflow': lambda: ETLAnalyzer(),
            'etl_r': lambda: ETLAnalyzer(),
            'etl_scala_java': lambda: ETLAnalyzer(),
            'etl_generic': lambda: ETLAnalyzer()
        }

    def create_analyzer(self, project_type: str) -> BaseAnalyzer:
        """Cria um analisador baseado no tipo de projeto"""
        if project_type in self.analyzers:
            return self.analyzers[project_type]()
        else:
            # Fallback para analisador genérico baseado no prefixo
            if project_type.startswith('php'):
                return PHPAnalyzer('php')
            elif project_type.startswith('ui'):
                return UIAnalyzer('ui')
            elif project_type.startswith('nest'):
                return NestAnalyzer()
            elif project_type.startswith('etl'):
                return ETLAnalyzer()
            else:
                return PHPAnalyzer('php')

    def detect_project_type(self, project_path: Path) -> str:
        """Detecta automaticamente o tipo de projeto"""
        if not project_path.exists():
            return 'unknown'
        
        # Verificar composer.json (PHP)
        composer_path = project_path / 'composer.json'
        if composer_path.exists():
            try:
                with open(composer_path, 'r', encoding='utf-8') as f:
                    composer_data = json.load(f)
                
                dependencies = composer_data.get('require', {})
                dev_dependencies = composer_data.get('require-dev', {})
                all_deps = {**dependencies, **dev_dependencies}
                
                # Detectar Laravel
                if 'laravel/framework' in all_deps:
                    return 'php_laravel'
                # Detectar Symfony (prioridade sobre Laravel components)
                elif any('symfony' in dep.lower() for dep in all_deps.keys()):
                    return 'php_symfony'
                # Detectar Hyperf
                elif any('hyperf' in dep for dep in all_deps.keys()):
                    return 'php_hyperf'
                else:
                    return 'php_generic'
            except (json.JSONDecodeError, FileNotFoundError):
                return 'php_generic'
        
        # Verificar package.json (Node.js)
        package_path = project_path / 'package.json'
        if package_path.exists():
            try:
                with open(package_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                dependencies = package_data.get('dependencies', {})
                dev_dependencies = package_data.get('devDependencies', {})
                all_deps = {**dependencies, **dev_dependencies}
                scripts = package_data.get('scripts', {})
                
                # Detectar React Native
                if any('react-native' in dep for dep in all_deps.keys()):
                    return 'ui_react_native'
                # Detectar NestJS
                elif any('@nestjs' in dep for dep in all_deps.keys()):
                    return 'nest_bff'
                # Detectar React
                elif any('react' in dep for dep in all_deps.keys()):
                    return 'ui_react'
                # Detectar Vue
                elif any('vue' in dep for dep in all_deps.keys()):
                    return 'ui_vue'
                # Detectar Angular
                elif any('@angular' in dep for dep in all_deps.keys()):
                    return 'ui_angular'
                # Verificar scripts para detecção adicional
                elif any('react-native' in str(v).lower() for v in scripts.values()):
                    return 'ui_react_native'
                elif any('nest' in str(v).lower() for v in scripts.values()):
                    return 'nest_bff'
                elif any('react' in str(v).lower() for v in scripts.values()):
                    return 'ui_react'
                elif any('vue' in str(v).lower() for v in scripts.values()):
                    return 'ui_vue'
                elif any('angular' in str(v).lower() for v in scripts.values()):
                    return 'ui_angular'
                else:
                    return 'ui_generic'
            except (json.JSONDecodeError, FileNotFoundError):
                return 'ui_generic'
        
        # Verificar arquivos ETL
        if self._is_etl_project(project_path):
            return self._detect_etl_type(project_path)
        
        return 'unknown'

    def _is_etl_project(self, project_path: Path) -> bool:
        """Verifica se o projeto é um projeto ETL"""
        etl_extensions = ['.ktr', '.kjb', '.sql', '.py', '.r', '.scala', '.java']
        etl_files = []
        
        for ext in etl_extensions:
            etl_files.extend(project_path.rglob(f'*{ext}'))
        
        return len(etl_files) > 0

    def _detect_etl_type(self, project_path: Path) -> str:
        """Detecta o tipo específico de projeto ETL"""
        # Verificar arquivos Pentaho
        if any(project_path.rglob('*.ktr')) or any(project_path.rglob('*.kjb')):
            return 'etl_pentaho'
        
        # Verificar arquivos SQL
        if any(project_path.rglob('*.sql')):
            return 'etl_sql'
        
        # Verificar arquivos Python ETL
        python_files = list(project_path.rglob('*.py'))
        if python_files:
            for py_file in python_files[:5]:  # Verificar apenas os primeiros 5 arquivos
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if any(pattern in content for pattern in ['pyspark', 'SparkSession']):
                            return 'etl_python_spark'
                        elif any(pattern in content for pattern in ['airflow', 'DAG']):
                            return 'etl_python_airflow'
                        elif any(pattern in content for pattern in ['pandas', 'pd.', 'df.']):
                            return 'etl_python_pandas'
                except Exception:
                    continue
        
        # Verificar arquivos R
        if any(project_path.rglob('*.r')) or any(project_path.rglob('*.R')):
            return 'etl_r'
        
        # Verificar arquivos Scala/Java
        if any(project_path.rglob('*.scala')) or any(project_path.rglob('*.java')):
            return 'etl_scala_java'
        
        return 'etl_generic'

    def analyze_project(self, project_path: Path, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analisa um projeto usando o analisador apropriado"""
        project_type = self.detect_project_type(project_path)
        analyzer = self.create_analyzer(project_type)
        
        # Analisar o projeto
        result = analyzer.analyze_project(project_path, filters)
        
        # Adicionar informações do factory
        result['project_name'] = project_path.name
        result['project_path'] = str(project_path)
        result['project_type'] = project_type
        
        return result

    def get_supported_types(self) -> Dict[str, str]:
        """Retorna os tipos de projeto suportados"""
        return {
            # PHP
            'php_laravel': 'Laravel Framework',
            'php_symfony': 'Symfony Framework',
            'php_hyperf': 'Hyperf Framework',
            'php_generic': 'PHP Genérico',
            
            # UI
            'ui_react': 'React',
            'ui_react_native': 'React Native',
            'ui_vue': 'Vue.js',
            'ui_angular': 'Angular',
            'ui_generic': 'UI Genérico',
            
            # NestJS
            'nest_bff': 'NestJS BFF',
            'nest_generic': 'NestJS Genérico',
            
            # ETL
            'etl_pentaho': 'Pentaho Spoon',
            'etl_sql': 'SQL Scripts',
            'etl_python_pandas': 'Python Pandas',
            'etl_python_spark': 'Python Spark',
            'etl_python_airflow': 'Python Airflow',
            'etl_r': 'R Scripts',
            'etl_scala_java': 'Scala/Java',
            'etl_generic': 'ETL Genérico'
        }

    def get_analyzer_info(self, project_type: str) -> Dict[str, Any]:
        """Retorna informações sobre um analisador específico"""
        analyzer = self.create_analyzer(project_type)
        supported_types = self.get_supported_types()
        
        return {
            'project_type': project_type,
            'display_name': supported_types.get(project_type, 'Desconhecido'),
            'analyzer_class': analyzer.__class__.__name__,
            'supported_extensions': analyzer.get_file_extensions(),
            'skip_patterns': analyzer.get_skip_patterns()
        }
