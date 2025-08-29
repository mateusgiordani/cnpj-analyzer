"""
Analisador de Migrations Phinx
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


class PhinxMigrationAnalyzer:
    """Analisador específico para migrations Phinx"""
    
    def __init__(self):
        self.phinx_patterns = {
            'add_column': r'\$table->addColumn\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]([^)]*)\)',
            'remove_column': r'\$table->removeColumn\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            'change_column': r'\$table->changeColumn\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]([^)]*)\)',
            'rename_column': r'\$table->renameColumn\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)',
            'drop_table': r'\$table->drop\s*\(\s*\)',
            'create_table': r'\$table->create\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        }
    
    def analyze_migration_file(self, file_path: str, content: str) -> List[PHPFieldDefinition]:
        """Analisa um arquivo de migration Phinx e retorna apenas definições de campos"""
        fields = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Pular linhas que são apenas referências em índices
            if self._is_index_reference(line):
                continue
            
            # Pular operações de remoção de coluna
            if self._is_remove_column(line):
                continue
            
            # Pular operações de drop table
            if self._is_drop_table(line):
                continue
            
            # Buscar definições de campos (addColumn)
            add_column_match = re.search(self.phinx_patterns['add_column'], line)
            if add_column_match:
                field_name = add_column_match.group(1)
                field_type = add_column_match.group(2)
                options = add_column_match.group(3)
                
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
            
            # Buscar alterações de coluna (changeColumn)
            change_column_match = re.search(self.phinx_patterns['change_column'], line)
            if change_column_match:
                field_name = change_column_match.group(1)
                field_type = change_column_match.group(2)
                options = change_column_match.group(3)
                
                if self._is_cnpj_field(field_name):
                    field_size = self._extract_field_size(options)
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type=f"CHANGED_{field_type}",
                        field_size=field_size,
                        context=line.strip(),
                        category='migration'
                    ))
                continue
        
        return fields
    
    def _is_index_reference(self, line: str) -> bool:
        """Verifica se a linha é apenas uma referência em índice"""
        index_patterns = [
            r'addIndex\s*\(',
            r'addUnique\s*\(',
            r'addForeignKey\s*\(',
            r'index\s*\(',
            r'unique\s*\(',
            r'foreignKey\s*\(',
        ]
        
        for pattern in index_patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def _is_remove_column(self, line: str) -> bool:
        """Verifica se a linha é uma remoção de coluna"""
        return re.search(self.phinx_patterns['remove_column'], line) is not None
    
    def _is_drop_table(self, line: str) -> bool:
        """Verifica se a linha é um drop de tabela"""
        return re.search(self.phinx_patterns['drop_table'], line) is not None
    
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
            r'cpfcnpjpagador',
            r'cpf_cnpj_base',
            r'cnpj_base',
            r'cpfcnpj_indicador',
            r'cpfcnpj_indicado',
            r'cpf_cnpj_indicador',
            r'cpf_cnpj_indicado',
        ]
        
        field_lower = field_name.lower()
        return any(re.search(pattern, field_lower) for pattern in cnpj_patterns)
    
    def _extract_field_size(self, options: str) -> Optional[int]:
        """Extrai o tamanho do campo das opções"""
        # Buscar 'length' => X
        length_match = re.search(r"'length'\s*=>\s*(\d+)", options)
        if length_match:
            return int(length_match.group(1))
        
        # Buscar length como segundo parâmetro
        length_match = re.search(r',\s*(\d+)', options)
        if length_match:
            return int(length_match.group(1))
        
        return None
