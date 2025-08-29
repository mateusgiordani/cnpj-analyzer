"""
Analisador Base - Funcionalidades comuns para todos os analisadores
Versão: 1.0
Data: 2025-01-27
"""

import re
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from rich.console import Console

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

@dataclass
class CNPJField:
    """Representa um campo CNPJ encontrado"""
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

class BaseAnalyzer(ABC):
    """Classe base para todos os analisadores"""
    
    def __init__(self, project_type: str):
        self.project_type = project_type
        self.console = Console()
        self.logger = logging.getLogger(f"{__name__}.{project_type}")
        
        # Padrões de busca para CNPJ
        self.cnpj_patterns = {
            'field_names': [
                r'cnpj',
                r'cpf_cnpj',
                r'cpfcnpj',
                r'nr_documento',
                r'documento',
                r'numero_documento',
                r'cnpj_cpf',
                r'documento_fiscal',
                r'cpfcnpjpagador',
                r'cpf_cnpj_base',
                r'cnpj_base',
                r'cpfcnpj_indicador',
                r'cpfcnpj_indicado',
                r'cpf_cnpj_indicador',
                r'cpf_cnpj_indicado',
                r'CpfCnpj',
                r'CpfCnpjValidator'
            ],
            'validation_patterns': [
                r'cnpj.*validat',
                r'validat.*cnpj',
                r'cpf.*cnpj.*validat',
                r'documento.*validat',
                r'CpfCnpjValidator',
                r'cpfcnpj.*validat',
                r'validat.*cpfcnpj',
                r'Rule::cnpj',
                r'cnpj.*rule',
                r'rule.*cnpj'
            ],
            'mask_patterns': [
                r'cnpj.*mask',
                r'mask.*cnpj',
                r'format.*cnpj',
                r'cnpj.*format'
            ],
            'database_patterns': [
                r'VARCHAR\s*\(\s*(\d+)\s*\)',
                r'CHAR\s*\(\s*(\d+)\s*\)',
                r'TEXT',
                r'BIGINT',
                r'INT'
            ]
        }

    @abstractmethod
    def get_file_extensions(self) -> List[str]:
        """Retorna as extensões de arquivo suportadas por este analisador"""
        pass

    @abstractmethod
    def get_skip_patterns(self) -> List[str]:
        """Retorna padrões de arquivos/pastas para ignorar"""
        pass

    def scan_files(self, project_path: Path, filters: Optional[Dict] = None) -> List[Dict]:
        """Escaneia arquivos do projeto com filtros opcionais"""
        files = []
        extensions = self.get_file_extensions()
        skip_patterns = self.get_skip_patterns()
        
        # Aplicar filtros adicionais se fornecidos
        if filters:
            skip_patterns.extend(filters.get('skip_patterns', []))
            include_patterns = filters.get('include_patterns', [])
        else:
            include_patterns = []
        
        for ext in extensions:
            for file_path in project_path.rglob(f'*{ext}'):
                if file_path.is_file() and not self._should_skip_file(file_path, skip_patterns):
                    # Verificar se deve incluir baseado nos padrões de inclusão
                    if include_patterns and not self._should_include_file(file_path, include_patterns):
                        continue
                        
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        files.append({
                            'file_path': str(file_path),
                            'content': content,
                            'extension': ext
                        })
                    except Exception as e:
                        self.logger.warning(f"Erro ao ler arquivo {file_path}: {e}")
        
        return files

    def _should_skip_file(self, file_path: Path, skip_patterns: List[str]) -> bool:
        """Verifica se o arquivo deve ser ignorado"""
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _should_include_file(self, file_path: Path, include_patterns: List[str]) -> bool:
        """Verifica se o arquivo deve ser incluído baseado nos padrões"""
        return any(pattern in str(file_path) for pattern in include_patterns)

    def find_cnpj_fields(self, files: List[Dict]) -> List[CNPJField]:
        """Encontra campos relacionados a CNPJ nos arquivos"""
        cnpj_fields = []
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.cnpj_patterns['field_names']:
                    if re.search(pattern, line, re.IGNORECASE):
                        field = self._analyze_cnpj_field(
                            file_path, line_num, line
                        )
                        if field:
                            cnpj_fields.append(field)
        
        return cnpj_fields

    def _analyze_cnpj_field(self, file_path: str, line_num: int, line: str) -> Optional[CNPJField]:
        """Analisa um campo CNPJ específico"""
        # Extrair nome do campo - padrões mais abrangentes
        field_patterns = [
            r'(\w+cnpj\w*)',
            r'(\w+documento\w*)',
            r'(\w+_cnpj\w*)',
            r'(\w+_cpf_cnpj\w*)',
            r'(\w+cpfcnpj\w*)',
            r'(CpfCnpj\w*)',
            r'(CpfCnpjValidator)'
        ]
        
        field_name = None
        for pattern in field_patterns:
            field_match = re.search(pattern, line, re.IGNORECASE)
            if field_match:
                field_name = field_match.group(1)
                break
                
        if not field_name:
            return None
        
        # Determinar tipo e tamanho do campo
        field_type, field_size = self._extract_field_type_and_size(line)
        
        # Determinar impacto e status
        impact_level, status, action_needed = self._assess_impact(field_type, field_size)
        
        return CNPJField(
            file_path=file_path,
            line_number=line_num,
            field_name=field_name,
            field_type=field_type,
            field_size=field_size,
            context=line.strip(),
            project_type=self.project_type,
            impact_level=impact_level,
            status=status,
            action_needed=action_needed,
            estimated_effort=self._estimate_effort(impact_level)
        )

    def _extract_field_type_and_size(self, line: str) -> tuple:
        """Extrai tipo e tamanho do campo da linha"""
        # Padrões para diferentes tipos de campo SQL padrão
        varchar_match = re.search(r'VARCHAR\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
        char_match = re.search(r'CHAR\s*\(\s*(\d+)\s*\)', line, re.IGNORECASE)
        text_match = re.search(r'TEXT', line, re.IGNORECASE)
        int_match = re.search(r'INT|BIGINT', line, re.IGNORECASE)
        
        # Padrões para migrations do Phinx (PHP)
        phinx_string_match = re.search(r"'string'.*'length'.*=>\s*(\d+)", line, re.IGNORECASE)
        phinx_char_match = re.search(r"'char'.*'length'.*=>\s*(\d+)", line, re.IGNORECASE)
        phinx_text_match = re.search(r"'text'", line, re.IGNORECASE)
        phinx_integer_match = re.search(r"'integer'", line, re.IGNORECASE)
        
        # Padrões para Laravel migrations
        laravel_string_match = re.search(r'\$table->string\s*\(\s*[\'"][^\'"]+[\'"]\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
        laravel_integer_match = re.search(r'\$table->integer\s*\(\s*[\'"][^\'"]+[\'"]\s*\)', line, re.IGNORECASE)
        laravel_text_match = re.search(r'\$table->text\s*\(\s*[\'"][^\'"]+[\'"]\s*\)', line, re.IGNORECASE)
        
        # Verificar padrões SQL primeiro
        if varchar_match:
            return 'VARCHAR', int(varchar_match.group(1))
        elif char_match:
            return 'CHAR', int(char_match.group(1))
        elif text_match:
            return 'TEXT', None
        elif int_match:
            return 'INTEGER', None
        
        # Verificar padrões Phinx
        elif phinx_string_match:
            return 'VARCHAR', int(phinx_string_match.group(1))
        elif phinx_char_match:
            return 'CHAR', int(phinx_char_match.group(1))
        elif phinx_text_match:
            return 'TEXT', None
        elif phinx_integer_match:
            return 'INTEGER', None
        
        # Verificar padrões Laravel
        elif laravel_string_match:
            return 'VARCHAR', int(laravel_string_match.group(1))
        elif laravel_integer_match:
            return 'INTEGER', None
        elif laravel_text_match:
            return 'TEXT', None
        
        else:
            return 'UNKNOWN', None

    def _assess_impact(self, field_type: str, field_size: Optional[int]) -> tuple:
        """Avalia o impacto da mudança do CNPJ alfanumérico"""
        # CNPJ alfanumérico requer mínimo 14 caracteres (formato atual) e idealmente 18 para futuro
        min_cnpj_size = 14
        ideal_cnpj_size = 18
        
        if field_type == 'INTEGER':
            return ImpactLevel.HIGH, Status.INCOMPATIBLE, "Alterar tipo para VARCHAR(18)"
        elif field_type == 'VARCHAR':
            if field_size and field_size < min_cnpj_size:
                return ImpactLevel.CRITICAL, Status.INCOMPATIBLE, f"CRÍTICO: Tamanho {field_size} < {min_cnpj_size}. Alterar para VARCHAR(18)"
            elif field_size and field_size < ideal_cnpj_size:
                return ImpactLevel.MEDIUM, Status.ATTENTION, f"Aumentar tamanho de {field_size} para {ideal_cnpj_size}"
            elif field_size and field_size >= ideal_cnpj_size:
                return ImpactLevel.LOW, Status.COMPATIBLE, "Nenhuma alteração necessária"
            else:
                return ImpactLevel.MEDIUM, Status.NEEDS_ANALYSIS, "Análise manual necessária"
        elif field_type == 'CHAR':
            if field_size and field_size < min_cnpj_size:
                return ImpactLevel.CRITICAL, Status.INCOMPATIBLE, f"CRÍTICO: Tamanho {field_size} < {min_cnpj_size}. Alterar para VARCHAR(18)"
            elif field_size and field_size < ideal_cnpj_size:
                return ImpactLevel.MEDIUM, Status.ATTENTION, f"Alterar para VARCHAR(18) ou aumentar CHAR para {ideal_cnpj_size}"
            else:
                return ImpactLevel.LOW, Status.COMPATIBLE, "Nenhuma alteração necessária"
        elif field_type == 'TEXT':
            return ImpactLevel.LOW, Status.COMPATIBLE, "Nenhuma alteração necessária"
        else:
            return ImpactLevel.MEDIUM, Status.NEEDS_ANALYSIS, "Análise manual necessária"

    def _estimate_effort(self, impact_level: ImpactLevel) -> str:
        """Estima o esforço necessário baseado no nível de impacto"""
        effort_map = {
            ImpactLevel.LOW: "1-2 horas",
            ImpactLevel.MEDIUM: "4-8 horas",
            ImpactLevel.HIGH: "1-2 dias",
            ImpactLevel.CRITICAL: "2-5 dias"
        }
        return effort_map.get(impact_level, "A definir")

    def find_validations(self, files: List[Dict]) -> List[Dict]:
        """Encontra validações relacionadas a CNPJ"""
        validations = []
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.cnpj_patterns['validation_patterns']:
                    if re.search(pattern, line, re.IGNORECASE):
                        validations.append({
                            'file_path': file_path,
                            'line_number': line_num,
                            'line': line.strip(),
                            'validation_type': 'CNPJ'
                        })
        
        return validations

    def find_frontend_masks(self, files: List[Dict]) -> List[Dict]:
        """Encontra máscaras de CNPJ no frontend"""
        masks = []
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.cnpj_patterns['mask_patterns']:
                    if re.search(pattern, line, re.IGNORECASE):
                        masks.append({
                            'file_path': file_path,
                            'line_number': line_num,
                            'line': line.strip(),
                            'mask_type': 'CNPJ'
                        })
        
        return masks

    def analyze_project(self, project_path: Path, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Analisa um projeto e retorna os resultados"""
        project_name = project_path.name if hasattr(project_path, 'name') else str(project_path).split('/')[-1]
        self.console.print(f"[blue]Analisando projeto {self.project_type}: {project_name}[/blue]")
        
        # Escanear arquivos com filtros
        files = self.scan_files(project_path, filters)
        
        # Encontrar campos CNPJ
        cnpj_fields = self.find_cnpj_fields(files)
        
        # Encontrar validações
        validations = self.find_validations(files)
        
        # Encontrar máscaras
        masks = self.find_frontend_masks(files)
        
        return {
            'project_type': self.project_type,
            'total_files_scanned': len(files),
            'cnpj_fields_found': cnpj_fields,
            'validations': validations,
            'frontend_masks': masks,
            'files': files
        }
