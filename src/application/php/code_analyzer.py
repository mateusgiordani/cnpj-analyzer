"""
Analisador de Código PHP
Versão: 1.0
Data: 2025-08-28
"""

import re
from typing import List
from dataclasses import dataclass


@dataclass
class PHPFieldDefinition:
    """Representa uma definição de campo PHP encontrada"""
    file_path: str
    line_number: int
    field_name: str
    field_type: str
    field_size: None
    context: str
    category: str  # 'migration', 'model', 'validation', 'test'


class PHPCodeAnalyzer:
    """Analisador para código PHP (models, services, etc.)"""
    
    def __init__(self):
        self.code_patterns = {
            'property': r'(?:public|private|protected)\s+\$(\w+)',
            'variable': r'\$(\w+)\s*=',
            'parameter': r'function\s+\w+\s*\([^)]*\$(\w+)[^)]*\)',
            'class_property': r'class\s+\w+\s*\{[^}]*\$(\w+)[^}]*\}',
            'array_key': r'[\'"]([^\'"]+)[\'"]\s*=>',
            'method_call': r'->(\w+)\s*\(',
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
                continue
            
            # Buscar parâmetros de função
            param_match = re.search(self.code_patterns['parameter'], line)
            if param_match:
                field_name = param_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='PARAMETER',
                        field_size=None,
                        context=line.strip(),
                        category='code'
                    ))
                continue
            
            # Buscar chaves de array
            array_match = re.search(self.code_patterns['array_key'], line)
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
                        category='code'
                    ))
                continue
            
            # Buscar chamadas de método
            method_match = re.search(self.code_patterns['method_call'], line)
            if method_match:
                field_name = method_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='METHOD_CALL',
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
            r'cpfCnpj',
            r'cpfcnpj',
            r'cpf_cnpj',
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
