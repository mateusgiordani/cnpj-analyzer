"""
Analisador UI - React, Vue, Angular
Versão: 1.0
Data: 2025-01-27
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base_analyzer import BaseAnalyzer
from dto import CNPJFieldUI, CNPJFieldInterface, ImpactLevel, Status

class UIAnalyzer(BaseAnalyzer):
    """Analisador específico para projetos de UI"""
    
    def __init__(self, framework: str = "ui"):
        super().__init__(f"ui_{framework}", CNPJFieldUI)
        self.framework = framework
        
        # Padrões específicos para UI
        self.ui_patterns = {
            'react': {
                'component_patterns': [
                    r'function\s+([A-Z][a-zA-Z]*)\s*\(.*\)\s*{',
                    r'const\s+([A-Z][a-zA-Z]*)\s*=\s*\(.*\)\s*=>',
                    r'class\s+([A-Z][a-zA-Z]*)\s+extends\s+Component',
                    r'export\s+default\s+([A-Z][a-zA-Z]*)'
                ],
                'hook_patterns': [
                    r'useState\s*\(\s*[\'"]([^\'"]*cnpj[^\'"]*)[\'"]',
                    r'useEffect\s*\(\s*\(\)\s*=>\s*{',
                    r'const\s+\[([^,]+),\s*set([^,]+)\]\s*=\s*useState'
                ],
                'validation_patterns': [
                    r'validate.*cnpj',
                    r'cnpj.*validate',
                    r'pattern.*cnpj',
                    r'cnpj.*pattern'
                ],
                'mask_patterns': [
                    r'mask.*cnpj',
                    r'cnpj.*mask',
                    r'format.*cnpj',
                    r'cnpj.*format',
                    r'input.*mask',
                    r'mask.*input'
                ]
            },
            'vue': {
                'component_patterns': [
                    r'export\s+default\s*{',
                    r'name:\s*[\'"]([^\'"]+)[\'"]',
                    r'props:\s*{',
                    r'data\s*\(\s*\)\s*{'
                ],
                'validation_patterns': [
                    r'v-validate.*cnpj',
                    r'cnpj.*v-validate',
                    r'@input.*validate',
                    r'validate.*@input'
                ],
                'mask_patterns': [
                    r'v-mask.*cnpj',
                    r'cnpj.*v-mask',
                    r'@input.*mask',
                    r'mask.*@input'
                ]
            },
            'angular': {
                'component_patterns': [
                    r'@Component\s*\(\s*{',
                    r'export\s+class\s+([A-Z][a-zA-Z]*)',
                    r'selector:\s*[\'"]([^\'"]+)[\'"]',
                    r'templateUrl:\s*[\'"]([^\'"]+)[\'"]'
                ],
                'validation_patterns': [
                    r'Validators\.pattern',
                    r'cnpj.*validator',
                    r'validator.*cnpj',
                    r'@Input.*cnpj'
                ],
                'mask_patterns': [
                    r'mask.*cnpj',
                    r'cnpj.*mask',
                    r'@Input.*mask',
                    r'mask.*@Input'
                ]
            }
        }

    def get_file_extensions(self) -> List[str]:
        """Retorna as extensões de arquivo suportadas"""
        extensions = {
            'react': ['.tsx', '.ts', '.jsx', '.js', '.json'],
            'vue': ['.vue', '.ts', '.js', '.json'],
            'angular': ['.ts', '.js', '.html', '.json']
        }
        return extensions.get(self.framework, ['.tsx', '.ts', '.jsx', '.js', '.vue', '.html', '.json'])

    def get_skip_patterns(self) -> List[str]:
        """Retorna padrões de arquivos/pastas para ignorar"""
        return [
            'node_modules', 'vendor', '.git', '__pycache__', 
            '.venv', 'venv', 'dist', 'build', '.next', '.nuxt',
            '.angular', 'coverage', '.nyc_output', '.cache'
        ]

    def scan_package_json(self, project_path: Path) -> Dict[str, Any]:
        """Escaneia package.json para informações do projeto"""
        package_json_path = project_path / 'package.json'
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                return {
                    'name': package_data.get('name', ''),
                    'version': package_data.get('version', ''),
                    'dependencies': package_data.get('dependencies', {}),
                    'devDependencies': package_data.get('devDependencies', {}),
                    'scripts': package_data.get('scripts', {})
                }
            except (json.JSONDecodeError, FileNotFoundError) as e:
                self.logger.warning(f"Erro ao ler package.json: {e}")
        
        return {}

    def find_ui_specific_patterns(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Encontra padrões específicos da UI"""
        patterns = self.ui_patterns.get(self.framework, {})
        results = {}
        
        for pattern_type, pattern_list in patterns.items():
            results[pattern_type] = []
            
            for file_info in files:
                file_path = file_info['file_path']
                content = file_info['content']
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in pattern_list:
                        if re.search(pattern, line, re.IGNORECASE):
                            results[pattern_type].append({
                                'file_path': file_path,
                                'line_number': line_num,
                                'line': line.strip(),
                                'pattern_type': pattern_type
                            })
        
        return results

    def find_react_specific(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Encontra padrões específicos do React"""
        if self.framework != 'react':
            return {}
        
        react_patterns = {
            'components': [],
            'hooks': [],
            'forms': [],
            'validations': []
        }
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            
            # Detectar componentes React
            if re.search(r'function\s+[A-Z]|const\s+[A-Z].*=|class\s+[A-Z]', content):
                react_patterns['components'].append({
                    'file_path': file_path,
                    'content': content
                })
            
            # Detectar hooks
            if re.search(r'useState|useEffect|useCallback|useMemo', content):
                react_patterns['hooks'].append({
                    'file_path': file_path,
                    'content': content
                })
            
            # Detectar formulários
            if re.search(r'form.*onSubmit|handleSubmit|Formik|react-hook-form', content, re.IGNORECASE):
                react_patterns['forms'].append({
                    'file_path': file_path,
                    'content': content
                })
            
            # Detectar validações
            if re.search(r'validate|validation|yup|joi', content, re.IGNORECASE):
                react_patterns['validations'].append({
                    'file_path': file_path,
                    'content': content
                })
        
        return react_patterns

    def find_vue_specific(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Encontra padrões específicos do Vue"""
        if self.framework != 'vue':
            return {}
        
        vue_patterns = {
            'components': [],
            'directives': [],
            'forms': [],
            'validations': []
        }
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            
            # Detectar componentes Vue
            if re.search(r'export\s+default|Vue\.component|defineComponent', content):
                vue_patterns['components'].append({
                    'file_path': file_path,
                    'content': content
                })
            
            # Detectar diretivas
            if re.search(r'v-|@[a-z]+', content):
                vue_patterns['directives'].append({
                    'file_path': file_path,
                    'content': content
                })
            
            # Detectar formulários
            if re.search(r'v-model|@submit|form.*@submit', content):
                vue_patterns['forms'].append({
                    'file_path': file_path,
                    'content': content
                })
            
            # Detectar validações
            if re.search(r'v-validate|vee-validate|@input.*validate', content):
                vue_patterns['validations'].append({
                    'file_path': file_path,
                    'content': content
                })
        
        return vue_patterns

    def find_angular_specific(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Encontra padrões específicos do Angular"""
        if self.framework != 'angular':
            return {}
        
        angular_patterns = {
            'components': [],
            'services': [],
            'forms': [],
            'validations': []
        }
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            
            # Detectar componentes Angular
            if re.search(r'@Component|export\s+class.*Component', content):
                angular_patterns['components'].append({
                    'file_path': file_path,
                    'content': content
                })
            
            # Detectar serviços
            if re.search(r'@Injectable|export\s+class.*Service', content):
                angular_patterns['services'].append({
                    'file_path': file_path,
                    'content': content
                })
            
            # Detectar formulários
            if re.search(r'FormGroup|FormControl|ReactiveFormsModule', content):
                angular_patterns['forms'].append({
                    'file_path': file_path,
                    'content': content
                })
            
            # Detectar validações
            if re.search(r'Validators|AbstractControl|ValidationErrors', content):
                angular_patterns['validations'].append({
                    'file_path': file_path,
                    'content': content
                })
        
        return angular_patterns

    def find_input_masks(self, files: List[Dict]) -> List[CNPJFieldInterface]:
        """Encontra máscaras de input específicas para UI"""
        masks = []
        
        mask_patterns = [
            r'mask.*cnpj',
            r'cnpj.*mask',
            r'format.*cnpj',
            r'cnpj.*format',
            r'input.*mask',
            r'mask.*input',
            r'v-mask',
            r'react-input-mask',
            r'ngx-mask',
            r'pattern.*[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}',
            r'[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}'
        ]
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in mask_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Extrair nome do campo
                        field_name = self._extract_field_name_from_line(line)
                        if field_name:
                            masks.append(self.create_cnpj_field(
                                file_path=file_path,
                                line_number=line_num,
                                field_name=field_name,
                                field_type='INPUT_MASK',
                                field_size=None,
                                context=line.strip(),
                                project_type=self.project_type,
                                impact_level=ImpactLevel.MEDIUM,
                                status=Status.NEEDS_ANALYSIS,
                                action_needed='Máscara de input precisa ser atualizada para CNPJ alfanumérico',
                                estimated_effort='4-8 horas',
                                component_type=self._extract_component_type(file_path),
                                mask_pattern=self._extract_mask_pattern(line)
                            ))
        
        return masks

    def find_validations(self, files: List[Dict]) -> List[CNPJFieldInterface]:
        """Encontra validações relacionadas a CNPJ - versão UI"""
        validations = []
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.cnpj_patterns['validation_patterns']:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Extrair nome do campo
                        field_name = self._extract_field_name_from_line(line)
                        if field_name:
                            validations.append(self.create_cnpj_field(
                                file_path=file_path,
                                line_number=line_num,
                                field_name=field_name,
                                field_type='VALIDATION_FUNCTION',
                                field_size=None,
                                context=line.strip(),
                                project_type=self.project_type,
                                impact_level=ImpactLevel.HIGH,
                                status=Status.NEEDS_ANALYSIS,
                                action_needed='Função de validação precisa ser atualizada para CNPJ alfanumérico',
                                estimated_effort='1-2 dias',
                                component_type=self._extract_component_type(file_path),
                                validation_rules=['validate']
                            ))
        
        return validations

    def find_frontend_masks(self, files: List[Dict]) -> List[CNPJFieldInterface]:
        """Encontra máscaras de CNPJ no frontend - versão UI"""
        masks = []
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.cnpj_patterns['mask_patterns']:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Extrair nome do campo
                        field_name = self._extract_field_name_from_line(line)
                        if field_name:
                            masks.append(self.create_cnpj_field(
                                file_path=file_path,
                                line_number=line_num,
                                field_name=field_name,
                                field_type='MASK_FUNCTION',
                                field_size=None,
                                context=line.strip(),
                                project_type=self.project_type,
                                impact_level=ImpactLevel.MEDIUM,
                                status=Status.NEEDS_ANALYSIS,
                                action_needed='Máscara precisa ser atualizada para CNPJ alfanumérico',
                                estimated_effort='4-8 horas',
                                component_type=self._extract_component_type(file_path),
                                mask_pattern=self._extract_mask_pattern(line)
                            ))
        
        return masks

    def _extract_field_name_from_line(self, line: str) -> Optional[str]:
        """Extrai nome do campo de uma linha"""
        field_patterns = [
            r'(\w*cnpj\w*)',
            r'(\w*documento\w*)',
            r'(\w*_cnpj\w*)',
            r'(\w*_cpf_cnpj\w*)',
            r'(\w*cpfcnpj\w*)',
            r'(CpfCnpj\w*)',
            r'(CpfCnpjValidator)',
            r'(validateCpfCnpj)',
            r'(validate.*cnpj)',
            r'(cnpj.*validate)',
            r'(\w*cnpj\w*)',  # Padrão mais genérico
            r'(\w*CNPJ\w*)',  # Maiúsculas
            r'(\w*Cnpj\w*)',  # CamelCase
            r'(\w*cnpj\w*)',  # Minúsculas
            r'(\w*_cnpj\w*)', # Com underscore
            r'(\w*-cnpj\w*)', # Com hífen
            r'(\w*\.cnpj\w*)', # Com ponto
        ]
        
        for pattern in field_patterns:
            field_match = re.search(pattern, line, re.IGNORECASE)
            if field_match:
                return field_match.group(1)
        
        return None

    def _extract_component_type(self, file_path: str) -> Optional[str]:
        """Extrai o tipo de componente baseado no arquivo"""
        file_path_lower = file_path.lower()
        if '.vue' in file_path_lower:
            return 'Vue'
        elif '.tsx' in file_path_lower or '.jsx' in file_path_lower:
            return 'React'
        elif 'angular' in file_path_lower or '.component.' in file_path_lower:
            return 'Angular'
        return None

    def _extract_event_handlers(self, line: str) -> Optional[list]:
        """Extrai event handlers da linha"""
        handlers = []
        event_patterns = [
            r'@([a-z]+)',
            r'on([A-Z][a-z]+)',
            r'\(([a-z]+)\)'
        ]
        
        for pattern in event_patterns:
            matches = re.findall(pattern, line)
            handlers.extend(matches)
        
        return handlers if handlers else None

    def _extract_validation_rules(self, line: str) -> Optional[list]:
        """Extrai regras de validação da linha"""
        rules = []
        validation_patterns = [
            r'required',
            r'minLength',
            r'maxLength',
            r'pattern',
            r'validate'
        ]
        
        for pattern in validation_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                rules.append(pattern)
        
        return rules if rules else None

    def _extract_mask_pattern(self, line: str) -> Optional[str]:
        """Extrai padrão de máscara da linha"""
        mask_patterns = [
            r'v-mask\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'mask\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'format\s*=\s*[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in mask_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def find_form_validations(self, files: List[Dict]) -> List[CNPJFieldInterface]:
        """Encontra validações de formulário específicas para UI"""
        validations = []
        
        validation_patterns = [
            r'validate.*cnpj',
            r'cnpj.*validate',
            r'pattern.*cnpj',
            r'cnpj.*pattern',
            r'required.*cnpj',
            r'cnpj.*required',
            r'minLength.*14',
            r'maxLength.*18',
            r'[0-9]{14}',
            r'[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}'
        ]
        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in validation_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Extrair nome do campo
                        field_name = self._extract_field_name_from_line(line)
                        if field_name:
                            validations.append(self.create_cnpj_field(
                                file_path=file_path,
                                line_number=line_num,
                                field_name=field_name,
                                field_type='FORM_VALIDATION',
                                field_size=None,
                                context=line.strip(),
                                project_type=self.project_type,
                                impact_level=ImpactLevel.MEDIUM,
                                status=Status.NEEDS_ANALYSIS,
                                action_needed='Validação de formulário precisa ser atualizada para CNPJ alfanumérico',
                                estimated_effort='4-8 horas',
                                component_type=self._extract_component_type(file_path),
                                validation_rules=self._extract_validation_rules(line)
                            ))
        
        return validations

    def find_cnpj_fields(self, files: List[Dict]) -> List[CNPJFieldInterface]:
        """Encontra campos relacionados a CNPJ nos arquivos UI"""
        cnpj_fields = []
        

        
        for file_info in files:
            file_path = file_info['file_path']
            content = file_info['content']
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.cnpj_patterns['field_names']:
                    if re.search(pattern, line, re.IGNORECASE):
                        field = self._analyze_ui_cnpj_field(
                            file_path, line_num, line, content
                        )
                        if field:
                            cnpj_fields.append(field)
        

        return cnpj_fields

    def _analyze_ui_cnpj_field(self, file_path: str, line_num: int, line: str, full_content: str) -> Optional[CNPJFieldInterface]:
        """Analisa um campo CNPJ específico em arquivos UI"""
        # Extrair nome do campo - padrões mais abrangentes
        field_patterns = [
            r'(\w*cnpj\w*)',
            r'(\w*documento\w*)',
            r'(\w*_cnpj\w*)',
            r'(\w*_cpf_cnpj\w*)',
            r'(\w*cpfcnpj\w*)',
            r'(CpfCnpj\w*)',
            r'(CpfCnpjValidator)',
            r'(validateCpfCnpj)',
            r'(validate.*cnpj)',
            r'(cnpj.*validate)',
            r'(\w*cnpj\w*)',  # Padrão mais genérico
            r'(\w*CNPJ\w*)',  # Maiúsculas
            r'(\w*Cnpj\w*)',  # CamelCase
            r'(\w*cnpj\w*)',  # Minúsculas
            r'(\w*_cnpj\w*)', # Com underscore
            r'(\w*-cnpj\w*)', # Com hífen
            r'(\w*\.cnpj\w*)', # Com ponto
        ]
        
        field_name = None
        for pattern in field_patterns:
            field_match = re.search(pattern, line, re.IGNORECASE)
            if field_match:
                field_name = field_match.group(1)
                break
                
        if not field_name:
            return None
        
        # Determinar tipo e tamanho do campo para UI
        field_type, field_size = self._extract_ui_field_type_and_size(line, full_content)
        
        # Determinar impacto e status
        impact_level, status, action_needed = self._assess_ui_impact(field_type, field_size)
        
        # Extrair informações específicas para UI
        component_type = self._extract_component_type(file_path)
        event_handlers = self._extract_event_handlers(line)
        validation_rules = self._extract_validation_rules(line)
        mask_pattern = self._extract_mask_pattern(line)
        
        return self.create_cnpj_field(
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
            estimated_effort=self._estimate_effort(impact_level),
            component_type=component_type,
            event_handlers=event_handlers,
            validation_rules=validation_rules,
            mask_pattern=mask_pattern
        )

    def _extract_ui_field_type_and_size(self, line: str, full_content: str) -> tuple:
        """Extrai tipo e tamanho do campo da linha para arquivos UI"""
        line_lower = line.lower()
        
        # Padrões para Vue props
        if re.search(r'@prop|public\s+\w+!:', line, re.IGNORECASE):
            # Verificar se é string, number, etc.
            if re.search(r':\s*string|string\s*!', line, re.IGNORECASE):
                return 'STRING', None
            elif re.search(r':\s*number|number\s*!', line, re.IGNORECASE):
                return 'NUMBER', None
            elif re.search(r':\s*boolean|boolean\s*!', line, re.IGNORECASE):
                return 'BOOLEAN', None
            else:
                return 'STRING', None  # Default para props
        
        # Padrões para variáveis JavaScript/TypeScript
        elif re.search(r'const\s+\w+|let\s+\w+|var\s+\w+', line, re.IGNORECASE):
            if re.search(r'=.*[\'"][^\'"]*[\'"]', line):  # String literal
                return 'STRING', None
            elif re.search(r'=.*\d+', line):  # Number literal
                return 'NUMBER', None
            else:
                return 'STRING', None  # Default para variáveis
        
        # Padrões para v-model (Vue)
        elif re.search(r'v-model', line, re.IGNORECASE):
            return 'STRING', None
        
        # Padrões para formulários
        elif re.search(r'form.*cnpj|cnpj.*form', line, re.IGNORECASE):
            return 'STRING', None
        
        # Padrões para validações
        elif re.search(r'validate.*cnpj|cnpj.*validate', line, re.IGNORECASE):
            return 'VALIDATION_FUNCTION', None
        
        # Padrões para eventos Vue com funções de validação
        elif re.search(r'@[a-z]+.*validate.*cnpj|@[a-z]+.*cnpj.*validate', line, re.IGNORECASE):
            return 'VALIDATION_FUNCTION', None
        
        # Padrões para funções de validação em eventos
        elif re.search(r'@change.*validate|@input.*validate|@blur.*validate', line, re.IGNORECASE):
            return 'VALIDATION_FUNCTION', None
        
        # Padrões para máscaras
        elif re.search(r'mask.*cnpj|cnpj.*mask', line, re.IGNORECASE):
            return 'STRING', None
        
        # Padrões para APIs/requests
        elif re.search(r'api.*cnpj|cnpj.*api|request.*cnpj|cnpj.*request', line, re.IGNORECASE):
            return 'STRING', None
        
        # Padrões para interfaces/types TypeScript
        elif re.search(r'interface.*\{|type.*=|:\s*\{', line, re.IGNORECASE):
            return 'STRING', None
        
        # Padrões para métodos/funções
        elif re.search(r'function.*cnpj|cnpj.*function|method.*cnpj|cnpj.*method', line, re.IGNORECASE):
            return 'STRING', None
        
        # Padrões para comentários (ignorar)
        elif re.search(r'//.*cnpj|/\*.*cnpj|<!--.*cnpj', line, re.IGNORECASE):
            return 'COMMENT', None
        
        # Padrões para strings literais
        elif re.search(r'[\'"][^\'"]*cnpj[^\'"]*[\'"]', line, re.IGNORECASE):
            return 'STRING_LITERAL', None
        
        # Padrões para imports
        elif re.search(r'import.*cnpj|from.*cnpj', line, re.IGNORECASE):
            return 'IMPORT', None
        
        # Padrões para exports
        elif re.search(r'export.*cnpj', line, re.IGNORECASE):
            return 'EXPORT', None
        
        # Padrões para CSS/estilos (ignorar)
        elif re.search(r'\.cnpj|#cnpj|cnpj\s*\{', line, re.IGNORECASE):
            return 'CSS', None
        
        # Padrões para template HTML
        elif re.search(r'<[^>]*cnpj[^>]*>', line, re.IGNORECASE):
            return 'TEMPLATE', None
        
        # Padrões para atributos HTML
        elif re.search(r'[a-z-]+=.*cnpj', line, re.IGNORECASE):
            return 'ATTRIBUTE', None
        
        # Se não conseguir identificar, mas tem cnpj na linha, provavelmente é string
        else:
            return 'STRING', None

    def _assess_ui_impact(self, field_type: str, field_size: Optional[int]) -> tuple:
        """Avalia o impacto da mudança do CNPJ alfanumérico para campos UI"""
        if field_type in ['COMMENT', 'CSS', 'IMPORT', 'EXPORT', 'TEMPLATE', 'ATTRIBUTE']:
            return ImpactLevel.LOW, Status.COMPATIBLE, "Campo não requer alteração"
        
        elif field_type == 'NUMBER':
            return ImpactLevel.HIGH, Status.INCOMPATIBLE, "Campo numérico precisa ser alterado para string"
        
        elif field_type == 'BOOLEAN':
            return ImpactLevel.MEDIUM, Status.NEEDS_ANALYSIS, "Verificar se campo boolean é apropriado para CNPJ"
        
        elif field_type == 'VALIDATION_FUNCTION':
            return ImpactLevel.HIGH, Status.NEEDS_ANALYSIS, "Função de validação precisa ser atualizada para CNPJ alfanumérico"
        
        elif field_type in ['STRING', 'STRING_LITERAL']:
            return ImpactLevel.LOW, Status.COMPATIBLE, "Campo string é compatível com CNPJ alfanumérico"
        
        else:
            return ImpactLevel.MEDIUM, Status.NEEDS_ANALYSIS, "Análise manual necessária"

    def analyze_project(self, project_path: Path, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analisa um projeto de UI e retorna os resultados"""
        project_name = project_path.name if hasattr(project_path, 'name') else str(project_path).split('/')[-1]
        self.console.print(f"[blue]Analisando projeto UI ({self.framework}): {project_name}[/blue]")
        
        # Escanear arquivos
        files = self.scan_files(project_path, filters)
        
        # Escanear package.json
        package_info = self.scan_package_json(project_path)
        
        # Encontrar campos CNPJ
        cnpj_fields = self.find_cnpj_fields(files)
        
        # Encontrar validações
        validations = self.find_validations(files)
        
        # Encontrar máscaras
        masks = self.find_frontend_masks(files)
        
        # Encontrar máscaras de input específicas
        input_masks = self.find_input_masks(files)
        
        # Encontrar validações de formulário
        form_validations = self.find_form_validations(files)
        
        # Encontrar padrões específicos do framework
        framework_specific = {}
        if self.framework == 'react':
            framework_specific = self.find_react_specific(files)
        elif self.framework == 'vue':
            framework_specific = self.find_vue_specific(files)
        elif self.framework == 'angular':
            framework_specific = self.find_angular_specific(files)
        
        # Encontrar padrões UI específicos
        ui_patterns = self.find_ui_specific_patterns(files)
        
        # Combinar todos os campos encontrados
        all_fields = cnpj_fields + validations + masks + input_masks + form_validations
        

        
        # Determinar impacto geral
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
            'project_type': f"ui_{self.framework}",
            'cnpj_fields_found': all_fields,
            'validations_found': validations,
            'frontend_masks': masks,
            'overall_impact': overall_impact.value if overall_impact else 'baixo',
            'files_scanned': len(files),
            'framework_detected': self.framework,
            'package_info': package_info,
            'input_masks': input_masks,
            'form_validations': form_validations,
            'framework_specific': framework_specific,
            'ui_patterns': ui_patterns
        }
