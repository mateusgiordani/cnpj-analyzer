"""
Analisador PHP - Laravel, Symfony, Hyperf
Versão: 1.0
Data: 2025-01-27
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from analyzers.base_analyzer import BaseAnalyzer, CNPJField, ImpactLevel, Status

class PHPAnalyzer(BaseAnalyzer):
    """Analisador específico para projetos PHP"""
    
    def __init__(self, framework: str = "php"):
        super().__init__(f"php_{framework}")
        self.framework = framework
        
        # Padrões específicos para PHP
        self.php_patterns = {
            'laravel': {
                'migration_patterns': [
                    r'public\s+function\s+up\s*\(\s*\)',
                    r'Schema::create\s*\(\s*[\'"]([^\'"]+)[\'"]',
                    r'\$table->string\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(\d+)\s*\)',
                    r'\$table->integer\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
                ],
                'model_patterns': [
                    r'protected\s+\$fillable\s*=\s*\[',
                    r'protected\s+\$casts\s*=\s*\[',
                    r'public\s+function\s+([a-zA-Z_]+)\s*\(\s*\)'
                ],
                'validation_patterns': [
                    r'Rule::cnpj\s*\(\s*\)',
                    r'cnpj\s*[,|]',
                    r'validat.*cnpj',
                    r'cnpj.*validat'
                ]
            },
            'symfony': {
                'entity_patterns': [
                    r'@ORM\\Column\s*\(\s*type\s*=\s*[\'"]([^\'"]+)[\'"]',
                    r'@Assert\\Regex\s*\(\s*pattern\s*=\s*[\'"]([^\'"]+)[\'"]',
                    r'private\s+\$([a-zA-Z_]+)\s*:'
                ],
                'validation_patterns': [
                    r'@Assert\\Regex',
                    r'@Assert\\Length',
                    r'cnpj.*constraint'
                ]
            },
            'hyperf': {
                'model_patterns': [
                    r'@Column\s*\(\s*type\s*=\s*[\'"]([^\'"]+)[\'"]',
                    r'protected\s+\$([a-zA-Z_]+)\s*;',
                    r'public\s+function\s+([a-zA-Z_]+)\s*\(\s*\)'
                ],
                'validation_patterns': [
                    r'@Validator\s*\(\s*[\'"]([^\'"]+)[\'"]',
                    r'cnpj.*rule',
                    r'rule.*cnpj'
                ]
            }
        }

    def get_file_extensions(self) -> List[str]:
        """Retorna as extensões de arquivo suportadas"""
        return ['.php', '.sql', '.yml', '.yaml']

    def get_skip_patterns(self) -> List[str]:
        """Retorna padrões de arquivos/pastas para ignorar"""
        return [
            'vendor', 'node_modules', '.git', '__pycache__', 
            '.venv', 'venv', 'dist', 'build', '.next', '.nuxt',
            'storage', 'bootstrap/cache', 'public/build'
        ]

    def scan_database_files(self, project_path: Path) -> List[Dict]:
        """Escaneia arquivos específicos de banco de dados"""
        database_files = []
        
        # Buscar arquivos de migração
        migration_patterns = [
            'database/migrations/*.php',
            'migrations/*.php',
            'db/migrations/*.php',
            'src/Migration/*.php',
            '**/migrations/*.php',
            '**/Migrations/*.php'
        ]
        
        for pattern in migration_patterns:
            for file_path in project_path.rglob(pattern):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        database_files.append({
                            'file_path': str(file_path),
                            'content': content,
                            'type': 'migration'
                        })
                        self.logger.info(f"Migração encontrada: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Erro ao ler migração {file_path}: {e}")
        
        # Buscar arquivos que contenham "migration" no nome
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and 'migration' in file_path.name.lower() and file_path.suffix == '.php':
                if str(file_path) not in [f['file_path'] for f in database_files]:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        database_files.append({
                            'file_path': str(file_path),
                            'content': content,
                            'type': 'migration'
                        })
                        self.logger.info(f"Migração por nome encontrada: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Erro ao ler migração {file_path}: {e}")
        
        # Buscar arquivos SQL
        for file_path in project_path.rglob('*.sql'):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    database_files.append({
                        'file_path': str(file_path),
                        'content': content,
                        'type': 'sql'
                    })
                except Exception as e:
                    self.logger.warning(f"Erro ao ler SQL {file_path}: {e}")
        
        return database_files

    def find_php_specific_patterns(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Encontra padrões específicos do PHP"""
        patterns = self.php_patterns.get(self.framework, {})
        results = {}
        
        for pattern_type, pattern_list in patterns.items():
            results[pattern_type] = []
            
            for file_info in files:
                file_path = file_info['file_path']
                content = file_info['content']
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in pattern_list:
                        if re.search(pattern, line, re.IGNORECASE):
                            results[pattern_type].append({
                                'file_path': file_path,
                                'line_number': line_num,
                                'line': line.strip(),
                                'pattern_type': pattern_type
                            })
        
        return results

    def find_laravel_specific(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Encontra padrões específicos do Laravel"""
        if self.framework != 'laravel':
            return {}
        
        laravel_patterns = {
            'models': [],
            'controllers': [],
            'requests': [],
            'resources': []
        }
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            
            # Detectar tipos de arquivo Laravel
            if 'app/Models/' in file_path or 'app/Model/' in file_path:
                laravel_patterns['models'].append({
                    'file_path': file_path,
                    'content': content
                })
            elif 'app/Http/Controllers/' in file_path:
                laravel_patterns['controllers'].append({
                    'file_path': file_path,
                    'content': content
                })
            elif 'app/Http/Requests/' in file_path:
                laravel_patterns['requests'].append({
                    'file_path': file_path,
                    'content': content
                })
            elif 'app/Http/Resources/' in file_path:
                laravel_patterns['resources'].append({
                    'file_path': file_path,
                    'content': content
                })
        
        return laravel_patterns

    def find_symfony_specific(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Encontra padrões específicos do Symfony"""
        if self.framework != 'symfony':
            return {}
        
        symfony_patterns = {
            'entities': [],
            'controllers': [],
            'forms': [],
            'validators': []
        }
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            
            # Detectar tipos de arquivo Symfony
            if 'Entity/' in file_path or 'entity/' in file_path:
                symfony_patterns['entities'].append({
                    'file_path': file_path,
                    'content': content
                })
            elif 'Controller/' in file_path or 'controller/' in file_path:
                symfony_patterns['controllers'].append({
                    'file_path': file_path,
                    'content': content
                })
            elif 'Form/' in file_path or 'form/' in file_path:
                symfony_patterns['forms'].append({
                    'file_path': file_path,
                    'content': content
                })
            elif 'Validator/' in file_path or 'validator/' in file_path:
                symfony_patterns['validators'].append({
                    'file_path': file_path,
                    'content': content
                })
        
        return symfony_patterns

    def find_hyperf_specific(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Encontra padrões específicos do Hyperf"""
        if self.framework != 'hyperf':
            return {}
        
        hyperf_patterns = {
            'models': [],
            'controllers': [],
            'validators': [],
            'middleware': []
        }
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            
            # Detectar tipos de arquivo Hyperf
            if 'Model/' in file_path or 'model/' in file_path:
                hyperf_patterns['models'].append({
                    'file_path': file_path,
                    'content': content
                })
            elif 'Controller/' in file_path or 'controller/' in file_path:
                hyperf_patterns['controllers'].append({
                    'file_path': file_path,
                    'content': content
                })
            elif 'Validator/' in file_path or 'validator/' in file_path:
                hyperf_patterns['validators'].append({
                    'file_path': file_path,
                    'content': content
                })
            elif 'Middleware/' in file_path or 'middleware/' in file_path:
                hyperf_patterns['middleware'].append({
                    'file_path': file_path,
                    'content': content
                })
        
        return hyperf_patterns

    def analyze_project(self, project_path: Path, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Analisa um projeto PHP e retorna os resultados"""
        project_name = project_path.name if hasattr(project_path, 'name') else str(project_path).split('/')[-1]
        self.console.print(f"[blue]Analisando projeto PHP ({self.framework}): {project_name}[/blue]")
        
        # Escanear arquivos gerais com filtros
        files = self.scan_files(project_path, filters)
        
        # Escanear arquivos de banco
        database_files = self.scan_database_files(project_path)
        
        # Encontrar campos CNPJ
        cnpj_fields = self.find_cnpj_fields(files + database_files)
        
        # Encontrar validações
        validations = self.find_validations(files)
        
        # Encontrar máscaras
        masks = self.find_frontend_masks(files)
        
        # Encontrar padrões específicos do framework
        framework_specific = {}
        if self.framework == 'laravel':
            framework_specific = self.find_laravel_specific(files)
        elif self.framework == 'symfony':
            framework_specific = self.find_symfony_specific(files)
        elif self.framework == 'hyperf':
            framework_specific = self.find_hyperf_specific(files)
        
        # Encontrar padrões PHP específicos
        php_patterns = self.find_php_specific_patterns(files)
        
        return {
            'project_type': self.project_type,
            'framework': self.framework,
            'total_files_scanned': len(files),
            'database_files_scanned': len(database_files),
            'cnpj_fields_found': cnpj_fields,
            'validations': validations,
            'frontend_masks': masks,
            'framework_specific': framework_specific,
            'php_patterns': php_patterns,
            'files': files,
            'database_files': database_files
        }
