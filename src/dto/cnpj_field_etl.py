"""
Implementação CNPJField para ETL - Campos específicos de projetos ETL
Versão: 1.0
Data: 2025-08-29
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .cnpj_field_base import CNPJFieldBase
from .cnpj_field_interface import ImpactLevel, Status

@dataclass
class CNPJFieldETL(CNPJFieldBase):
    """Implementação específica do CNPJField para ETL"""
    
    # Campos específicos para ETL
    etl_tool: Optional[str] = None  # Pentaho, Talend, etc.
    etl_type: Optional[str] = None  # Transformation, Job, etc.
    data_type: Optional[str] = None  # VARCHAR, STRING, etc.
    transformation_step: Optional[str] = None  # Nome do step/componente
    source_target: Optional[str] = None  # Source, Target, etc.
    validation_rule: Optional[str] = None  # Regra de validação ETL
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o campo para dicionário serializável com campos ETL específicos"""
        base_dict = super().to_dict()
        base_dict.update({
            'etl_tool': self.etl_tool,
            'etl_type': self.etl_type,
            'data_type': self.data_type,
            'transformation_step': self.transformation_step,
            'source_target': self.source_target,
            'validation_rule': self.validation_rule
        })
        return base_dict
    
    def get_etl_context(self) -> str:
        """Retorna contexto específico para ETL"""
        context_parts = []
        
        if self.etl_tool:
            context_parts.append(f"Ferramenta ETL: {self.etl_tool}")
        
        if self.etl_type:
            context_parts.append(f"Tipo ETL: {self.etl_type}")
        
        if self.data_type:
            context_parts.append(f"Tipo Dados: {self.data_type}")
        
        if self.transformation_step:
            context_parts.append(f"Step: {self.transformation_step}")
        
        if self.source_target:
            context_parts.append(f"Origem/Destino: {self.source_target}")
        
        if self.validation_rule:
            context_parts.append(f"Validação: {self.validation_rule}")
        
        return " | ".join(context_parts) if context_parts else self.context
    
    def is_pentaho_field(self) -> bool:
        """Verifica se é um campo Pentaho"""
        return self.etl_tool == 'Pentaho'
    
    def is_sql_field(self) -> bool:
        """Verifica se é um campo SQL"""
        return self.etl_tool == 'SQL'
    
    def is_python_etl_field(self) -> bool:
        """Verifica se é um campo Python ETL"""
        return self.etl_tool == 'Python'
    
    def is_transformation_field(self) -> bool:
        """Verifica se é um campo de transformação"""
        return self.etl_type == 'Transformation'
    
    def is_job_field(self) -> bool:
        """Verifica se é um campo de job"""
        return self.etl_type == 'Job'
    
    def get_etl_impact_assessment(self) -> str:
        """Retorna avaliação de impacto específica para ETL"""
        if self.is_pentaho_field():
            if self.is_transformation_field():
                return "Alto impacto - Transformação Pentaho precisa ser atualizada"
            elif self.is_job_field():
                return "Médio impacto - Job Pentaho precisa ser atualizado"
        elif self.is_sql_field():
            return "Alto impacto - Script SQL precisa ser atualizado"
        elif self.is_python_etl_field():
            return "Médio impacto - Script Python ETL precisa ser atualizado"
        
        return self.action_needed
    
    def get_data_type_compatibility(self) -> str:
        """Retorna compatibilidade do tipo de dados"""
        if self.data_type:
            if 'VARCHAR' in self.data_type.upper() or 'STRING' in self.data_type.upper():
                return "Compatível com CNPJ alfanumérico"
            elif 'INT' in self.data_type.upper() or 'NUMBER' in self.data_type.upper():
                return "Incompatível - Precisa ser alterado para VARCHAR/STRING"
            else:
                return "Análise necessária"
        return "Tipo de dados não identificado"
    
    def get_validation_impact(self) -> str:
        """Retorna impacto da validação ETL"""
        if self.validation_rule:
            if 'pattern' in self.validation_rule.lower():
                return "Validação com padrão - Precisa ser atualizada"
            elif 'length' in self.validation_rule.lower():
                return "Validação de tamanho - Precisa ser atualizada"
            else:
                return "Validação básica - Compatível"
        return "Sem validação específica"
