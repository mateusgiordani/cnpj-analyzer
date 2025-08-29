"""
Extractor de tipos para SQL
Versão: 1.0
Data: 2025-08-29
"""

import re
from typing import Tuple, Optional
from .base_type_extractor import BaseTypeExtractor

class SQLExtractor(BaseTypeExtractor):
    """Extractor de tipos para arquivos SQL"""
    
    def get_supported_extensions(self) -> list:
        """Retorna as extensões suportadas"""
        return ['.sql']
    
    def extract_type_and_size(self, line: str) -> Tuple[str, Optional[int]]:
        """
        Extrai tipo e tamanho do campo da linha para SQL
        
        Args:
            line: Linha do código SQL
            
        Returns:
            Tuple com (tipo, tamanho)
        """
        line_lower = line.lower()
        
        # Padrões de tipos SQL
        if re.search(r'VARCHAR\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'VARCHAR\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'VARCHAR', int(match.group(1))
        elif re.search(r'CHAR\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'CHAR\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'CHAR', int(match.group(1))
        elif re.search(r'INT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'INT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'INT', int(match.group(1))
        elif re.search(r'INTEGER\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'INTEGER\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'INTEGER', int(match.group(1))
        elif re.search(r'BIGINT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'BIGINT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'BIGINT', int(match.group(1))
        elif re.search(r'SMALLINT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'SMALLINT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'SMALLINT', int(match.group(1))
        elif re.search(r'TINYINT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'TINYINT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'TINYINT', int(match.group(1))
        elif re.search(r'DECIMAL\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'DECIMAL\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'DECIMAL', int(match.group(1))
        elif re.search(r'NUMERIC\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'NUMERIC\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'NUMERIC', int(match.group(1))
        elif re.search(r'FLOAT\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'FLOAT\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'FLOAT', int(match.group(1))
        elif re.search(r'DOUBLE\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'DOUBLE\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'DOUBLE', int(match.group(1))
        
        # Tipos sem tamanho
        elif re.search(r'VARCHAR', line, re.IGNORECASE):
            return 'VARCHAR', None
        elif re.search(r'CHAR', line, re.IGNORECASE):
            return 'CHAR', None
        elif re.search(r'INT', line, re.IGNORECASE):
            return 'INT', None
        elif re.search(r'INTEGER', line, re.IGNORECASE):
            return 'INTEGER', None
        elif re.search(r'BIGINT', line, re.IGNORECASE):
            return 'BIGINT', None
        elif re.search(r'SMALLINT', line, re.IGNORECASE):
            return 'SMALLINT', None
        elif re.search(r'TINYINT', line, re.IGNORECASE):
            return 'TINYINT', None
        elif re.search(r'DECIMAL', line, re.IGNORECASE):
            return 'DECIMAL', None
        elif re.search(r'NUMERIC', line, re.IGNORECASE):
            return 'NUMERIC', None
        elif re.search(r'FLOAT', line, re.IGNORECASE):
            return 'FLOAT', None
        elif re.search(r'DOUBLE', line, re.IGNORECASE):
            return 'DOUBLE', None
        elif re.search(r'REAL', line, re.IGNORECASE):
            return 'REAL', None
        
        # Tipos de data/hora
        elif re.search(r'DATETIME', line, re.IGNORECASE):
            return 'DATETIME', None
        elif re.search(r'TIMESTAMP', line, re.IGNORECASE):
            return 'TIMESTAMP', None
        elif re.search(r'DATE', line, re.IGNORECASE):
            return 'DATE', None
        elif re.search(r'TIME', line, re.IGNORECASE):
            return 'TIME', None
        elif re.search(r'YEAR', line, re.IGNORECASE):
            return 'YEAR', None
        
        # Tipos de texto
        elif re.search(r'TEXT', line, re.IGNORECASE):
            return 'TEXT', None
        elif re.search(r'LONGTEXT', line, re.IGNORECASE):
            return 'LONGTEXT', None
        elif re.search(r'MEDIUMTEXT', line, re.IGNORECASE):
            return 'MEDIUMTEXT', None
        elif re.search(r'TINYTEXT', line, re.IGNORECASE):
            return 'TINYTEXT', None
        
        # Tipos de blob
        elif re.search(r'BLOB', line, re.IGNORECASE):
            return 'BLOB', None
        elif re.search(r'LONGBLOB', line, re.IGNORECASE):
            return 'LONGBLOB', None
        elif re.search(r'MEDIUMBLOB', line, re.IGNORECASE):
            return 'MEDIUMBLOB', None
        elif re.search(r'TINYBLOB', line, re.IGNORECASE):
            return 'TINYBLOB', None
        
        # Tipos booleanos
        elif re.search(r'BOOLEAN', line, re.IGNORECASE):
            return 'BOOLEAN', None
        elif re.search(r'BOOL', line, re.IGNORECASE):
            return 'BOOL', None
        elif re.search(r'BIT', line, re.IGNORECASE):
            return 'BIT', None
        
        # Tipos JSON
        elif re.search(r'JSON', line, re.IGNORECASE):
            return 'JSON', None
        
        # Tipos de enum
        elif re.search(r'ENUM\s*\(', line, re.IGNORECASE):
            return 'ENUM', None
        elif re.search(r'SET\s*\(', line, re.IGNORECASE):
            return 'SET', None
        
        # Padrões de constraint
        elif re.search(r'PRIMARY KEY', line, re.IGNORECASE):
            return 'PRIMARY_KEY', None
        elif re.search(r'FOREIGN KEY', line, re.IGNORECASE):
            return 'FOREIGN_KEY', None
        elif re.search(r'UNIQUE', line, re.IGNORECASE):
            return 'UNIQUE', None
        elif re.search(r'NOT NULL', line, re.IGNORECASE):
            return 'NOT_NULL', None
        elif re.search(r'DEFAULT', line, re.IGNORECASE):
            return 'DEFAULT', None
        elif re.search(r'AUTO_INCREMENT', line, re.IGNORECASE):
            return 'AUTO_INCREMENT', None
        
        # Padrões de índice
        elif re.search(r'INDEX', line, re.IGNORECASE):
            return 'INDEX', None
        elif re.search(r'KEY', line, re.IGNORECASE):
            return 'KEY', None
        elif re.search(r'UNIQUE KEY', line, re.IGNORECASE):
            return 'UNIQUE_KEY', None
        elif re.search(r'PRIMARY KEY', line, re.IGNORECASE):
            return 'PRIMARY_KEY', None
        
        # Padrões de tabela
        elif re.search(r'CREATE TABLE', line, re.IGNORECASE):
            return 'CREATE_TABLE', None
        elif re.search(r'ALTER TABLE', line, re.IGNORECASE):
            return 'ALTER_TABLE', None
        elif re.search(r'DROP TABLE', line, re.IGNORECASE):
            return 'DROP_TABLE', None
        elif re.search(r'INSERT INTO', line, re.IGNORECASE):
            return 'INSERT', None
        elif re.search(r'UPDATE', line, re.IGNORECASE):
            return 'UPDATE', None
        elif re.search(r'DELETE FROM', line, re.IGNORECASE):
            return 'DELETE', None
        elif re.search(r'SELECT', line, re.IGNORECASE):
            return 'SELECT', None
        
        # Padrões de comentário
        elif re.search(r'--.*', line, re.IGNORECASE):
            return 'SQL_COMMENT', None
        elif re.search(r'/\*.*\*/', line, re.IGNORECASE):
            return 'SQL_COMMENT_BLOCK', None
        
        # Inferência por contexto
        else:
            if 'cnpj' in line_lower or 'cpf' in line_lower or 'documento' in line_lower:
                return 'VARCHAR', None  # CNPJ/CPF são sempre VARCHAR em SQL
            elif 'id' in line_lower:
                return 'ID_FIELD', None
            elif 'date' in line_lower or 'time' in line_lower:
                return 'DATE_FIELD', None
            elif 'email' in line_lower:
                return 'EMAIL_FIELD', None
            elif 'phone' in line_lower or 'telefone' in line_lower:
                return 'PHONE_FIELD', None
            elif 'amount' in line_lower or 'value' in line_lower or 'total' in line_lower:
                return 'NUMBER_FIELD', None
            elif 'name' in line_lower or 'nome' in line_lower:
                return 'STRING_FIELD', None
            else:
                return 'UNKNOWN', None
