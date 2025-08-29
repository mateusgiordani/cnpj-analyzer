"""
Analisador de Testes PHP
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


class PHPTestAnalyzer:
    """Analisador para testes PHP"""
    
    def __init__(self):
        self.test_patterns = {
            'test_data': r'[\'"]([^\'"]*cnpj[^\'"]*)[\'"]',
            'test_variable': r'\$(\w+)\s*=',
            'test_method': r'function\s+test(\w*Cnpj\w*)',
            'test_assertion': r'assert|expect|should',
            'test_fixture': r'[\'"]([^\'"]*cnpj[^\'"]*)[\'"]\s*=>',
            'test_property': r'(?:public|private|protected)\s+\$(\w+)',
            'test_parameter': r'function\s+\w+\s*\([^)]*\$(\w+)[^)]*\)',
            'mock_data': r'mock|stub|fake',
        }
    
    def analyze_test_file(self, file_path: str, content: str) -> List[PHPFieldDefinition]:
        """Analisa um arquivo de teste PHP"""
        fields = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Buscar dados de teste
            test_data_match = re.search(self.test_patterns['test_data'], line, re.IGNORECASE)
            if test_data_match:
                field_name = test_data_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=f"test_data_{line_num}",
                        field_type='TEST_DATA',
                        field_size=None,
                        context=line.strip(),
                        category='test'
                    ))
                continue
            
            # Buscar variáveis de teste
            var_match = re.search(self.test_patterns['test_variable'], line)
            if var_match:
                field_name = var_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='TEST_VARIABLE',
                        field_size=None,
                        context=line.strip(),
                        category='test'
                    ))
                continue
            
            # Buscar métodos de teste
            method_match = re.search(self.test_patterns['test_method'], line, re.IGNORECASE)
            if method_match:
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"test_method_{line_num}",
                    field_type='TEST_METHOD',
                    field_size=None,
                    context=line.strip(),
                    category='test'
                ))
                continue
            
            # Buscar assertions de teste
            assertion_match = re.search(self.test_patterns['test_assertion'], line)
            if assertion_match and self._contains_cnpj_reference(line):
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"test_assertion_{line_num}",
                    field_type='TEST_ASSERTION',
                    field_size=None,
                    context=line.strip(),
                    category='test'
                ))
                continue
            
            # Buscar fixtures de teste
            fixture_match = re.search(self.test_patterns['test_fixture'], line, re.IGNORECASE)
            if fixture_match:
                field_name = fixture_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='TEST_FIXTURE',
                        field_size=None,
                        context=line.strip(),
                        category='test'
                    ))
                continue
            
            # Buscar propriedades de teste
            prop_match = re.search(self.test_patterns['test_property'], line)
            if prop_match:
                field_name = prop_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='TEST_PROPERTY',
                        field_size=None,
                        context=line.strip(),
                        category='test'
                    ))
                continue
            
            # Buscar parâmetros de teste
            param_match = re.search(self.test_patterns['test_parameter'], line)
            if param_match:
                field_name = param_match.group(1)
                if self._is_cnpj_field(field_name):
                    fields.append(PHPFieldDefinition(
                        file_path=file_path,
                        line_number=line_num,
                        field_name=field_name,
                        field_type='TEST_PARAMETER',
                        field_size=None,
                        context=line.strip(),
                        category='test'
                    ))
                continue
            
            # Buscar dados mock
            mock_match = re.search(self.test_patterns['mock_data'], line, re.IGNORECASE)
            if mock_match and self._contains_cnpj_reference(line):
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"mock_data_{line_num}",
                    field_type='MOCK_DATA',
                    field_size=None,
                    context=line.strip(),
                    category='test'
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
    
    def _contains_cnpj_reference(self, line: str) -> bool:
        """Verifica se a linha contém referência a CNPJ"""
        cnpj_patterns = [
            r'cnpj',
            r'cpf_cnpj',
            r'cpfcnpj',
            r'cpfCnpj',
            r'cpfcnpj',
            r'cnpj_cpf',
            r'cnpjcpf',
        ]
        
        line_lower = line.lower()
        return any(re.search(pattern, line_lower) for pattern in cnpj_patterns)
