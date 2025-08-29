"""
Implementação CNPJField para PHP - Campos específicos de projetos PHP
Versão: 1.0
Data: 2025-08-29
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .cnpj_field_base import CNPJFieldBase
from .cnpj_field_interface import ImpactLevel, Status

@dataclass
class CNPJFieldPHP(CNPJFieldBase):
    """Implementação específica do CNPJField para PHP"""
    
    # Campos específicos para PHP
    php_type: Optional[str] = None  # string, int, etc.
    sql_type: Optional[str] = None  # VARCHAR, CHAR, etc.
    framework: Optional[str] = None  # Laravel, Symfony, etc.
    validation_rules: Optional[list] = None  # Regras de validação PHP
    migration_type: Optional[str] = None  # Tipo de migração
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o campo para dicionário serializável com campos PHP específicos"""
        base_dict = super().to_dict()
        base_dict.update({
            'php_type': self.php_type,
            'sql_type': self.sql_type,
            'framework': self.framework,
            'validation_rules': self.validation_rules,
            'migration_type': self.migration_type
        })
        return base_dict
    
    def get_php_context(self) -> str:
        """Retorna contexto específico para PHP"""
        context_parts = []
        
        if self.php_type:
            context_parts.append(f"Tipo PHP: {self.php_type}")
        
        if self.sql_type:
            context_parts.append(f"Tipo SQL: {self.sql_type}")
        
        if self.framework:
            context_parts.append(f"Framework: {self.framework}")
        
        if self.validation_rules:
            context_parts.append(f"Validações: {', '.join(self.validation_rules)}")
        
        if self.migration_type:
            context_parts.append(f"Migração: {self.migration_type}")
        
        return " | ".join(context_parts) if context_parts else self.context
    
    def is_migration_field(self) -> bool:
        """Verifica se é um campo de migração"""
        return 'migration' in self.file_path.lower()
    
    def is_model_field(self) -> bool:
        """Verifica se é um campo de modelo"""
        return 'model' in self.file_path.lower() or 'entity' in self.file_path.lower()
    
    def is_validation_field(self) -> bool:
        """Verifica se é um campo de validação"""
        return self.field_type in ['VALIDATION_FUNCTION', 'FORM_VALIDATION']
    
    def get_php_impact_assessment(self) -> str:
        """Retorna avaliação de impacto específica para PHP"""
        if self.is_migration_field():
            return "Alto impacto - Migração precisa ser atualizada"
        elif self.is_model_field():
            return "Médio impacto - Modelo precisa ser atualizado"
        elif self.is_validation_field():
            return "Alto impacto - Validação precisa ser atualizada"
        else:
            return self.action_needed
    
    def get_sql_compatibility(self) -> str:
        """Retorna compatibilidade SQL"""
        if self.sql_type:
            if 'VARCHAR' in self.sql_type or 'CHAR' in self.sql_type:
                return "Compatível com CNPJ alfanumérico"
            elif 'INT' in self.sql_type or 'BIGINT' in self.sql_type:
                return "Incompatível - Precisa ser alterado para VARCHAR"
            else:
                return "Análise necessária"
        return "Tipo SQL não identificado"
