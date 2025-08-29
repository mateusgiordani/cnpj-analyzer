"""
Analisador de Migrations Genérico
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


class GenericMigrationAnalyzer:
    """Analisador genérico para migrations de tipo desconhecido"""
    
    def __init__(self):
        self.generic_patterns = {
            'sql_create': r'CREATE\s+TABLE\s+[\'"`]?(\w+)[\'"`]?\s*\(([^)]+)\)',
            'sql_alter': r'ALTER\s+TABLE\s+[\'"`]?(\w+)[\'"`]?\s+ADD\s+COLUMN\s+[\'"`]?(\w+)[\'"`]?\s+(\w+)(?:\((\d+)\))?',
            'sql_drop': r'DROP\s+(?:TABLE|COLUMN)\s+[\'"`]?(\w+)[\'"`]?',
            'php_variable': r'\$(\w+)\s*=',
            'php_array': r'[\'"`](\w+)[\'"`]\s*=>',
        }
    
    def analyze_migration_file(self, file_path: str, content: str) -> List[PHPFieldDefinition]:
        """Analisa um arquivo de migration genérico e retorna apenas definições de campos"""
        fields = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Pular linhas que são operações de remoção
            if self._is_drop_operation(line):
                continue
            
            # Buscar definições SQL
            sql_match = self._find_sql_definitions(line)
            if sql_match:
                field_name, field_type, field_size = sql_match
                if self._is_cnpj_field(field_name):
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
            
            # Buscar variáveis PHP que podem ser campos
            var_match = re.search(self.generic_patterns['php_variable'], line)
            if var_match:
                field_name = var_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='PHP_VARIABLE',
                        field_size=None,
                        context=line.strip(),
                        category='migration'
                    ))
                continue
            
            # Buscar chaves de array que podem ser campos
            array_match = re.search(self.generic_patterns['php_array'], line)
            if array_match:
                field_name = array_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='ARRAY_KEY',
                        field_size=None,
                        context=line.strip(),
                        category='migration'
                    ))
        
        return fields
    
    def _is_drop_operation(self, line: str) -> bool:
        """Verifica se a linha é uma operação de remoção"""
        drop_patterns = [
            r'DROP\s+',
            r'DELETE\s+',
            r'REMOVE\s+',
            r'dropColumn',
            r'removeColumn',
            r'deleteColumn',
        ]
        
        line_upper = line.upper()
        return any(re.search(pattern, line_upper) for pattern in drop_patterns)
    
    def _find_sql_definitions(self, line: str) -> Optional[tuple]:
        """Encontra definições SQL na linha"""
        # Buscar ALTER TABLE ADD COLUMN
        alter_match = re.search(self.generic_patterns['sql_alter'], line, re.IGNORECASE)
        if alter_match:
            field_name = alter_match.group(2)
            field_type = alter_match.group(3).upper()
            field_size = int(alter_match.group(4)) if alter_match.group(4) else None
            return field_name, field_type, field_size
        
        # Buscar CREATE TABLE
        create_match = re.search(self.generic_patterns['sql_create'], line, re.IGNORECASE)
        if create_match:
            # Extrair campos da definição da tabela
            table_def = create_match.group(2)
            return self._extract_fields_from_table_def(table_def)
        
        return None
    
    def _extract_fields_from_table_def(self, table_def: str) -> Optional[tuple]:
        """Extrai campos da definição de tabela SQL"""
        # Padrão para encontrar campos na definição
        field_pattern = r'[\'"`]?(\w+)[\'"`]?\s+(\w+)(?:\((\d+)\))?'
        matches = re.findall(field_pattern, table_def, re.IGNORECASE)
        
        for field_name, field_type, field_size in matches:
            if self._is_cnpj_field(field_name):
                size = int(field_size) if field_size else None
                return field_name, field_type.upper(), size
        
        return None
    
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
