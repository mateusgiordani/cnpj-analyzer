"""
Implementação Base CNPJField - Implementação padrão do CNPJField
Versão: 1.0
Data: 2025-08-29
"""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .cnpj_field_interface import CNPJFieldInterface, ImpactLevel, Status

@dataclass
class CNPJFieldBase(CNPJFieldInterface):
    """Implementação base do CNPJField"""
    
    file_path: str
    line_number: int
    field_name: str
    field_type: str
    field_size: Optional[int]
    context: str
    project_type: str
    impact_level: ImpactLevel
    status: Status
    action_needed: str
    estimated_effort: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o campo para dicionário serializável"""
        return {
            'file_path': self.file_path,
            'line_number': self.line_number,
            'field_name': self.field_name,
            'field_type': self.field_type,
            'field_size': self.field_size,
            'context': self.context,
            'project_type': self.project_type,
            'impact_level': self.impact_level.value,
            'status': self.status.value,
            'action_needed': self.action_needed,
            'estimated_effort': self.estimated_effort
        }
    
    def to_json(self) -> str:
        """Converte o campo para JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def get_impact_level(self) -> str:
        """Retorna o nível de impacto como string"""
        return self.impact_level.value
    
    def get_status(self) -> str:
        """Retorna o status como string"""
        return self.status.value
    
    def get_field_type(self) -> str:
        """Retorna o tipo do campo"""
        return self.field_type
    
    def get_file_path(self) -> str:
        """Retorna o caminho do arquivo"""
        return self.file_path
    
    def get_line_number(self) -> int:
        """Retorna o número da linha"""
        return self.line_number
    
    def get_field_name(self) -> str:
        """Retorna o nome do campo"""
        return self.field_name
    
    def get_context(self) -> str:
        """Retorna o contexto do campo"""
        return self.context
    
    def get_action_needed(self) -> str:
        """Retorna a ação necessária"""
        return self.action_needed
    
    def get_estimated_effort(self) -> str:
        """Retorna o esforço estimado"""
        return self.estimated_effort
