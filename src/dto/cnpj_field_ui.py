"""
Implementação CNPJField para UI - Campos específicos de interface de usuário
Versão: 1.0
Data: 2025-08-29
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .cnpj_field_base import CNPJFieldBase
from .cnpj_field_interface import ImpactLevel, Status

@dataclass
class CNPJFieldUI(CNPJFieldBase):
    """Implementação específica do CNPJField para UI"""
    
    # Campos específicos para UI
    component_type: Optional[str] = None  # Vue, React, Angular
    event_handlers: Optional[list] = None  # @change, @input, etc.
    validation_rules: Optional[list] = None  # Regras de validação
    mask_pattern: Optional[str] = None  # Padrão de máscara
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o campo para dicionário serializável com campos UI específicos"""
        base_dict = super().to_dict()
        base_dict.update({
            'component_type': self.component_type,
            'event_handlers': self.event_handlers,
            'validation_rules': self.validation_rules,
            'mask_pattern': self.mask_pattern
        })
        return base_dict
    
    def get_ui_context(self) -> str:
        """Retorna contexto específico para UI"""
        context_parts = []
        
        if self.component_type:
            context_parts.append(f"Componente: {self.component_type}")
        
        if self.event_handlers:
            context_parts.append(f"Eventos: {', '.join(self.event_handlers)}")
        
        if self.validation_rules:
            context_parts.append(f"Validações: {', '.join(self.validation_rules)}")
        
        if self.mask_pattern:
            context_parts.append(f"Máscara: {self.mask_pattern}")
        
        return " | ".join(context_parts) if context_parts else self.context
    
    def is_validation_function(self) -> bool:
        """Verifica se é uma função de validação"""
        return self.field_type in ['VALIDATION_FUNCTION', 'FORM_VALIDATION']
    
    def is_mask_function(self) -> bool:
        """Verifica se é uma função de máscara"""
        return self.field_type in ['MASK_FUNCTION', 'INPUT_MASK']
    
    def get_ui_impact_assessment(self) -> str:
        """Retorna avaliação de impacto específica para UI"""
        if self.is_validation_function():
            return "Alto impacto - Função de validação precisa ser atualizada"
        elif self.is_mask_function():
            return "Médio impacto - Máscara precisa ser atualizada"
        else:
            return self.action_needed
