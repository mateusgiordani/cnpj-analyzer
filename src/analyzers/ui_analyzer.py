"""
Analisador UI - React, Vue, Angular
Versão: 1.0
Data: 2025-01-27
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from analyzers.base_analyzer import BaseAnalyzer, CNPJField, ImpactLevel, Status

class UIAnalyzer(BaseAnalyzer):
    """Analisador específico para projetos de UI"""
    
    def __init__(self, framework: str = "ui"):
        super().__init__(f"ui_{framework}")
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

    def find_input_masks(self, files: List[Dict]) -> List[Dict]:
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
                        masks.append({
                            'file_path': file_path,
                            'line_number': line_num,
                            'line': line.strip(),
                            'mask_type': 'input_mask'
                        })
        
        return masks

    def find_form_validations(self, files: List[Dict]) -> List[Dict]:
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
                        validations.append({
                            'file_path': file_path,
                            'line_number': line_num,
                            'line': line.strip(),
                            'validation_type': 'form_validation'
                        })
        
        return validations

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
