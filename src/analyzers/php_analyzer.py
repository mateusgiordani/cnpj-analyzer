"""
Analisador Principal PHP
Versão: 2.0
Data: 2025-08-28
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base_analyzer import BaseAnalyzer, CNPJField, ImpactLevel, Status
from .php import (
    PHPMigrationAnalyzer,
    PHPCodeAnalyzer,
    PHPValidationAnalyzer,
    PHPTestAnalyzer,
    PHPFieldDefinition
)


class PHPAnalyzer(BaseAnalyzer):
    """Analisador principal para projetos PHP"""
    
    def __init__(self, project_path: Path):
        super().__init__('php')
        self.project_path = project_path
        
        # Inicializar analisadores especializados
        self.migration_analyzer = PHPMigrationAnalyzer()
        self.code_analyzer = PHPCodeAnalyzer()
        self.validation_analyzer = PHPValidationAnalyzer()
        self.test_analyzer = PHPTestAnalyzer()
    
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
        
        # Analisar cada categoria usando analisadores especializados
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
        """Analisa arquivos de migration usando o analisador especializado"""
        fields = []
        for file_path, content in migration_files:
            fields.extend(self.migration_analyzer.analyze_migration_file(file_path, content))
        return fields
    
    def _analyze_code(self, code_files: List[tuple]) -> List[PHPFieldDefinition]:
        """Analisa arquivos de código usando o analisador especializado"""
        fields = []
        for file_path, content in code_files:
            fields.extend(self.code_analyzer.analyze_code_file(file_path, content))
        return fields
    
    def _analyze_validations(self, validation_files: List[tuple]) -> List[PHPFieldDefinition]:
        """Analisa arquivos de validação usando o analisador especializado"""
        fields = []
        for file_path, content in validation_files:
            fields.extend(self.validation_analyzer.analyze_validation_file(file_path, content))
        return fields
    
    def _analyze_tests(self, test_files: List[tuple]) -> List[PHPFieldDefinition]:
        """Analisa arquivos de teste usando o analisador especializado"""
        fields = []
        for file_path, content in test_files:
            fields.extend(self.test_analyzer.analyze_test_file(file_path, content))
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
    
    def _assess_impact(self, field_type: str, field_size: Optional[int]) -> tuple:
        """Avalia o impacto de um campo baseado no tipo e tamanho"""
        if field_type == 'UNKNOWN':
            return ImpactLevel.MEDIUM, Status.NEEDS_ANALYSIS, 'Análise manual necessária'
        
        if field_type in ['VARCHAR', 'CHAR']:
            if field_size is None:
                return ImpactLevel.LOW, Status.COMPATIBLE, 'Campo sem tamanho definido é compatível'
            elif field_size < 14:
                return ImpactLevel.CRITICAL, Status.INCOMPATIBLE, f'CRÍTICO: Tamanho {field_size} < 14. Alterar para VARCHAR(18)'
            elif field_size == 14:
                return ImpactLevel.LOW, Status.COMPATIBLE, 'Tamanho 14 é compatível com CNPJ atual'
            elif field_size < 18:
                return ImpactLevel.MEDIUM, Status.ATTENTION, f'Aumentar tamanho de {field_size} para 18 para CNPJ alfanumérico'
            else:
                return ImpactLevel.LOW, Status.COMPATIBLE, 'Tamanho adequado para CNPJ alfanumérico'
        
        elif field_type in ['TEXT']:
            return ImpactLevel.LOW, Status.COMPATIBLE, 'Campo TEXT é compatível'
        
        elif field_type in ['INTEGER', 'BIGINT']:
            return ImpactLevel.HIGH, Status.INCOMPATIBLE, 'Campo numérico precisa ser alterado para VARCHAR(18)'
        
        else:
            return ImpactLevel.MEDIUM, Status.NEEDS_ANALYSIS, 'Verificar compatibilidade do tipo'
    
    def _estimate_effort(self, impact_level: ImpactLevel) -> str:
        """Estima o esforço baseado no nível de impacto"""
        if impact_level == ImpactLevel.CRITICAL:
            return '8-16 horas'
        elif impact_level == ImpactLevel.HIGH:
            return '4-8 horas'
        elif impact_level == ImpactLevel.MEDIUM:
            return '2-4 horas'
        else:
            return '1-2 horas'
    
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
