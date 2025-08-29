"""
Analisador de Migrations PHP
Versão: 1.0
Data: 2025-08-28
"""

import re
from typing import List, Optional
from dataclasses import dataclass


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
