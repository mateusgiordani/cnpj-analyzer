"""
Analisador PHP - Laravel, Symfony, Hyperf
Versão: 1.0
Data: 2025-01-27
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base_analyzer import BaseAnalyzer, CNPJField, ImpactLevel, Status


@dataclass
class PHPFieldDefinition:
    """Representa uma definição de campo PHP encontrada"""
    file_path: str
    line_number: int
    field_name: str
    field_type: str
    field_size: Optional[int]
    context: str
    category: str  # 'migration', 'model', 'validation', 'test'


class PHPMigrationAnalyzer:
    """Analisador específico para migrations PHP (Phinx, Laravel, Hyperf)"""
    
    def __init__(self):
        self.migration_patterns = {
            'phinx': {
                'field_definition': r'\$table->addColumn\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]([^)]*)\)',
                'laravel_field': r'\$table->(\w+)\s*\(\s*[\'"]([^\'"]+)[\'"]([^)]*)\)',
                'index_reference': r'[\'"]([^\'"]+)[\'"]\s*[,\]]',  # Para detectar referências em índices
            }
        }
    
    def analyze_migration_file(self, file_path: str, content: str) -> List[PHPFieldDefinition]:
        """Analisa um arquivo de migration e retorna apenas definições de campos"""
        fields = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Pular linhas que são apenas referências em índices
            if self._is_index_reference(line):
                continue
                
            # Buscar definições de campos Phinx
            phinx_match = re.search(self.migration_patterns['phinx']['field_definition'], line)
            if phinx_match:
                field_name = phinx_match.group(1)
                field_type = phinx_match.group(2)
                options = phinx_match.group(3)
                
                if self._is_cnpj_field(field_name):
                    field_size = self._extract_field_size(options)
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type=field_type,
                        field_size=field_size,
                        context=line.strip(),
                        category='migration'
                    ))
                continue
            
            # Buscar definições de campos Laravel
            laravel_match = re.search(self.migration_patterns['phinx']['laravel_field'], line)
            if laravel_match:
                method = laravel_match.group(1)
                field_name = laravel_match.group(2)
                options = laravel_match.group(3)
                
                if self._is_cnpj_field(field_name):
                    field_size = self._extract_field_size(options)
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type=method,
                        field_size=field_size,
                        context=line.strip(),
                        category='migration'
                    ))
        
        return fields
    
    def _is_index_reference(self, line: str) -> bool:
        """Verifica se a linha é apenas uma referência em índice"""
        # Padrões que indicam referência em índice
        index_patterns = [
            r'addIndex\s*\(',
            r'addUnique\s*\(',
            r'addForeignKey\s*\(',
            r'index\s*\(',
            r'unique\s*\(',
        ]
        
        for pattern in index_patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def _is_cnpj_field(self, field_name: str) -> bool:
        """Verifica se o campo é relacionado a CNPJ"""
        cnpj_patterns = [
            r'cnpj',
            r'cpf_cnpj',
            r'cpfcnpj',
            r'cpfCnpj',
            r'cpfcnpj',
            r'cnpj_cpf',
            r'cnpjcpf',
        ]
        
        field_lower = field_name.lower()
        return any(re.search(pattern, field_lower) for pattern in cnpj_patterns)
    
    def _extract_field_size(self, options: str) -> Optional[int]:
        """Extrai o tamanho do campo das opções"""
        # Buscar 'length' => X
        length_match = re.search(r"'length'\s*=>\s*(\d+)", options)
        if length_match:
            return int(length_match.group(1))
        
        # Buscar length como segundo parâmetro (Laravel)
        length_match = re.search(r',\s*(\d+)', options)
        if length_match:
            return int(length_match.group(1))
        
        return None


class PHPCodeAnalyzer:
    """Analisador para código PHP (models, services, etc.)"""
    
    def __init__(self):
        self.code_patterns = {
            'property': r'(?:public|private|protected)\s+\$(\w+)',
            'variable': r'\$(\w+)\s*=',
            'parameter': r'function\s+\w+\s*\([^)]*\$(\w+)[^)]*\)',
        }
    
    def analyze_code_file(self, file_path: str, content: str) -> List[PHPFieldDefinition]:
        """Analisa um arquivo de código PHP"""
        fields = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Buscar propriedades de classe
            prop_match = re.search(self.code_patterns['property'], line)
            if prop_match:
                field_name = prop_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='PROPERTY',
                        field_size=None,
                        context=line.strip(),
                        category='code'
                    ))
                continue
            
            # Buscar variáveis
            var_match = re.search(self.code_patterns['variable'], line)
            if var_match:
                field_name = var_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='VARIABLE',
                        field_size=None,
                        context=line.strip(),
                        category='code'
                    ))
        
        return fields
    
    def _is_cnpj_field(self, field_name: str) -> bool:
        """Verifica se o campo é relacionado a CNPJ"""
        cnpj_patterns = [
            r'cnpj',
            r'cpf_cnpj',
            r'cpfcnpj',
            r'cpfCnpj',
            r'cpfcnpj',
            r'cnpj_cpf',
            r'cnpjcpf',
        ]
        
        field_lower = field_name.lower()
        return any(re.search(pattern, field_lower) for pattern in cnpj_patterns)


class PHPValidationAnalyzer:
    """Analisador para validações PHP"""
    
    def __init__(self):
        self.validation_patterns = {
            'rule': r'[\'"]([^\'"]*cnpj[^\'"]*)[\'"]',
            'validator': r'CNPJ|Cnpj',
            'validation_method': r'validateCnpj|validate_cnpj',
        }
    
    def analyze_validation_file(self, file_path: str, content: str) -> List[PHPFieldDefinition]:
        """Analisa um arquivo de validação PHP"""
        fields = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Buscar regras de validação
            rule_match = re.search(self.validation_patterns['rule'], line, re.IGNORECASE)
            if rule_match:
                rule = rule_match.group(1)
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"validation_rule_{line_num}",
                    field_type='VALIDATION_RULE',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
                continue
            
            # Buscar validadores
            validator_match = re.search(self.validation_patterns['validator'], line)
            if validator_match:
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"validator_{line_num}",
                    field_type='VALIDATOR',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
        
        return fields


class PHPAnalyzer(BaseAnalyzer):
    """Analisador principal para projetos PHP"""
    
    def __init__(self, project_path: Path):
        super().__init__('php')
        self.project_path = project_path
        self.migration_analyzer = PHPMigrationAnalyzer()
        self.code_analyzer = PHPCodeAnalyzer()
        self.validation_analyzer = PHPValidationAnalyzer()
    
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
    
    def analyze_project(self, project_path: Path, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Analisa um projeto PHP"""
        print(f"🔍 Analisando projeto PHP: {project_path.name}")
        
        # Escanear arquivos
        scanned_files = self.scan_files(project_path)
        
        # Categorizar arquivos
        migration_files = []
        code_files = []
        validation_files = []
        test_files = []
        
        for file_info in scanned_files:
            file_path = file_info['file_path']
            content = file_info['content']
            
            if self._is_migration_file(file_path):
                migration_files.append((file_path, content))
            elif self._is_test_file(file_path):
                test_files.append((file_path, content))
            elif self._is_validation_file(file_path):
                validation_files.append((file_path, content))
            else:
                code_files.append((file_path, content))
        
        # Analisar cada categoria
        migration_fields = self._analyze_migrations(migration_files)
        code_fields = self._analyze_code(code_files)
        validation_fields = self._analyze_validations(validation_files)
        test_fields = self._analyze_tests(test_files)
        
        # Converter para CNPJField
        all_fields = []
        
        # Migrations
        for field in migration_fields:
            field_type, field_size = self._map_php_type_to_sql(field.field_type, field.field_size)
            impact_level, status, action_needed = self._assess_impact(field_type, field_size)
            
            all_fields.append(CNPJField(
                file_path=field.file_path,
                line_number=field.line_number,
                field_name=field.field_name,
                field_type=field_type,
                field_size=field_size,
                context=field.context,
                project_type='php_migration',
                impact_level=impact_level,
                status=status,
                action_needed=action_needed,
                estimated_effort=self._estimate_effort(impact_level)
            ))
        
        # Código
        for field in code_fields:
            all_fields.append(CNPJField(
                file_path=field.file_path,
                line_number=field.line_number,
                field_name=field.field_name,
                field_type=field.field_type,
                field_size=field.field_size,
                context=field.context,
                project_type='php_code',
                impact_level=ImpactLevel.MEDIUM,
                status=Status.NEEDS_ANALYSIS,
                action_needed='Revisar uso do campo CNPJ',
                estimated_effort='2-4 horas'
            ))
        
        # Validações
        for field in validation_fields:
            all_fields.append(CNPJField(
                file_path=field.file_path,
                line_number=field.line_number,
                field_name=field.field_name,
                field_type=field.field_type,
                field_size=field.field_size,
                context=field.context,
                project_type='php_validation',
                impact_level=ImpactLevel.HIGH,
                status=Status.NEEDS_ANALYSIS,
                action_needed='Atualizar validação para CNPJ alfanumérico',
                estimated_effort='4-8 horas'
            ))
        
        # Testes
        for field in test_fields:
            all_fields.append(CNPJField(
                file_path=field.file_path,
                line_number=field.line_number,
                field_name=field.field_name,
                field_type=field.field_type,
                field_size=field.field_size,
                context=field.context,
                project_type='php_test',
                impact_level=ImpactLevel.MEDIUM,
                status=Status.NEEDS_ANALYSIS,
                action_needed='Atualizar testes para CNPJ alfanumérico',
                estimated_effort='2-4 horas'
            ))
        
        # Determinar impacto geral
        if all_fields:
            if len(all_fields) > 10:
                overall_impact = ImpactLevel.HIGH
            elif len(all_fields) > 5:
                overall_impact = ImpactLevel.MEDIUM
            else:
                overall_impact = ImpactLevel.LOW
        else:
            overall_impact = ImpactLevel.NONE
        
        return {
            'project_name': project_path.name,
            'project_path': str(project_path),
            'project_type': 'php',
            'cnpj_fields_found': all_fields,
            'validations_found': [],
            'frontend_masks': [],
            'overall_impact': overall_impact.value if overall_impact else 'none',
            'files_scanned': len(scanned_files),
            'framework_detected': self._detect_framework(),
            'categories': {
                'migrations': len(migration_fields),
                'code': len(code_fields),
                'validations': len(validation_fields),
                'tests': len(test_fields),
            }
        }
    
    def _analyze_migrations(self, migration_files: List[tuple]) -> List[PHPFieldDefinition]:
        """Analisa arquivos de migration"""
        fields = []
        for file_path, content in migration_files:
            fields.extend(self.migration_analyzer.analyze_migration_file(file_path, content))
        return fields
    
    def _analyze_code(self, code_files: List[tuple]) -> List[PHPFieldDefinition]:
        """Analisa arquivos de código"""
        fields = []
        for file_path, content in code_files:
            fields.extend(self.code_analyzer.analyze_code_file(file_path, content))
        return fields
    
    def _analyze_validations(self, validation_files: List[tuple]) -> List[PHPFieldDefinition]:
        """Analisa arquivos de validação"""
        fields = []
        for file_path, content in validation_files:
            fields.extend(self.validation_analyzer.analyze_validation_file(file_path, content))
        return fields
    
    def _analyze_tests(self, test_files: List[tuple]) -> List[PHPFieldDefinition]:
        """Analisa arquivos de teste"""
        # Por enquanto, usar o mesmo analisador de código para testes
        fields = []
        for file_path, content in test_files:
            fields.extend(self.code_analyzer.analyze_code_file(file_path, content))
        return fields
    
    def _is_migration_file(self, file_path: str) -> bool:
        """Verifica se é um arquivo de migration"""
        return (
            'migration' in file_path.lower() or
            'db/migrations' in file_path or
            file_path.endswith('_migration.php') or
            re.search(r'\d{14}_.*\.php$', file_path)  # Padrão Laravel
        )
    
    def _is_test_file(self, file_path: str) -> bool:
        """Verifica se é um arquivo de teste"""
        return (
            'test' in file_path.lower() or
            'spec' in file_path.lower() or
            'tests/' in file_path or
            file_path.endswith('Test.php') or
            file_path.endswith('Spec.php')
        )
    
    def _is_validation_file(self, file_path: str) -> bool:
        """Verifica se é um arquivo de validação"""
        return (
            'validator' in file_path.lower() or
            'validation' in file_path.lower() or
            'rule' in file_path.lower() or
            'validate' in file_path.lower()
        )
    
    def _map_php_type_to_sql(self, php_type: str, size: Optional[int]) -> tuple:
        """Mapeia tipos PHP para tipos SQL"""
        php_type_lower = php_type.lower()
        
        if php_type_lower in ['string', 'varchar']:
            return 'VARCHAR', size
        elif php_type_lower in ['char']:
            return 'CHAR', size
        elif php_type_lower in ['text', 'longtext']:
            return 'TEXT', None
        elif php_type_lower in ['integer', 'int', 'bigint']:
            return 'INTEGER', None
        elif php_type_lower in ['decimal', 'float', 'double']:
            return 'DECIMAL', None
        else:
            return 'UNKNOWN', None
    
    def _detect_framework(self) -> str:
        """Detecta o framework PHP usado"""
        composer_path = Path(self.project_path) / 'composer.json'
        if composer_path.exists():
            try:
                with open(composer_path, 'r') as f:
                    composer_data = json.load(f)
                
                require = composer_data.get('require', {})
                require_dev = composer_data.get('require-dev', {})
                
                if 'laravel/framework' in require:
                    return 'laravel'
                elif 'symfony/symfony' in require or 'symfony/framework-bundle' in require:
                    return 'symfony'
                elif 'hyperf/hyperf' in require:
                    return 'hyperf'
                elif 'robmorgan/phinx' in require:
                    return 'phinx'
            except:
                pass
        
        return 'php_generic'
