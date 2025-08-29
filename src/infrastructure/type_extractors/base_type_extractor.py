"""
Extractor base para tipos de campos
Versão: 1.0
Data: 2025-08-29
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional

class BaseTypeExtractor(ABC):
    """Classe base para extractors de tipos de campos"""
    
    @abstractmethod
    def extract_type_and_size(self, line: str) -> Tuple[str, Optional[int]]:
        """
        Extrai tipo e tamanho do campo da linha
        
        Args:
            line: Linha do código
            
        Returns:
            Tuple com (tipo, tamanho)
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> list:
        """
        Retorna as extensões de arquivo suportadas
        
        Returns:
            Lista de extensões suportadas
        """
        pass
    
    def is_supported_file(self, file_path: str) -> bool:
        """
        Verifica se o arquivo é suportado por este extractor
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se suportado, False caso contrário
        """
        extensions = self.get_supported_extensions()
        return any(file_path.lower().endswith(ext) for ext in extensions)
