"""
Analisador de Migrations Laravel
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


class LaravelMigrationAnalyzer:
    """Analisador específico para migrations Laravel"""
    
    def __init__(self):
        self.laravel_patterns = {
            'string_field': r'\$table->string\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(\d+)\s*\)',
            'char_field': r'\$table->char\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(\d+)\s*\)',
            'text_field': r'\$table->text\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            'integer_field': r'\$table->integer\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            'bigint_field': r'\$table->bigInteger\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            'decimal_field': r'\$table->decimal\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
            'drop_column': r'\$table->dropColumn\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            'drop_columns': r'\$table->dropColumn\s*\(\s*\[([^\]]+)\]\s*\)',
            'rename_column': r'\$table->renameColumn\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)',
            'drop_table': r'Schema::drop\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            'create_table': r'Schema::create\s*\(\s*[\'"]([^\'"]+)[\'"]\s*',
        }
    
    def analyze_migration_file(self, file_path: str, content: str) -> List[PHPFieldDefinition]:
        """Analisa um arquivo de migration Laravel e retorna apenas definições de campos"""
        fields = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Pular linhas que são apenas referências em índices
            if self._is_index_reference(line):
                continue
            
            # Pular operações de remoção de coluna
            if self._is_drop_column(line):
                continue
            
            # Pular operações de drop table
            if self._is_drop_table(line):
                continue
            
            # Buscar campos string
            string_match = re.search(self.laravel_patterns['string_field'], line)
            if string_match:
                field_name = string_match.group(1)
                field_size = int(string_match.group(2))
                
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='string',
                        field_size=field_size,
                        context=line.strip(),
                        category='migration'
                    ))
                continue
            
            # Buscar campos char
            char_match = re.search(self.laravel_patterns['char_field'], line)
            if char_match:
                field_name = char_match.group(1)
                field_size = int(char_match.group(2))
                
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='char',
                        field_size=field_size,
                        context=line.strip(),
                        category='migration'
                    ))
                continue
            
            # Buscar campos text
            text_match = re.search(self.laravel_patterns['text_field'], line)
            if text_match:
                field_name = text_match.group(1)
                
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='text',
                        field_size=None,
                        context=line.strip(),
                        category='migration'
                    ))
                continue
            
            # Buscar campos integer
            integer_match = re.search(self.laravel_patterns['integer_field'], line)
            if integer_match:
                field_name = integer_match.group(1)
                
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='integer',
                        field_size=None,
                        context=line.strip(),
                        category='migration'
                    ))
                continue
            
            # Buscar campos bigInteger
            bigint_match = re.search(self.laravel_patterns['bigint_field'], line)
            if bigint_match:
                field_name = bigint_match.group(1)
                
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='bigInteger',
                        field_size=None,
                        context=line.strip(),
                        category='migration'
                    ))
                continue
        
        return fields
    
    def _is_index_reference(self, line: str) -> bool:
        """Verifica se a linha é apenas uma referência em índice"""
        index_patterns = [
            r'index\s*\(',
            r'unique\s*\(',
            r'foreign\s*\(',
            r'foreignId\s*\(',
            r'unsignedBigInteger\s*\(',
            r'unsignedInteger\s*\(',
        ]
        
        for pattern in index_patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def _is_drop_column(self, line: str) -> bool:
        """Verifica se a linha é uma remoção de coluna"""
        return (
            re.search(self.laravel_patterns['drop_column'], line) is not None or
            re.search(self.laravel_patterns['drop_columns'], line) is not None
        )
    
    def _is_drop_table(self, line: str) -> bool:
        """Verifica se a linha é um drop de tabela"""
        return re.search(self.laravel_patterns['drop_table'], line) is not None
    
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
