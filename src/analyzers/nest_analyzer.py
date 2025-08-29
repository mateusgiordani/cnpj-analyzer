"""
Analisador NestJS - BFF (Backend for Frontend)
Versão: 2.0
Data: 2025-08-28
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from analyzers.base_analyzer import BaseAnalyzer, CNPJField, ImpactLevel, Status

class NestAnalyzer(BaseAnalyzer):
    """Analisador específico para projetos NestJS"""
    
    def __init__(self):
        super().__init__("nest_bff")
        
        # Padrões específicos para NestJS
        self.nest_patterns = {
            'decorator_patterns': [
                r'@Controller\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Get\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Post\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Put\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Delete\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Injectable\s*\(\s*\)',
                r'@Module\s*\(\s*{',
                r'@UseGuards\s*\(\s*\)',
                r'@UseInterceptors\s*\(\s*\)',
                r'@UsePipes\s*\(\s*\)'
            ],
            'dto_patterns': [
                r'export\s+class\s+([A-Z][a-zA-Z]*Dto)',
                r'export\s+interface\s+([A-Z][a-zA-Z]*Dto)',
                r'export\s+class\s+([A-Z][a-zA-Z]*Request)',
                r'export\s+class\s+([A-Z][a-zA-Z]*Response)',
                r'@IsString\s*\(\s*\)',
                r'@IsNotEmpty\s*\(\s*\)',
                r'@IsOptional\s*\(\s*\)',
                r'@Length\s*\(\s*\d+,\s*\d+\s*\)',
                r'@Matches\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@IsCNPJ\s*\(\s*\)',
                r'@IsDocument\s*\(\s*\)',
                r'@Transform\s*\(\s*\)'
            ],
            'validation_patterns': [
                r'class-validator',
                r'@Validate\s*\(\s*\)',
                r'validate.*cnpj',
                r'cnpj.*validate',
                r'@IsCNPJ\s*\(\s*\)',
                r'@IsDocument\s*\(\s*\)',
                r'@IsString\s*\(\s*\)',
                r'@IsNotEmpty\s*\(\s*\)',
                r'@Length\s*\(\s*\d+,\s*\d+\s*\)',
                r'@Matches\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'ValidationPipe',
                r'class-transformer'
            ],
            'service_patterns': [
                r'export\s+class\s+([A-Z][a-zA-Z]*Service)',
                r'constructor\s*\(\s*private\s+([a-zA-Z_]+)\s*:\s*([A-Z][a-zA-Z]*)\s*\)',
                r'async\s+([a-zA-Z_]+)\s*\(\s*([^)]+)\s*\)\s*:\s*Promise',
                r'@Inject\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Injectable\s*\(\s*\)',
                r'export\s+class\s+([A-Z][a-zA-Z]*Repository)',
                r'export\s+class\s+([A-Z][a-zA-Z]*Provider)'
            ],
            'database_patterns': [
                r'@Entity\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Column\s*\(\s*{',
                r'@PrimaryGeneratedColumn\s*\(\s*\)',
                r'@ManyToOne\s*\(\s*\)',
                r'@OneToMany\s*\(\s*\)',
                r'@JoinColumn\s*\(\s*\)',
                r'@CreateDateColumn\s*\(\s*\)',
                r'@UpdateDateColumn\s*\(\s*\)',
                r'@Index\s*\(\s*\)',
                r'@Unique\s*\(\s*\)'
            ],
            'controller_patterns': [
                r'export\s+class\s+([A-Z][a-zA-Z]*Controller)',
                r'@Controller\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Get\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Post\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Put\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Delete\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Patch\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Query\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Param\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'@Body\s*\(\s*\)'
            ]
        }

    def get_file_extensions(self) -> List[str]:
        """Retorna as extensões de arquivo suportadas"""
        return ['.ts', '.js', '.json']

    def get_skip_patterns(self) -> List[str]:
        """Retorna padrões de arquivos para pular"""
        return [
            r'node_modules/',
            r'\.git/',
            r'dist/',
            r'build/',
            r'coverage/',
            r'\.cache/',
            r'\.vscode/',
            r'\.idea/',
            r'*.min.js',
            r'*.min.css',
            r'*.map',
            r'test/',
            r'tests/',
            r'__tests__/',
            r'*.spec.ts',
            r'*.test.ts',
            r'*.spec.js',
            r'*.test.js'
        ]

    def scan_package_json(self, project_path: Path) -> Dict[str, Any]:
        """Analisa package.json para detectar dependências e configurações NestJS"""
        package_json_path = project_path / 'package.json'
        if not package_json_path.exists():
            return {}
        
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dependencies = data.get('dependencies', {})
            dev_dependencies = data.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}
            
            # Detectar tipo de projeto
            project_type = self._detect_project_type(all_deps, data)
            
            return {
                'dependencies': dependencies,
                'devDependencies': dev_dependencies,
                'allDependencies': all_deps,
                'projectType': project_type,
                'scripts': data.get('scripts', {}),
                'name': data.get('name', ''),
                'version': data.get('version', ''),
                'nest_dependencies': self._extract_nest_dependencies(data)
            }
        except Exception as e:
            self.logger.error(f"Erro ao ler package.json: {e}")
            return {}

    def _detect_project_type(self, dependencies: Dict[str, str], package_data: Dict[str, Any]) -> str:
        """Detecta o tipo específico do projeto NestJS"""
        deps_lower = {k.lower(): v for k, v in dependencies.items()}
        
        # NestJS
        if any('@nestjs' in dep for dep in deps_lower.keys()):
            return 'nest_bff'
        
        # Verificar scripts no package.json
        scripts = package_data.get('scripts', {})
        if any('nest' in str(v).lower() for v in scripts.values()):
            return 'nest_bff'
        
        return 'nest_generic'

    def _extract_nest_dependencies(self, package_data: Dict) -> Dict[str, str]:
        """Extrai dependências específicas do NestJS"""
        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})
        all_deps = {**dependencies, **dev_dependencies}
        
        nest_deps = {}
        for dep, version in all_deps.items():
            if '@nestjs' in dep.lower():
                nest_deps[dep] = version
        
        return nest_deps

    def find_nest_specific_patterns(self, content: str, file_path: str) -> List[CNPJField]:
        """Encontra padrões específicos do NestJS"""
        fields = []
        
        # Buscar DTOs com CNPJ
        dto_patterns = [
            r'export\s+class\s+([A-Z][a-zA-Z]*Dto)',
            r'export\s+interface\s+([A-Z][a-zA-Z]*Dto)',
            r'export\s+class\s+([A-Z][a-zA-Z]*Request)',
            r'export\s+class\s+([A-Z][a-zA-Z]*Response)'
        ]
        
        for pattern in dto_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                dto_name = match.group(1)
                if 'cnpj' in dto_name.lower():
                    fields.append(CNPJField(
                        file_path=file_path,
                        line_number=match.start() + 1,
                        field_name=dto_name,
                        field_type='NESTJS_DTO',
                        field_size=None,
                        context=f"DTO NestJS: {dto_name}",
                        project_type='nest_bff',
                        impact_level=ImpactLevel.MEDIUM,
                        status=Status.NEEDS_ANALYSIS,
                        action_needed='Revisar validação de CNPJ',
                        estimated_effort='2-4 horas'
                    ))
        
        # Buscar propriedades com CNPJ em DTOs
        property_patterns = [
            r'(\w+)\s*:\s*string\s*;.*cnpj',
            r'(\w+)\s*:\s*string\s*;.*CNPJ',
            r'@IsString\s*\(\s*\)\s*(\w+)\s*:\s*string\s*;.*cnpj',
            r'@IsNotEmpty\s*\(\s*\)\s*(\w+)\s*:\s*string\s*;.*cnpj'
        ]
        
        for pattern in property_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                property_name = match.group(1)
                if 'cnpj' in property_name.lower():
                    fields.append(CNPJField(
                        file_path=file_path,
                        line_number=match.start() + 1,
                        field_name=property_name,
                        field_type='NESTJS_PROPERTY',
                        field_size=None,
                        context=f"Propriedade NestJS: {property_name}",
                        project_type='nest_bff',
                        impact_level=ImpactLevel.MEDIUM,
                        status=Status.NEEDS_ANALYSIS,
                        action_needed='Revisar validação de CNPJ',
                        estimated_effort='2-4 horas'
                    ))
        
        return fields

    def find_controllers(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra controllers NestJS"""
        controllers = []
        
        # Buscar controllers
        controller_patterns = [
            r'export\s+class\s+([A-Z][a-zA-Z]*Controller)',
            r'@Controller\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        ]
        
        for pattern in controller_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                controller_name = match.group(1)
                if 'cnpj' in controller_name.lower():
                    controllers.append({
                        'file_path': file_path,
                        'line_number': match.start() + 1,
                        'controller_name': controller_name,
                        'type': 'NESTJS_CONTROLLER'
                    })
        
        return controllers

    def find_services(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra services NestJS"""
        services = []
        
        # Buscar services
        service_patterns = [
            r'export\s+class\s+([A-Z][a-zA-Z]*Service)',
            r'export\s+class\s+([A-Z][a-zA-Z]*Repository)',
            r'export\s+class\s+([A-Z][a-zA-Z]*Provider)'
        ]
        
        for pattern in service_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                service_name = match.group(1)
                if 'cnpj' in service_name.lower():
                    services.append({
                        'file_path': file_path,
                        'line_number': match.start() + 1,
                        'service_name': service_name,
                        'type': 'NESTJS_SERVICE'
                    })
        
        return services

    def find_dtos(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra DTOs NestJS"""
        dtos = []
        
        # Buscar DTOs
        dto_patterns = [
            r'export\s+class\s+([A-Z][a-zA-Z]*Dto)',
            r'export\s+interface\s+([A-Z][a-zA-Z]*Dto)',
            r'export\s+class\s+([A-Z][a-zA-Z]*Request)',
            r'export\s+class\s+([A-Z][a-zA-Z]*Response)'
        ]
        
        for pattern in dto_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                dto_name = match.group(1)
                if 'cnpj' in dto_name.lower():
                    dtos.append({
                        'file_path': file_path,
                        'line_number': match.start() + 1,
                        'dto_name': dto_name,
                        'type': 'NESTJS_DTO'
                    })
        
        return dtos

    def find_entities(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra entities NestJS"""
        entities = []
        
        # Buscar entities
        entity_patterns = [
            r'@Entity\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            r'export\s+class\s+([A-Z][a-zA-Z]*Entity)',
            r'export\s+class\s+([A-Z][a-zA-Z]*Model)'
        ]
        
        for pattern in entity_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                entity_name = match.group(1)
                if 'cnpj' in entity_name.lower():
                    entities.append({
                        'file_path': file_path,
                        'line_number': match.start() + 1,
                        'entity_name': entity_name,
                        'type': 'NESTJS_ENTITY'
                    })
        
        return entities

    def find_cnpj_validations(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra validações de CNPJ específicas do NestJS"""
        validations = []
        
        # Padrões de validação específicos do NestJS
        validation_patterns = [
            r'@IsCNPJ\s*\(\s*\)',
            r'@IsDocument\s*\(\s*\)',
            r'@IsString\s*\(\s*\)\s*.*cnpj',
            r'@IsNotEmpty\s*\(\s*\)\s*.*cnpj',
            r'@Length\s*\(\s*\d+,\s*\d+\s*\)\s*.*cnpj',
            r'@Matches\s*\(\s*[\'"]([^\'"]*cnpj[^\'"]*)[\'"]\s*\)',
            r'validate.*cnpj',
            r'cnpj.*validate',
            r'ValidationPipe.*cnpj',
            r'class-validator.*cnpj'
        ]
        
        for pattern in validation_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                validation_text = match.group(0)
                validations.append({
                    'file_path': file_path,
                    'line_number': match.start() + 1,
                    'validation_text': validation_text,
                    'type': 'NESTJS_VALIDATION'
                })
        
        return validations

    def analyze_project(self, project_path: Path, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analisa um projeto NestJS"""
        self.logger.info(f"Analisando projeto NestJS: {project_path}")
        
        # Detectar tipo específico do projeto
        package_info = self.scan_package_json(project_path)
        project_type = package_info.get('projectType', 'nest_generic')
        
        # Escanear arquivos
        scanned_files = self.scan_files(project_path, filters)
        
        # Encontrar campos CNPJ
        cnpj_fields = self.find_cnpj_fields(scanned_files)
        
        # Buscar padrões específicos do NestJS
        nest_specific_fields = []
        controllers = []
        services = []
        dtos = []
        entities = []
        validations = []
        
        for file_info in scanned_files:
            file_path = file_info['file_path']
            content = file_info['content']
            if content:
                nest_specific_fields.extend(self.find_nest_specific_patterns(content, file_path))
                controllers.extend(self.find_controllers(content, file_path))
                services.extend(self.find_services(content, file_path))
                dtos.extend(self.find_dtos(content, file_path))
                entities.extend(self.find_entities(content, file_path))
                validations.extend(self.find_cnpj_validations(content, file_path))
        
        # Combinar campos
        all_fields = cnpj_fields + nest_specific_fields
        
        # Determinar impacto geral baseado nos campos encontrados
        if all_fields:
            if len(all_fields) > 10:
                overall_impact = ImpactLevel.HIGH
            elif len(all_fields) > 5:
                overall_impact = ImpactLevel.MEDIUM
            else:
                overall_impact = ImpactLevel.LOW
        else:
            overall_impact = ImpactLevel.LOW  # Sem campos = baixo impacto
        
        return {
            'project_name': project_path.name,
            'project_path': str(project_path),
            'project_type': f"nest_{project_type}",
            'cnpj_fields_found': all_fields,
            'validations_found': validations,
            'frontend_masks': [],  # NestJS não tem máscaras frontend
            'overall_impact': overall_impact.value if overall_impact else 'baixo',
            'package_info': package_info,
            'files_scanned': len(scanned_files),
            'framework_detected': 'nestjs',
            'nestjs_components': {
                'controllers': controllers,
                'services': services,
                'dtos': dtos,
                'entities': entities
            }
        }

    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Lê o conteúdo de um arquivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Erro ao ler arquivo {file_path}: {e}")
            return None
