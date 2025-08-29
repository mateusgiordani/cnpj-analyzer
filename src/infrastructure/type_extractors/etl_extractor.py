"""
Extractor de tipos para ETL (Pentaho, SQL, etc.)
Versão: 1.0
Data: 2025-08-29
"""

import re
from typing import Tuple, Optional
from .base_type_extractor import BaseTypeExtractor

class ETLExtractor(BaseTypeExtractor):
    """Extractor de tipos para arquivos ETL"""
    
    def get_supported_extensions(self) -> list:
        """Retorna as extensões suportadas"""
        return ['.ktr', '.kjb', '.sql', '.xml', '.xsd', '.csv', '.txt']
    
    def extract_type_and_size(self, line: str) -> Tuple[str, Optional[int]]:
        """
        Extrai tipo e tamanho do campo da linha para ETL
        
        Args:
            line: Linha do código ETL
            
        Returns:
            Tuple com (tipo, tamanho)
        """
        line_lower = line.lower()
        
        # Padrões Pentaho KTR/KJB
        if re.search(r'<field.*name=["\']([^"\']*cnpj[^"\']*)["\']', line, re.IGNORECASE):
            return 'PENTAHO_FIELD', None
        elif re.search(r'<field.*type=["\']([^"\']*)["\']', line, re.IGNORECASE):
            match = re.search(r'<field.*type=["\']([^"\']*)["\']', line, re.IGNORECASE)
            if match:
                field_type = match.group(1).lower()
                if 'string' in field_type or 'varchar' in field_type:
                    return 'STRING', None
                elif 'number' in field_type or 'integer' in field_type or 'int' in field_type:
                    return 'NUMBER', None
                elif 'date' in field_type or 'timestamp' in field_type:
                    return 'DATE', None
                elif 'boolean' in field_type or 'bool' in field_type:
                    return 'BOOLEAN', None
                else:
                    return 'UNKNOWN', None
        
        # Padrões SQL
        elif re.search(r'VARCHAR\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
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
                return 'INTEGER', int(match.group(1))
        elif re.search(r'BIGINT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'BIGINT\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'BIGINT', int(match.group(1))
        elif re.search(r'DECIMAL\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'DECIMAL\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'DECIMAL', int(match.group(1))
        elif re.search(r'DATETIME', line, re.IGNORECASE):
            return 'DATETIME', None
        elif re.search(r'TIMESTAMP', line, re.IGNORECASE):
            return 'TIMESTAMP', None
        elif re.search(r'DATE', line, re.IGNORECASE):
            return 'DATE', None
        elif re.search(r'TEXT', line, re.IGNORECASE):
            return 'TEXT', None
        elif re.search(r'LONGTEXT', line, re.IGNORECASE):
            return 'LONGTEXT', None
        elif re.search(r'BLOB', line, re.IGNORECASE):
            return 'BLOB', None
        elif re.search(r'LONGBLOB', line, re.IGNORECASE):
            return 'LONGBLOB', None
        
        # Padrões Pentaho específicos
        elif re.search(r'String.*field', line, re.IGNORECASE):
            return 'PENTAHO_STRING', None
        elif re.search(r'Number.*field', line, re.IGNORECASE):
            return 'PENTAHO_NUMBER', None
        elif re.search(r'Date.*field', line, re.IGNORECASE):
            return 'PENTAHO_DATE', None
        elif re.search(r'Boolean.*field', line, re.IGNORECASE):
            return 'PENTAHO_BOOLEAN', None
        
        # Padrões de transformação Pentaho
        elif re.search(r'String.*Operations', line, re.IGNORECASE):
            return 'STRING_TRANSFORMATION', None
        elif re.search(r'Calculator', line, re.IGNORECASE):
            return 'CALCULATOR_STEP', None
        elif re.search(r'Filter.*Rows', line, re.IGNORECASE):
            return 'FILTER_STEP', None
        elif re.search(r'Add.*Constants', line, re.IGNORECASE):
            return 'ADD_CONSTANTS_STEP', None
        elif re.search(r'Select.*Values', line, re.IGNORECASE):
            return 'SELECT_VALUES_STEP', None
        elif re.search(r'Get.*Fields', line, re.IGNORECASE):
            return 'GET_FIELDS_STEP', None
        elif re.search(r'Set.*Variable', line, re.IGNORECASE):
            return 'SET_VARIABLE_STEP', None
        elif re.search(r'Get.*Variable', line, re.IGNORECASE):
            return 'GET_VARIABLE_STEP', None
        
        # Padrões de validação ETL
        elif re.search(r'Data.*Validator', line, re.IGNORECASE):
            return 'DATA_VALIDATOR', None
        elif re.search(r'Null.*Check', line, re.IGNORECASE):
            return 'NULL_CHECK', None
        elif re.search(r'Length.*Check', line, re.IGNORECASE):
            return 'LENGTH_CHECK', None
        elif re.search(r'Pattern.*Match', line, re.IGNORECASE):
            return 'PATTERN_MATCH', None
        
        # Padrões de entrada/saída
        elif re.search(r'Table.*Input', line, re.IGNORECASE):
            return 'TABLE_INPUT', None
        elif re.search(r'Table.*Output', line, re.IGNORECASE):
            return 'TABLE_OUTPUT', None
        elif re.search(r'CSV.*Input', line, re.IGNORECASE):
            return 'CSV_INPUT', None
        elif re.search(r'CSV.*Output', line, re.IGNORECASE):
            return 'CSV_OUTPUT', None
        elif re.search(r'Excel.*Input', line, re.IGNORECASE):
            return 'EXCEL_INPUT', None
        elif re.search(r'Excel.*Output', line, re.IGNORECASE):
            return 'EXCEL_OUTPUT', None
        elif re.search(r'JSON.*Input', line, re.IGNORECASE):
            return 'JSON_INPUT', None
        elif re.search(r'JSON.*Output', line, re.IGNORECASE):
            return 'JSON_OUTPUT', None
        
        # Padrões de variáveis
        elif re.search(r'\$\{.*\}', line, re.IGNORECASE):
            return 'VARIABLE', None
        elif re.search(r'Parameter', line, re.IGNORECASE):
            return 'PARAMETER', None
        
        # Inferência por contexto
        else:
            if 'cnpj' in line_lower or 'cpf' in line_lower or 'documento' in line_lower:
                return 'STRING', None  # CNPJ/CPF são sempre strings em ETL
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
