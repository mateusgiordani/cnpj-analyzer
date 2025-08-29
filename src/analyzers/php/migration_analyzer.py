"""
Analisador de Migrations PHP - Orquestrador
Versão: 2.0
Data: 2025-08-28
"""

import re
from typing import List, Optional
from dataclasses import dataclass

from .migrations import (
    PhinxMigrationAnalyzer,
    LaravelMigrationAnalyzer,
    GenericMigrationAnalyzer
)


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
    """Orquestrador de analisadores específicos para migrations PHP"""
    
    def __init__(self):
        self.phinx_analyzer = PhinxMigrationAnalyzer()
        self.laravel_analyzer = LaravelMigrationAnalyzer()
        self.generic_analyzer = GenericMigrationAnalyzer()
    
    def analyze_migration_file(self, file_path: str, content: str) -> List[PHPFieldDefinition]:
        """Analisa um arquivo de migration usando o analisador apropriado"""
        migration_type = self._detect_migration_type(file_path, content)
        
        if migration_type == 'phinx':
            return self.phinx_analyzer.analyze_migration_file(file_path, content)
        elif migration_type == 'laravel':
            return self.laravel_analyzer.analyze_migration_file(file_path, content)
        else:
            return self.generic_analyzer.analyze_migration_file(file_path, content)
    
    def _detect_migration_type(self, file_path: str, content: str) -> str:
        """Detecta o tipo de migration baseado no conteúdo"""
        content_lower = content.lower()
        
        # Detectar Phinx
        if any(pattern in content_lower for pattern in [
            '$table->addcolumn',
            '$table->removecolumn',
            '$table->changecolumn',
            'robmorgan\\phinx',
            'phinx'
        ]):
            return 'phinx'
        
        # Detectar Laravel
        if any(pattern in content_lower for pattern in [
            '$table->string(',
            '$table->char(',
            '$table->text(',
            '$table->integer(',
            'schema::create',
            'schema::drop',
            'laravel'
        ]):
            return 'laravel'
        
        # Detectar Hyperf (similar ao Laravel)
        if any(pattern in content_lower for pattern in [
            'hyperf',
            '@column',
            'doctrine'
        ]):
            return 'laravel'  # Usar analisador Laravel para Hyperf
        
        # Padrão genérico
        return 'generic'
