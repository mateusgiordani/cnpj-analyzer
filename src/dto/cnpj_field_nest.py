"""
Implementação CNPJField para Nest - Campos específicos de projetos NestJS
Versão: 1.0
Data: 2025-08-29
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .cnpj_field_base import CNPJFieldBase
from .cnpj_field_interface import ImpactLevel, Status

@dataclass
class CNPJFieldNest(CNPJFieldBase):
    """Implementação específica do CNPJField para NestJS"""
    
    # Campos específicos para NestJS
    nest_type: Optional[str] = None  # DTO, Controller, Service, etc.
    decorator_type: Optional[str] = None  # @Controller, @Injectable, etc.
    validation_decorators: Optional[list] = None  # @IsString, @IsNotEmpty, etc.
    property_type: Optional[str] = None  # string, number, etc.
    module_name: Optional[str] = None  # Nome do módulo
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o campo para dicionário serializável com campos NestJS específicos"""
        base_dict = super().to_dict()
        base_dict.update({
            'nest_type': self.nest_type,
            'decorator_type': self.decorator_type,
            'validation_decorators': self.validation_decorators,
            'property_type': self.property_type,
            'module_name': self.module_name
        })
        return base_dict
    
    def get_nest_context(self) -> str:
        """Retorna contexto específico para NestJS"""
        context_parts = []
        
        if self.nest_type:
            context_parts.append(f"Tipo NestJS: {self.nest_type}")
        
        if self.decorator_type:
            context_parts.append(f"Decorator: {self.decorator_type}")
        
        if self.validation_decorators:
            context_parts.append(f"Validações: {', '.join(self.validation_decorators)}")
        
        if self.property_type:
            context_parts.append(f"Tipo Propriedade: {self.property_type}")
        
        if self.module_name:
            context_parts.append(f"Módulo: {self.module_name}")
        
        return " | ".join(context_parts) if context_parts else self.context
    
    def is_dto_field(self) -> bool:
        """Verifica se é um campo de DTO"""
        return self.nest_type == 'NESTJS_DTO'
    
    def is_controller_field(self) -> bool:
        """Verifica se é um campo de Controller"""
        return self.nest_type == 'NESTJS_CONTROLLER'
    
    def is_service_field(self) -> bool:
        """Verifica se é um campo de Service"""
        return self.nest_type == 'NESTJS_SERVICE'
    
    def is_property_field(self) -> bool:
        """Verifica se é um campo de propriedade"""
        return self.nest_type == 'NESTJS_PROPERTY'
    
    def get_nest_impact_assessment(self) -> str:
        """Retorna avaliação de impacto específica para NestJS"""
        if self.is_dto_field():
            return "Alto impacto - DTO precisa ser atualizado para CNPJ alfanumérico"
        elif self.is_controller_field():
            return "Médio impacto - Controller precisa ser atualizado"
        elif self.is_service_field():
            return "Médio impacto - Service precisa ser atualizado"
        elif self.is_property_field():
            return "Alto impacto - Propriedade precisa ser atualizada"
        else:
            return self.action_needed
    
    def get_validation_status(self) -> str:
        """Retorna status de validação específico para NestJS"""
        if self.validation_decorators:
            if any('pattern' in dec.lower() for dec in self.validation_decorators):
                return "Validação com padrão - Precisa ser atualizada"
            elif any('length' in dec.lower() for dec in self.validation_decorators):
                return "Validação de tamanho - Precisa ser atualizada"
            else:
                return "Validação básica - Compatível"
        return "Sem validação específica"
