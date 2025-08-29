"""
Extractor de tipos para PHP
Versão: 1.0
Data: 2025-08-29
"""

import re
from typing import Tuple, Optional
from .base_type_extractor import BaseTypeExtractor

class PHPExtractor(BaseTypeExtractor):
    """Extractor de tipos para arquivos PHP"""
    
    def get_supported_extensions(self) -> list:
        """Retorna as extensões suportadas"""
        return ['.php']
    
    def extract_type_and_size(self, line: str) -> Tuple[str, Optional[int]]:
        """
        Extrai tipo e tamanho do campo da linha para PHP
        
        Args:
            line: Linha do código PHP
            
        Returns:
            Tuple com (tipo, tamanho)
        """
        line_lower = line.lower()
        
        # Padrões de tipos PHP
        if re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[\'"][^\'"]*[\'"]', line, re.IGNORECASE):
            return 'PHP_STRING', None
        elif re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\d+', line, re.IGNORECASE):
            return 'PHP_INTEGER', None
        elif re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\d+\.\d+', line, re.IGNORECASE):
            return 'PHP_FLOAT', None
        elif re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*(true|false)', line, re.IGNORECASE):
            return 'PHP_BOOLEAN', None
        elif re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*array\s*\(', line, re.IGNORECASE):
            return 'PHP_ARRAY', None
        elif re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\[', line, re.IGNORECASE):
            return 'PHP_ARRAY', None
        elif re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*new\s+', line, re.IGNORECASE):
            return 'PHP_OBJECT', None
        
        # Padrões de propriedades de classe
        elif re.search(r'private\s+\$[a-zA-Z_][a-zA-Z0-9_]*\s*;', line, re.IGNORECASE):
            return 'PHP_PRIVATE_PROPERTY', None
        elif re.search(r'public\s+\$[a-zA-Z_][a-zA-Z0-9_]*\s*;', line, re.IGNORECASE):
            return 'PHP_PUBLIC_PROPERTY', None
        elif re.search(r'protected\s+\$[a-zA-Z_][a-zA-Z0-9_]*\s*;', line, re.IGNORECASE):
            return 'PHP_PROTECTED_PROPERTY', None
        
        # Padrões de parâmetros de função
        elif re.search(r'function\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\$[a-zA-Z_][a-zA-Z0-9_]*\s*\)', line, re.IGNORECASE):
            return 'PHP_FUNCTION_PARAMETER', None
        elif re.search(r'public\s+function\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\$[a-zA-Z_][a-zA-Z0-9_]*\s*\)', line, re.IGNORECASE):
            return 'PHP_PUBLIC_FUNCTION_PARAMETER', None
        elif re.search(r'private\s+function\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\$[a-zA-Z_][a-zA-Z0-9_]*\s*\)', line, re.IGNORECASE):
            return 'PHP_PRIVATE_FUNCTION_PARAMETER', None
        elif re.search(r'protected\s+function\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\$[a-zA-Z_][a-zA-Z0-9_]*\s*\)', line, re.IGNORECASE):
            return 'PHP_PROTECTED_FUNCTION_PARAMETER', None
        
        # Padrões Laravel/Symfony
        elif re.search(r'@ORM\\Column', line, re.IGNORECASE):
            return 'DOCTRINE_COLUMN', None
        elif re.search(r'@ORM\\Entity', line, re.IGNORECASE):
            return 'DOCTRINE_ENTITY', None
        elif re.search(r'@ORM\\Table', line, re.IGNORECASE):
            return 'DOCTRINE_TABLE', None
        elif re.search(r'@ORM\\Id', line, re.IGNORECASE):
            return 'DOCTRINE_ID', None
        elif re.search(r'@ORM\\GeneratedValue', line, re.IGNORECASE):
            return 'DOCTRINE_GENERATED_VALUE', None
        elif re.search(r'@ORM\\ManyToOne', line, re.IGNORECASE):
            return 'DOCTRINE_MANY_TO_ONE', None
        elif re.search(r'@ORM\\OneToMany', line, re.IGNORECASE):
            return 'DOCTRINE_ONE_TO_MANY', None
        elif re.search(r'@ORM\\OneToOne', line, re.IGNORECASE):
            return 'DOCTRINE_ONE_TO_ONE', None
        elif re.search(r'@ORM\\ManyToMany', line, re.IGNORECASE):
            return 'DOCTRINE_MANY_TO_MANY', None
        
        # Padrões de validação Laravel
        elif re.search(r'@Assert\\NotBlank', line, re.IGNORECASE):
            return 'SYMFONY_NOT_BLANK', None
        elif re.search(r'@Assert\\Length', line, re.IGNORECASE):
            return 'SYMFONY_LENGTH', None
        elif re.search(r'@Assert\\Regex', line, re.IGNORECASE):
            return 'SYMFONY_REGEX', None
        elif re.search(r'@Assert\\Email', line, re.IGNORECASE):
            return 'SYMFONY_EMAIL', None
        elif re.search(r'@Assert\\NotNull', line, re.IGNORECASE):
            return 'SYMFONY_NOT_NULL', None
        elif re.search(r'@Assert\\Type', line, re.IGNORECASE):
            return 'SYMFONY_TYPE', None
        
        # Padrões de validação Laravel
        elif re.search(r'required', line, re.IGNORECASE):
            return 'LARAVEL_REQUIRED', None
        elif re.search(r'string', line, re.IGNORECASE):
            return 'LARAVEL_STRING', None
        elif re.search(r'integer', line, re.IGNORECASE):
            return 'LARAVEL_INTEGER', None
        elif re.search(r'numeric', line, re.IGNORECASE):
            return 'LARAVEL_NUMERIC', None
        elif re.search(r'email', line, re.IGNORECASE):
            return 'LARAVEL_EMAIL', None
        elif re.search(r'date', line, re.IGNORECASE):
            return 'LARAVEL_DATE', None
        elif re.search(r'boolean', line, re.IGNORECASE):
            return 'LARAVEL_BOOLEAN', None
        elif re.search(r'array', line, re.IGNORECASE):
            return 'LARAVEL_ARRAY', None
        elif re.search(r'min:', line, re.IGNORECASE):
            return 'LARAVEL_MIN', None
        elif re.search(r'max:', line, re.IGNORECASE):
            return 'LARAVEL_MAX', None
        elif re.search(r'size:', line, re.IGNORECASE):
            return 'LARAVEL_SIZE', None
        elif re.search(r'regex:', line, re.IGNORECASE):
            return 'LARAVEL_REGEX', None
        
        # Padrões de migração
        elif re.search(r'\$table->string\s*\(\s*[\'"][^\'"]*[\'"]\s*,\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'\$table->string\s*\(\s*[\'"][^\'"]*[\'"]\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'LARAVEL_MIGRATION_STRING', int(match.group(1))
        elif re.search(r'\$table->char\s*\(\s*[\'"][^\'"]*[\'"]\s*,\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'\$table->char\s*\(\s*[\'"][^\'"]*[\'"]\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'LARAVEL_MIGRATION_CHAR', int(match.group(1))
        elif re.search(r'\$table->integer\s*\(\s*[\'"][^\'"]*[\'"]\s*\)', line, re.IGNORECASE):
            return 'LARAVEL_MIGRATION_INTEGER', None
        elif re.search(r'\$table->bigInteger\s*\(\s*[\'"][^\'"]*[\'"]\s*\)', line, re.IGNORECASE):
            return 'LARAVEL_MIGRATION_BIGINTEGER', None
        elif re.search(r'\$table->text\s*\(\s*[\'"][^\'"]*[\'"]\s*\)', line, re.IGNORECASE):
            return 'LARAVEL_MIGRATION_TEXT', None
        elif re.search(r'\$table->boolean\s*\(\s*[\'"][^\'"]*[\'"]\s*\)', line, re.IGNORECASE):
            return 'LARAVEL_MIGRATION_BOOLEAN', None
        elif re.search(r'\$table->date\s*\(\s*[\'"][^\'"]*[\'"]\s*\)', line, re.IGNORECASE):
            return 'LARAVEL_MIGRATION_DATE', None
        elif re.search(r'\$table->datetime\s*\(\s*[\'"][^\'"]*[\'"]\s*\)', line, re.IGNORECASE):
            return 'LARAVEL_MIGRATION_DATETIME', None
        elif re.search(r'\$table->timestamp\s*\(\s*[\'"][^\'"]*[\'"]\s*\)', line, re.IGNORECASE):
            return 'LARAVEL_MIGRATION_TIMESTAMP', None
        elif re.search(r'\$table->decimal\s*\(\s*[\'"][^\'"]*[\'"]\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE):
            match = re.search(r'\$table->decimal\s*\(\s*[\'"][^\'"]*[\'"]\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
            if match:
                return 'LARAVEL_MIGRATION_DECIMAL', int(match.group(1))
        
        # Padrões de controller
        elif re.search(r'class\s+[a-zA-Z_][a-zA-Z0-9_]*Controller', line, re.IGNORECASE):
            return 'PHP_CONTROLLER_CLASS', None
        elif re.search(r'class\s+[a-zA-Z_][a-zA-Z0-9_]*Service', line, re.IGNORECASE):
            return 'PHP_SERVICE_CLASS', None
        elif re.search(r'class\s+[a-zA-Z_][a-zA-Z0-9_]*Repository', line, re.IGNORECASE):
            return 'PHP_REPOSITORY_CLASS', None
        elif re.search(r'class\s+[a-zA-Z_][a-zA-Z0-9_]*Model', line, re.IGNORECASE):
            return 'PHP_MODEL_CLASS', None
        elif re.search(r'class\s+[a-zA-Z_][a-zA-Z0-9_]*Entity', line, re.IGNORECASE):
            return 'PHP_ENTITY_CLASS', None
        
        # Padrões de namespace
        elif re.search(r'namespace\s+', line, re.IGNORECASE):
            return 'PHP_NAMESPACE', None
        elif re.search(r'use\s+', line, re.IGNORECASE):
            return 'PHP_USE_STATEMENT', None
        
        # Padrões de comentário
        elif re.search(r'//.*', line, re.IGNORECASE):
            return 'PHP_COMMENT', None
        elif re.search(r'/\*.*\*/', line, re.IGNORECASE):
            return 'PHP_COMMENT_BLOCK', None
        
        # Inferência por contexto
        else:
            if 'cnpj' in line_lower or 'cpf' in line_lower or 'documento' in line_lower:
                return 'PHP_STRING', None  # CNPJ/CPF são sempre strings em PHP
            elif 'id' in line_lower:
                return 'PHP_ID_FIELD', None
            elif 'date' in line_lower or 'time' in line_lower:
                return 'PHP_DATE_FIELD', None
            elif 'email' in line_lower:
                return 'PHP_EMAIL_FIELD', None
            elif 'phone' in line_lower or 'telefone' in line_lower:
                return 'PHP_PHONE_FIELD', None
            elif 'amount' in line_lower or 'value' in line_lower or 'total' in line_lower:
                return 'PHP_NUMBER_FIELD', None
            elif 'name' in line_lower or 'nome' in line_lower:
                return 'PHP_STRING_FIELD', None
            else:
                return 'UNKNOWN', None
