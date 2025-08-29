"""
Factory para extractors de tipos
Versão: 1.0
Data: 2025-08-29
"""

from typing import Dict, Type
from .base_type_extractor import BaseTypeExtractor
from .typescript_extractor import TypeScriptExtractor
from .php_extractor import PHPExtractor
from .sql_extractor import SQLExtractor
from .etl_extractor import ETLExtractor

class TypeExtractorFactory:
    """Factory para criar extractors de tipos baseado na extensão do arquivo"""
    
    def __init__(self):
        self._extractors: Dict[str, Type[BaseTypeExtractor]] = {
            # TypeScript/NestJS
            '.ts': TypeScriptExtractor,
            '.tsx': TypeScriptExtractor,
            
            # PHP
            '.php': PHPExtractor,
            
            # SQL
            '.sql': SQLExtractor,
            
            # ETL
            '.ktr': ETLExtractor,
            '.kjb': ETLExtractor,
            '.xml': ETLExtractor,
            '.xsd': ETLExtractor,
            '.csv': ETLExtractor,
            '.txt': ETLExtractor,
        }
    
    def get_extractor(self, file_path: str) -> BaseTypeExtractor:
        """
        Retorna o extractor apropriado para o arquivo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Extractor apropriado para o tipo de arquivo
        """
        # Encontrar a extensão do arquivo
        for ext in self._extractors.keys():
            if file_path.lower().endswith(ext):
                extractor_class = self._extractors[ext]
                return extractor_class()
        
        # Se não encontrar, usar o extractor mais genérico baseado no conteúdo
        return self._get_fallback_extractor(file_path)
    
    def _get_fallback_extractor(self, file_path: str) -> BaseTypeExtractor:
        """
        Retorna um extractor de fallback baseado no conteúdo do arquivo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Extractor de fallback
        """
        # Por padrão, usar SQL extractor como fallback
        return SQLExtractor()
    
    def register_extractor(self, extension: str, extractor_class: Type[BaseTypeExtractor]):
        """
        Registra um novo extractor para uma extensão
        
        Args:
            extension: Extensão do arquivo (ex: '.py')
            extractor_class: Classe do extractor
        """
        self._extractors[extension] = extractor_class
    
    def get_supported_extensions(self) -> list:
        """
        Retorna todas as extensões suportadas
        
        Returns:
            Lista de extensões suportadas
        """
        return list(self._extractors.keys())
    
    def is_supported_file(self, file_path: str) -> bool:
        """
        Verifica se o arquivo é suportado
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se suportado, False caso contrário
        """
        return any(file_path.lower().endswith(ext) for ext in self._extractors.keys())
