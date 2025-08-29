"""
Analisador ETL - Pentaho Spoon, Data Transformation, Python ETL
Versão: 2.0
Data: 2025-08-28
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

from analyzers.base_analyzer import BaseAnalyzer, CNPJField, ImpactLevel, Status

class ETLAnalyzer(BaseAnalyzer):
    """Analisador específico para projetos ETL"""
    
    def __init__(self):
        super().__init__("etl_transformation")
        
        # Padrões específicos para ETL
        self.etl_patterns = {
            'pentaho': {
                'transformation_patterns': [
                    r'<transformation>',
                    r'<notepad>',
                    r'<step>',
                    r'<name>([^<]+)</name>',
                    r'<type>([^<]+)</type>',
                    r'<filename>([^<]+)</filename>',
                    r'<directory>([^<]+)</directory>'
                ],
                'field_patterns': [
                    r'<field>',
                    r'<name>([^<]+)</name>',
                    r'<type>([^<]+)</type>',
                    r'<length>(\d+)</length>',
                    r'<precision>(\d+)</precision>',
                    r'<format>([^<]+)</format>'
                ],
                'validation_patterns': [
                    r'<validator>',
                    r'<validation_type>([^<]+)</validation_type>',
                    r'<regex>([^<]+)</regex>',
                    r'<min_length>(\d+)</min_length>',
                    r'<max_length>(\d+)</max_length>',
                    r'<field_name>([^<]+)</field_name>'
                ],
                'job_patterns': [
                    r'<job>',
                    r'<jobentry>',
                    r'<name>([^<]+)</name>',
                    r'<type>([^<]+)</type>',
                    r'<filename>([^<]+)</filename>'
                ]
            },
            'sql': {
                'select_patterns': [
                    r'SELECT\s+([^FROM]+)\s+FROM',
                    r'SELECT\s+DISTINCT\s+([^FROM]+)\s+FROM',
                    r'SELECT\s+TOP\s+\d+\s+([^FROM]+)\s+FROM',
                    r'SELECT\s+([^FROM]+)\s+FROM\s+([^\s;]+)',
                    r'SELECT\s+([^FROM]+)\s+FROM\s+([^\s;]+)\s+WHERE'
                ],
                'insert_patterns': [
                    r'INSERT\s+INTO\s+([^\s(]+)',
                    r'INSERT\s+INTO\s+([^\s(]+)\s*\([^)]+\)',
                    r'VALUES\s*\([^)]+\)',
                    r'INSERT\s+INTO\s+([^\s(]+)\s+SELECT'
                ],
                'update_patterns': [
                    r'UPDATE\s+([^\s]+)\s+SET',
                    r'SET\s+([^WHERE]+)\s+WHERE',
                    r'UPDATE\s+([^\s]+)\s+SET\s+([^WHERE]+)\s+WHERE'
                ],
                'where_patterns': [
                    r'WHERE\s+([^;]+)',
                    r'AND\s+([^;]+)',
                    r'OR\s+([^;]+)',
                    r'WHERE\s+([^;]+)\s+AND\s+([^;]+)'
                ],
                'table_patterns': [
                    r'CREATE\s+TABLE\s+([^\s(]+)',
                    r'ALTER\s+TABLE\s+([^\s]+)',
                    r'DROP\s+TABLE\s+([^\s;]+)',
                    r'TRUNCATE\s+TABLE\s+([^\s;]+)'
                ]
            },
            'python': {
                'pandas_patterns': [
                    r'import\s+pandas',
                    r'pd\.read_',
                    r'df\[[\'"]([^\'"]+)[\'"]\]',
                    r'df\.loc\[',
                    r'df\.iloc\[',
                    r'df\.query\(',
                    r'df\.filter\('
                ],
                'transformation_patterns': [
                    r'df\[[\'"]([^\'"]+)[\'"]\]\s*=\s*df\[[\'"]([^\'"]+)[\'"]\]',
                    r'df\.rename\s*\(\s*columns\s*=\s*{',
                    r'df\.drop\s*\(\s*columns\s*=\s*\[',
                    r'df\.fillna\s*\(',
                    r'df\.replace\(',
                    r'df\.astype\(',
                    r'df\.apply\('
                ],
                'etl_patterns': [
                    r'extract.*cnpj',
                    r'cnpj.*extract',
                    r'transform.*cnpj',
                    r'cnpj.*transform',
                    r'load.*cnpj',
                    r'cnpj.*load',
                    r'ETL.*cnpj',
                    r'cnpj.*ETL'
                ]
            },
            'spark': {
                'spark_patterns': [
                    r'from\s+pyspark',
                    r'SparkSession',
                    r'spark\.read',
                    r'df\.select\(',
                    r'df\.filter\(',
                    r'df\.withColumn\(',
                    r'df\.write'
                ]
            },
            'airflow': {
                'airflow_patterns': [
                    r'from\s+airflow',
                    r'DAG\s*\(\s*',
                    r'@task',
                    r'@dag',
                    r'PythonOperator',
                    r'BashOperator',
                    r'SqlOperator'
                ]
            }
        }

    def get_file_extensions(self) -> List[str]:
        """Retorna as extensões de arquivo suportadas"""
        return ['.ktr', '.kjb', '.xml', '.sql', '.py', '.r', '.scala', '.java', '.sh', '.bash', '.yaml', '.yml', '.json']

    def get_skip_patterns(self) -> List[str]:
        """Retorna padrões de arquivos para pular"""
        return [
            r'node_modules/',
            r'\.git/',
            r'__pycache__/',
            r'\.venv/',
            r'venv/',
            r'dist/',
            r'build/',
            r'target/',
            r'bin/',
            r'obj/',
            r'\.idea/',
            r'\.vscode/',
            r'*.pyc',
            r'*.pyo',
            r'*.pyd',
            r'*.so',
            r'*.dll',
            r'*.exe'
        ]

    def _detect_etl_type(self, project_path: Path) -> str:
        """Detecta o tipo específico do projeto ETL"""
        # Verificar arquivos Pentaho
        if any(project_path.rglob('*.ktr')) or any(project_path.rglob('*.kjb')):
            return 'pentaho'
        
        # Verificar arquivos SQL
        if any(project_path.rglob('*.sql')):
            return 'sql'
        
        # Verificar arquivos Python ETL
        python_files = list(project_path.rglob('*.py'))
        if python_files:
            for py_file in python_files[:5]:  # Verificar apenas os primeiros 5 arquivos
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if any(pattern in content for pattern in ['pandas', 'pd.', 'df.']):
                            return 'python_pandas'
                        if any(pattern in content for pattern in ['pyspark', 'SparkSession']):
                            return 'python_spark'
                        if any(pattern in content for pattern in ['airflow', 'DAG']):
                            return 'python_airflow'
                except Exception:
                    continue
        
        # Verificar arquivos R
        if any(project_path.rglob('*.r')) or any(project_path.rglob('*.R')):
            return 'r'
        
        # Verificar arquivos Scala/Java
        if any(project_path.rglob('*.scala')) or any(project_path.rglob('*.java')):
            return 'scala_java'
        
        return 'etl_generic'

    def scan_pentaho_files(self, project_path: Path) -> List[Dict[str, Any]]:
        """Escaneia arquivos específicos do Pentaho"""
        pentaho_files = []
        
        # Buscar arquivos .ktr (transformations)
        for file_path in project_path.rglob('*.ktr'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    pentaho_files.append({
                        'file_path': str(file_path),
                        'file_type': 'transformation',
                        'content': content
                    })
            except Exception as e:
                self.logger.error(f"Erro ao ler arquivo Pentaho {file_path}: {e}")
        
        # Buscar arquivos .kjb (jobs)
        for file_path in project_path.rglob('*.kjb'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    pentaho_files.append({
                        'file_path': str(file_path),
                        'file_type': 'job',
                        'content': content
                    })
            except Exception as e:
                self.logger.error(f"Erro ao ler arquivo Pentaho {file_path}: {e}")
        
        return pentaho_files

    def scan_sql_files(self, project_path: Path) -> List[Dict[str, Any]]:
        """Escaneia arquivos SQL"""
        sql_files = []
        
        for file_path in project_path.rglob('*.sql'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    sql_files.append({
                        'file_path': str(file_path),
                        'file_type': 'sql',
                        'content': content
                    })
            except Exception as e:
                self.logger.error(f"Erro ao ler arquivo SQL {file_path}: {e}")
        
        return sql_files

    def scan_python_etl_files(self, project_path: Path) -> List[Dict[str, Any]]:
        """Escaneia arquivos Python ETL"""
        python_files = []
        
        for file_path in project_path.rglob('*.py'):
            if self._is_etl_python_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        python_files.append({
                            'file_path': str(file_path),
                            'file_type': 'python_etl',
                            'content': content
                        })
                except Exception as e:
                    self.logger.error(f"Erro ao ler arquivo Python {file_path}: {e}")
        
        return python_files

    def _is_etl_python_file(self, file_path: Path) -> bool:
        """Verifica se um arquivo Python é um arquivo ETL"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Verificar se contém padrões ETL
                etl_patterns = [
                    'pandas', 'pd.', 'df.',
                    'pyspark', 'SparkSession',
                    'airflow', 'DAG',
                    'extract', 'transform', 'load',
                    'ETL', 'etl'
                ]
                
                return any(pattern in content for pattern in etl_patterns)
        except Exception:
            return False

    def find_pentaho_specific_patterns(self, content: str, file_path: str) -> List[CNPJField]:
        """Encontra padrões específicos do Pentaho"""
        fields = []
        
        # Buscar campos com CNPJ em transformations
        field_patterns = [
            r'<name>([^<]*cnpj[^<]*)</name>',
            r'<field_name>([^<]*cnpj[^<]*)</field_name>',
            r'<column_name>([^<]*cnpj[^<]*)</column_name>'
        ]
        
        for pattern in field_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                field_name = match.group(1)
                fields.append(CNPJField(
                    file_path=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    field_name=field_name,
                    field_type='PENTAHO_FIELD',
                    field_size=None,
                    context=f"Campo Pentaho: {field_name}",
                    project_type='etl_pentaho',
                    impact_level=ImpactLevel.MEDIUM,
                    status=Status.NEEDS_ANALYSIS,
                    action_needed='Revisar validação de CNPJ',
                    estimated_effort='2-4 horas'
                ))
        
        return fields

    def find_sql_specific_patterns(self, content: str, file_path: str) -> List[CNPJField]:
        """Encontra padrões específicos do SQL"""
        fields = []
        
        # Buscar colunas com CNPJ em SELECT
        select_patterns = [
            r'SELECT\s+([^FROM]+)\s+FROM',
            r'SELECT\s+DISTINCT\s+([^FROM]+)\s+FROM'
        ]
        
        for pattern in select_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                select_clause = match.group(1)
                # Buscar colunas com CNPJ
                column_matches = re.finditer(r'(\w+)\s*as\s*(\w+)|(\w+)', select_clause, re.IGNORECASE)
                for col_match in column_matches:
                    column_name = col_match.group(2) or col_match.group(3) or col_match.group(1)
                    if 'cnpj' in column_name.lower():
                        fields.append(CNPJField(
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            field_name=column_name,
                            field_type='SQL_COLUMN',
                            field_size=None,
                            context=f"Coluna SQL: {column_name}",
                            project_type='etl_sql',
                            impact_level=ImpactLevel.MEDIUM,
                            status=Status.NEEDS_ANALYSIS,
                            action_needed='Revisar validação de CNPJ',
                            estimated_effort='2-4 horas'
                        ))
        
        # Buscar tabelas com CNPJ
        table_patterns = [
            r'FROM\s+([^\s;]+)',
            r'JOIN\s+([^\s;]+)',
            r'UPDATE\s+([^\s;]+)',
            r'INSERT\s+INTO\s+([^\s(]+)'
        ]
        
        for pattern in table_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                table_name = match.group(1)
                if 'cnpj' in table_name.lower():
                    fields.append(CNPJField(
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        field_name=table_name,
                        field_type='SQL_TABLE',
                        field_size=None,
                        context=f"Tabela SQL: {table_name}",
                        project_type='etl_sql',
                        impact_level=ImpactLevel.MEDIUM,
                        status=Status.NEEDS_ANALYSIS,
                        action_needed='Revisar validação de CNPJ',
                        estimated_effort='2-4 horas'
                    ))
        
        return fields

    def find_python_etl_patterns(self, content: str, file_path: str) -> List[CNPJField]:
        """Encontra padrões específicos do Python ETL"""
        fields = []
        
        # Buscar colunas do pandas com CNPJ
        pandas_patterns = [
            r'df\[[\'"]([^\'"]*cnpj[^\'"]*)[\'"]\]',
            r'df\.loc\[.*[\'"]([^\'"]*cnpj[^\'"]*)[\'"]\]',
            r'df\.filter\(.*[\'"]([^\'"]*cnpj[^\'"]*)[\'"]\)'
        ]
        
        for pattern in pandas_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                column_name = match.group(1)
                fields.append(CNPJField(
                    file_path=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    field_name=column_name,
                    field_type='PYTHON_PANDAS_COLUMN',
                    field_size=None,
                    context=f"Coluna Pandas: {column_name}",
                    project_type='etl_python_pandas',
                    impact_level=ImpactLevel.MEDIUM,
                    status=Status.NEEDS_ANALYSIS,
                    action_needed='Revisar validação de CNPJ',
                    estimated_effort='2-4 horas'
                ))
        
        # Buscar variáveis com CNPJ
        variable_patterns = [
            r'(\w+)\s*=\s*.*cnpj',
            r'def\s+(\w+).*cnpj',
            r'class\s+(\w+).*cnpj'
        ]
        
        for pattern in variable_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                variable_name = match.group(1)
                if 'cnpj' in variable_name.lower():
                    fields.append(CNPJField(
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        field_name=variable_name,
                        field_type='PYTHON_VARIABLE',
                        field_size=None,
                        context=f"Variável Python: {variable_name}",
                        project_type='etl_python_pandas',
                        impact_level=ImpactLevel.MEDIUM,
                        status=Status.NEEDS_ANALYSIS,
                        action_needed='Revisar validação de CNPJ',
                        estimated_effort='2-4 horas'
                    ))
        
        return fields

    def find_pentaho_transformations(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra transformations do Pentaho"""
        transformations = []
        
        # Buscar transformations
        transformation_patterns = [
            r'<name>([^<]+)</name>',
            r'<type>([^<]+)</type>'
        ]
        
        for pattern in transformation_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                value = match.group(1)
                if 'cnpj' in value.lower():
                    transformations.append({
                        'file_path': file_path,
                        'line_number': content[:match.start()].count('\n') + 1,
                        'value': value,
                        'type': 'PENTAHO_TRANSFORMATION'
                    })
        
        return transformations

    def find_pentaho_jobs(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra jobs do Pentaho"""
        jobs = []
        
        # Buscar jobs
        job_patterns = [
            r'<name>([^<]+)</name>',
            r'<type>([^<]+)</type>'
        ]
        
        for pattern in job_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                value = match.group(1)
                if 'cnpj' in value.lower():
                    jobs.append({
                        'file_path': file_path,
                        'line_number': content[:match.start()].count('\n') + 1,
                        'value': value,
                        'type': 'PENTAHO_JOB'
                    })
        
        return jobs

    def find_sql_queries(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra queries SQL"""
        queries = []
        
        # Buscar queries com CNPJ
        query_patterns = [
            r'SELECT.*cnpj.*FROM',
            r'INSERT.*cnpj.*INTO',
            r'UPDATE.*cnpj.*SET',
            r'WHERE.*cnpj',
            r'AND.*cnpj',
            r'OR.*cnpj'
        ]
        
        for pattern in query_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                query_text = match.group(0)
                queries.append({
                    'file_path': file_path,
                    'line_number': content[:match.start()].count('\n') + 1,
                    'query_text': query_text,
                    'type': 'SQL_QUERY'
                })
        
        return queries

    def find_python_transformations(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra transformations Python"""
        transformations = []
        
        # Buscar transformations com CNPJ
        transformation_patterns = [
            r'df.*cnpj.*=',
            r'df.*=.*cnpj',
            r'df\.rename.*cnpj',
            r'df\.drop.*cnpj',
            r'df\.fillna.*cnpj',
            r'df\.replace.*cnpj'
        ]
        
        for pattern in transformation_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                transformation_text = match.group(0)
                transformations.append({
                    'file_path': file_path,
                    'line_number': content[:match.start()].count('\n') + 1,
                    'transformation_text': transformation_text,
                    'type': 'PYTHON_TRANSFORMATION'
                })
        
        return transformations

    def find_cnpj_in_etl(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Encontra referências específicas a CNPJ em ETL"""
        cnpj_references = []
        
        # Padrões específicos de CNPJ em ETL
        cnpj_patterns = [
            r'cnpj.*extract',
            r'extract.*cnpj',
            r'cnpj.*transform',
            r'transform.*cnpj',
            r'cnpj.*load',
            r'load.*cnpj',
            r'ETL.*cnpj',
            r'cnpj.*ETL',
            r'data.*cnpj',
            r'cnpj.*data',
            r'process.*cnpj',
            r'cnpj.*process'
        ]
        
        for pattern in cnpj_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                reference_text = match.group(0)
                cnpj_references.append({
                    'file_path': file_path,
                    'line_number': content[:match.start()].count('\n') + 1,
                    'reference_text': reference_text,
                    'type': 'ETL_CNPJ_REFERENCE'
                })
        
        return cnpj_references

    def analyze_project(self, project_path: Path, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analisa um projeto ETL"""
        self.logger.info(f"Analisando projeto ETL: {project_path}")
        
        # Detectar tipo específico do projeto ETL
        etl_type = self._detect_etl_type(project_path)
        
        # Escanear arquivos
        scanned_files = self.scan_files(project_path, filters)
        
        # Encontrar campos CNPJ
        cnpj_fields = self.find_cnpj_fields(scanned_files)
        
        # Buscar padrões específicos do ETL
        etl_specific_fields = []
        transformations = []
        jobs = []
        queries = []
        python_transformations = []
        cnpj_references = []
        
        for file_info in scanned_files:
            file_path = file_info['file_path']
            content = file_info['content']
            if content:
                if etl_type == 'pentaho':
                    etl_specific_fields.extend(self.find_pentaho_specific_patterns(content, file_path))
                    transformations.extend(self.find_pentaho_transformations(content, file_path))
                    jobs.extend(self.find_pentaho_jobs(content, file_path))
                elif etl_type == 'sql':
                    etl_specific_fields.extend(self.find_sql_specific_patterns(content, file_path))
                    queries.extend(self.find_sql_queries(content, file_path))
                elif etl_type.startswith('python'):
                    etl_specific_fields.extend(self.find_python_etl_patterns(content, file_path))
                    python_transformations.extend(self.find_python_transformations(content, file_path))
                
                cnpj_references.extend(self.find_cnpj_in_etl(content, file_path))
        
        # Combinar campos
        all_fields = cnpj_fields + etl_specific_fields
        
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
            'project_type': f"etl_{etl_type}",
            'cnpj_fields_found': all_fields,
            'validations_found': [],
            'frontend_masks': [],
            'overall_impact': overall_impact.value if overall_impact else 'baixo',
            'files_scanned': len(scanned_files),
            'framework_detected': 'etl',
            'etl_type': etl_type,
            'etl_components': {
                'transformations': transformations,
                'jobs': jobs,
                'queries': queries,
                'python_transformations': python_transformations,
                'cnpj_references': cnpj_references
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
