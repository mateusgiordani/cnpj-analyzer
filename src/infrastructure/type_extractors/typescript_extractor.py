"""
Extractor de tipos para TypeScript/NestJS
Versão: 1.0
Data: 2025-08-29
"""

import re
from typing import Tuple, Optional
from .base_type_extractor import BaseTypeExtractor

class TypeScriptExtractor(BaseTypeExtractor):
    """Extractor de tipos para arquivos TypeScript/NestJS"""
    
    def get_supported_extensions(self) -> list:
        """Retorna as extensões suportadas"""
        return ['.ts', '.tsx']
    
    def extract_type_and_size(self, line: str) -> Tuple[str, Optional[int]]:
        """
        Extrai tipo e tamanho do campo da linha para TypeScript
        
        Args:
            line: Linha do código TypeScript
            
        Returns:
            Tuple com (tipo, tamanho)
        """
        line_lower = line.lower()
        
        # Tipos básicos TypeScript
        if re.search(r':\s*string\s*[\[\]]?', line, re.IGNORECASE):
            return 'STRING', None
        elif re.search(r':\s*number\s*[\[\]]?', line, re.IGNORECASE):
            return 'NUMBER', None
        elif re.search(r':\s*boolean\s*[\[\]]?', line, re.IGNORECASE):
            return 'BOOLEAN', None
        elif re.search(r':\s*any\s*[\[\]]?', line, re.IGNORECASE):
            return 'ANY', None
        elif re.search(r':\s*object\s*[\[\]]?', line, re.IGNORECASE):
            return 'OBJECT', None
        elif re.search(r':\s*array\s*[\[\]]?', line, re.IGNORECASE):
            return 'ARRAY', None
        elif re.search(r':\s*\[.*\]', line, re.IGNORECASE):
            return 'ARRAY', None
        elif re.search(r':\s*Promise<', line, re.IGNORECASE):
            return 'PROMISE', None
        elif re.search(r':\s*Observable<', line, re.IGNORECASE):
            return 'OBSERVABLE', None
        
        # Decorators de validação
        elif re.search(r'@IsString', line, re.IGNORECASE):
            return 'STRING', None
        elif re.search(r'@IsNumber', line, re.IGNORECASE):
            return 'NUMBER', None
        elif re.search(r'@IsBoolean', line, re.IGNORECASE):
            return 'BOOLEAN', None
        elif re.search(r'@IsArray', line, re.IGNORECASE):
            return 'ARRAY', None
        elif re.search(r'@IsObject', line, re.IGNORECASE):
            return 'OBJECT', None
        
        # Decorators de tamanho
        elif re.search(r'@Length\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'@Length\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'STRING', int(match.group(2))  # Usar o tamanho máximo
        elif re.search(r'@MaxLength\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'@MaxLength\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'STRING', int(match.group(1))
        elif re.search(r'@MinLength\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'@MinLength\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'STRING', int(match.group(1))
        
        # Decorators específicos
        elif re.search(r'@Matches\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', line, re.IGNORECASE):
            return 'STRING', None  # Campo com validação de padrão
        elif re.search(r'@IsCNPJ', line, re.IGNORECASE):
            return 'CNPJ_VALIDATION', None
        elif re.search(r'@IsDocument', line, re.IGNORECASE):
            return 'DOCUMENT_VALIDATION', None
        elif re.search(r'@IsNotEmpty', line, re.IGNORECASE):
            return 'REQUIRED_FIELD', None
        elif re.search(r'@IsOptional', line, re.IGNORECASE):
            return 'OPTIONAL_FIELD', None
        elif re.search(r'@Transform', line, re.IGNORECASE):
            return 'TRANSFORMED_FIELD', None
        
        # Métodos e classes
        elif re.search(r'async\s+.*\(.*\)\s*:\s*Promise', line, re.IGNORECASE):
            return 'ASYNC_METHOD', None
        elif re.search(r'async\s+.*\(.*\)\s*:\s*Observable', line, re.IGNORECASE):
            return 'ASYNC_METHOD', None
        elif re.search(r'export\s+class\s+', line, re.IGNORECASE):
            return 'CLASS_DEFINITION', None
        elif re.search(r'export\s+interface\s+', line, re.IGNORECASE):
            return 'INTERFACE_DEFINITION', None
        elif re.search(r'export\s+type\s+', line, re.IGNORECASE):
            return 'TYPE_DEFINITION', None
        elif re.search(r'export\s+enum\s+', line, re.IGNORECASE):
            return 'ENUM_DEFINITION', None
        elif re.search(r'constructor\s*\(', line, re.IGNORECASE):
            return 'CONSTRUCTOR', None
        
        # Decorators de classe
        elif re.search(r'@Injectable', line, re.IGNORECASE):
            return 'SERVICE_CLASS', None
        elif re.search(r'@Controller', line, re.IGNORECASE):
            return 'CONTROLLER_CLASS', None
        elif re.search(r'@Entity', line, re.IGNORECASE):
            return 'ENTITY_CLASS', None
        elif re.search(r'@Column', line, re.IGNORECASE):
            return 'DATABASE_COLUMN', None
        elif re.search(r'@PrimaryGeneratedColumn', line, re.IGNORECASE):
            return 'PRIMARY_KEY', None
        elif re.search(r'@ManyToOne|@OneToMany|@OneToOne|@ManyToMany', line, re.IGNORECASE):
            return 'RELATIONSHIP', None
        
        # Inferência por contexto
        else:
            if 'cnpj' in line_lower or 'cpf' in line_lower or 'documento' in line_lower:
                return 'STRING', None  # CNPJ/CPF são sempre strings
            elif 'id' in line_lower:
                return 'ID_FIELD', None
            elif 'date' in line_lower or 'time' in line_lower:
                return 'DATE_FIELD', None
            elif 'email' in line_lower:
                return 'EMAIL_FIELD', None
            elif 'phone' in line_lower or 'telefone' in line_lower:
                return 'PHONE_FIELD', None
            else:
                return 'UNKNOWN', None
