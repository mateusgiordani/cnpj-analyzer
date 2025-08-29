"""
Interface CNPJField - Define o contrato para implementações de CNPJField
Versão: 1.0
Data: 2025-08-29
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

class ImpactLevel(Enum):
    """Níveis de impacto"""
    LOW = "baixo"
    MEDIUM = "medio"
    HIGH = "alto"
    CRITICAL = "critico"

class Status(Enum):
    """Status de compatibilidade"""
    COMPATIBLE = "compativel"
    ATTENTION = "atencao"
    INCOMPATIBLE = "incompativel"
    NEEDS_ANALYSIS = "precisa_analise"

class CNPJFieldInterface(ABC):
    """Interface base para CNPJField"""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Converte o campo para dicionário serializável"""
        pass
    
    @abstractmethod
    def to_json(self) -> str:
        """Converte o campo para JSON string"""
        pass
    
    @abstractmethod
    def get_impact_level(self) -> str:
        """Retorna o nível de impacto como string"""
        pass
    
    @abstractmethod
    def get_status(self) -> str:
        """Retorna o status como string"""
        pass
    
    @abstractmethod
    def get_field_type(self) -> str:
        """Retorna o tipo do campo"""
        pass
    
    @abstractmethod
    def get_file_path(self) -> str:
        """Retorna o caminho do arquivo"""
        pass
    
    @abstractmethod
    def get_line_number(self) -> int:
        """Retorna o número da linha"""
        pass
    
    @abstractmethod
    def get_field_name(self) -> str:
        """Retorna o nome do campo"""
        pass
    
    @abstractmethod
    def get_context(self) -> str:
        """Retorna o contexto do campo"""
        pass
    
    @abstractmethod
    def get_action_needed(self) -> str:
        """Retorna a ação necessária"""
        pass
    
    @abstractmethod
    def get_estimated_effort(self) -> str:
        """Retorna o esforço estimado"""
        pass
