"""
Analisador de Validações PHP
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


class PHPValidationAnalyzer:
    """Analisador para validações PHP"""
    
    def __init__(self):
        self.validation_patterns = {
            'rule': r'[\'"]([^\'"]*cnpj[^\'"]*)[\'"]',
            'validator': r'CNPJ|Cnpj',
            'validation_method': r'validateCnpj|validate_cnpj',
            'assertion': r'@Assert\\',
            'rule_class': r'Rule::cnpj|CnpjValidator',
            'validation_array': r'[\'"]([^\'"]*cnpj[^\'"]*)[\'"]\s*[,|]',
            'custom_validator': r'class\s+(\w*Cnpj\w*Validator)',
            'validation_service': r'CnpjValidator|CpfCnpjValidator',
        }
    
    def analyze_validation_file(self, file_path: str, content: str) -> List[PHPFieldDefinition]:
        """Analisa um arquivo de validação PHP"""
        fields = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Buscar regras de validação
            rule_match = re.search(self.validation_patterns['rule'], line, re.IGNORECASE)
            if rule_match:
                rule = rule_match.group(1)
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"validation_rule_{line_num}",
                    field_type='VALIDATION_RULE',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
                continue
            
            # Buscar validadores
            validator_match = re.search(self.validation_patterns['validator'], line)
            if validator_match:
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"validator_{line_num}",
                    field_type='VALIDATOR',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
                continue
            
            # Buscar métodos de validação
            method_match = re.search(self.validation_patterns['validation_method'], line, re.IGNORECASE)
            if method_match:
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"validation_method_{line_num}",
                    field_type='VALIDATION_METHOD',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
                continue
            
            # Buscar assertions (Symfony)
            assertion_match = re.search(self.validation_patterns['assertion'], line)
            if assertion_match and self._contains_cnpj_reference(line):
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"assertion_{line_num}",
                    field_type='ASSERTION',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
                continue
            
            # Buscar classes de regra
            rule_class_match = re.search(self.validation_patterns['rule_class'], line)
            if rule_class_match:
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"rule_class_{line_num}",
                    field_type='RULE_CLASS',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
                continue
            
            # Buscar arrays de validação
            array_match = re.search(self.validation_patterns['validation_array'], line, re.IGNORECASE)
            if array_match:
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"validation_array_{line_num}",
                    field_type='VALIDATION_ARRAY',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
                continue
            
            # Buscar validadores customizados
            custom_match = re.search(self.validation_patterns['custom_validator'], line)
            if custom_match:
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=custom_match.group(1),
                    field_type='CUSTOM_VALIDATOR',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
                continue
            
            # Buscar serviços de validação
            service_match = re.search(self.validation_patterns['validation_service'], line)
            if service_match:
                fields.append(PHPFieldDefinition(
                    file_path=file_path,
                    line_number=line_num,
                    field_name=f"validation_service_{line_num}",
                    field_type='VALIDATION_SERVICE',
                    field_size=None,
                    context=line.strip(),
                    category='validation'
                ))
        
        return fields
    
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
