"""
Dead Code Detector - Find unreachable code, unused imports, variables, and functions.
"""

import ast
from typing import Dict, List, Set, Tuple, Optional


class UnusedImportDetector:
    """Detect unused imports in Python code."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find unused import statements."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        unused_imports = []
        
        # Collect all imports
        imports = self._collect_imports(tree)
        
        # Collect all names used in the code
        used_names = self._collect_used_names(tree)
        
        # Find imports that are never used
        for import_info in imports:
            if import_info['alias'] not in used_names:
                unused_imports.append({
                    "type": "unused_import",
                    "severity": "low",
                    "location": f"line {import_info['line']}",
                    "file": file_path,
                    "import_statement": import_info['statement'],
                    "module": import_info['module'],
                    "name": import_info['alias'],
                    "description": f"Unused import: {import_info['statement']}",
                    "recommendation": "Remove this unused import to reduce clutter"
                })
        
        return unused_imports
    
    def _collect_imports(self, tree: ast.AST) -> List[Dict]:
        """Collect all import statements with their aliases."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append({
                        'module': alias.name,
                        'alias': name,
                        'statement': f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""),
                        'line': node.lineno
                    })
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    if alias.name == '*':
                        # Star imports are handled separately
                        continue
                    name = alias.asname if alias.asname else alias.name
                    imports.append({
                        'module': f"{module}.{alias.name}" if module else alias.name,
                        'alias': name,
                        'statement': f"from {module} import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""),
                        'line': node.lineno
                    })
        
        return imports
    
    def _collect_used_names(self, tree: ast.AST) -> Set[str]:
        """Collect all names that are actually used (loaded) in the code."""
        used_names = set()
        
        for node in ast.walk(tree):
            # Names used in expressions
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            
            # Attributes (e.g., module.function)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
            
            # Don't count imports themselves
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
        
        return used_names


class UnusedVariableDetector:
    """Detect variables that are assigned but never used."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find unused variables."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        unused_vars = []
        
        # Analyze each function/method separately
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                unused_in_func = self._find_unused_in_function(node)
                for var_info in unused_in_func:
                    unused_vars.append({
                        "type": "unused_variable",
                        "severity": "low",
                        "location": f"line {var_info['line']}",
                        "file": file_path,
                        "function": node.name,
                        "variable": var_info['name'],
                        "description": f"Variable '{var_info['name']}' is assigned but never used",
                        "recommendation": "Remove unused variable or prefix with '_' if intentionally unused"
                    })
        
        return unused_vars
    
    def _find_unused_in_function(self, func_node: ast.FunctionDef) -> List[Dict]:
        """Find unused variables within a function."""
        assigned = {}  # var_name -> line_number
        used = set()
        
        # Collect assignments
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    names = self._extract_names(target)
                    for name in names:
                        if not name.startswith('_'):  # Ignore vars starting with _
                            assigned[name] = node.lineno
            
            elif isinstance(node, ast.AugAssign):
                names = self._extract_names(node.target)
                for name in names:
                    used.add(name)  # AugAssign reads and writes
            
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                names = self._extract_names(node.target)
                for name in names:
                    assigned[name] = node.lineno
        
        # Collect usages (reads)
        for node in ast.walk(func_node):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
        
        # Find variables that are assigned but never used
        unused = []
        for var_name, line in assigned.items():
            if var_name not in used and var_name not in ['self', 'cls']:
                unused.append({'name': var_name, 'line': line})
        
        return unused
    
    def _extract_names(self, node: ast.AST) -> Set[str]:
        """Extract variable names from an assignment target."""
        names = set()
        
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                names.update(self._extract_names(elt))
        elif isinstance(node, ast.Starred):
            names.update(self._extract_names(node.value))
        
        return names


class UnreachableCodeDetector:
    """Detect unreachable code (code after return, break, continue, raise)."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find unreachable code blocks."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        unreachable_blocks = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                unreachable = self._find_unreachable_in_function(node)
                for block_info in unreachable:
                    unreachable_blocks.append({
                        "type": "unreachable_code",
                        "severity": "medium",
                        "location": f"line {block_info['line']}",
                        "file": file_path,
                        "function": node.name,
                        "after_statement": block_info['after'],
                        "description": f"Code after {block_info['after']} is unreachable",
                        "recommendation": "Remove unreachable code or restructure control flow"
                    })
        
        return unreachable_blocks
    
    def _find_unreachable_in_function(self, func_node: ast.FunctionDef) -> List[Dict]:
        """Find unreachable code in a function."""
        unreachable = []
        
        # Check each block of statements
        for i, stmt in enumerate(func_node.body):
            # If this statement is a terminator, check if there's code after it
            if self._is_terminator(stmt):
                # Check if there are more statements after this
                if i + 1 < len(func_node.body):
                    next_stmt = func_node.body[i + 1]
                    unreachable.append({
                        'line': next_stmt.lineno,
                        'after': self._get_terminator_type(stmt)
                    })
        
        # Recursively check nested blocks
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                unreachable.extend(self._check_block(node.body))
                if hasattr(node, 'orelse'):
                    unreachable.extend(self._check_block(node.orelse))
        
        return unreachable
    
    def _check_block(self, statements: List[ast.stmt]) -> List[Dict]:
        """Check a block of statements for unreachable code."""
        unreachable = []
        
        for i, stmt in enumerate(statements):
            if self._is_terminator(stmt):
                if i + 1 < len(statements):
                    next_stmt = statements[i + 1]
                    unreachable.append({
                        'line': next_stmt.lineno,
                        'after': self._get_terminator_type(stmt)
                    })
                    break  # Everything after is unreachable
        
        return unreachable
    
    def _is_terminator(self, stmt: ast.stmt) -> bool:
        """Check if a statement terminates execution flow."""
        return isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue))
    
    def _get_terminator_type(self, stmt: ast.stmt) -> str:
        """Get the type of terminator statement."""
        if isinstance(stmt, ast.Return):
            return "return"
        elif isinstance(stmt, ast.Raise):
            return "raise"
        elif isinstance(stmt, ast.Break):
            return "break"
        elif isinstance(stmt, ast.Continue):
            return "continue"
        return "unknown"


class UnusedFunctionDetector:
    """Detect functions that are defined but never called."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find unused functions."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        # Collect all function definitions
        defined_functions = self._collect_function_definitions(tree)
        
        # Collect all function calls
        called_functions = self._collect_function_calls(tree)
        
        # Find functions that are never called
        unused_functions = []
        for func_name, func_info in defined_functions.items():
            # Skip special methods, private methods, and common entry points
            if self._should_skip(func_name):
                continue
            
            if func_name not in called_functions:
                unused_functions.append({
                    "type": "unused_function",
                    "severity": "medium",
                    "location": f"line {func_info['line']}",
                    "file": file_path,
                    "function": func_name,
                    "description": f"Function '{func_name}' is defined but never called",
                    "recommendation": (
                        "Remove unused function or verify it's not called dynamically/externally. "
                        "Prefix with '_' if it's intentionally private/unused."
                    )
                })
        
        return unused_functions
    
    def _collect_function_definitions(self, tree: ast.AST) -> Dict[str, Dict]:
        """Collect all function definitions."""
        functions = {}
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name] = {
                    'line': node.lineno,
                    'is_method': self._is_method(node)
                }
        
        return functions
    
    def _collect_function_calls(self, tree: ast.AST) -> Set[str]:
        """Collect all function/method calls."""
        calls = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Direct function call
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                # Method call
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        
        return calls
    
    def _is_method(self, func_node: ast.FunctionDef) -> bool:
        """Check if function is a method (has 'self' or 'cls' as first param)."""
        if func_node.args.args:
            first_arg = func_node.args.args[0].arg
            return first_arg in ['self', 'cls']
        return False
    
    def _should_skip(self, func_name: str) -> bool:
        """Check if function should be skipped (special methods, entry points, etc.)."""
        # Skip dunder methods
        if func_name.startswith('__') and func_name.endswith('__'):
            return True
        
        # Skip private methods (single underscore)
        if func_name.startswith('_'):
            return True
        
        # Skip common entry points
        if func_name in ['main', 'run', 'setup', 'teardown', 'setUp', 'tearDown']:
            return True
        
        # Skip test methods
        if func_name.startswith('test_'):
            return True
        
        return False


class ShadowedVariableDetector:
    """Detect variables that shadow outer scope variables."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find shadowed variables."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        shadowed_vars = []
        
        # Build scope hierarchy
        scopes = self._build_scope_hierarchy(tree)
        
        # Check for shadowing
        for scope_info in scopes:
            for var_name, var_line in scope_info['defined'].items():
                # Check parent scopes
                parent = scope_info['parent']
                while parent:
                    if var_name in parent['defined']:
                        shadowed_vars.append({
                            "type": "shadowed_variable",
                            "severity": "low",
                            "location": f"line {var_line}",
                            "file": file_path,
                            "variable": var_name,
                            "inner_scope": scope_info['name'],
                            "outer_scope": parent['name'],
                            "outer_definition": f"line {parent['defined'][var_name]}",
                            "description": f"Variable '{var_name}' shadows outer scope variable",
                            "recommendation": "Rename variable to avoid shadowing or use different name"
                        })
                        break
                    parent = parent.get('parent')
        
        return shadowed_vars
    
    def _build_scope_hierarchy(self, tree: ast.AST) -> List[Dict]:
        """Build a hierarchy of scopes with their variables."""
        scopes = []
        
        # Module-level scope
        module_scope = {
            'name': '<module>',
            'defined': self._get_module_level_vars(tree),
            'parent': None
        }
        scopes.append(module_scope)
        
        # Function/class scopes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_scope = {
                    'name': f"function '{node.name}'",
                    'defined': self._get_function_vars(node),
                    'parent': module_scope  # Simplified; could build full nesting
                }
                scopes.append(func_scope)
        
        return scopes
    
    def _get_module_level_vars(self, tree: ast.AST) -> Dict[str, int]:
        """Get variables defined at module level."""
        vars_defined = {}
        
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    for name in self._extract_names(target):
                        vars_defined[name] = node.lineno
        
        return vars_defined
    
    def _get_function_vars(self, func_node: ast.FunctionDef) -> Dict[str, int]:
        """Get variables defined in a function."""
        vars_defined = {}
        
        # Parameters
        for arg in func_node.args.args:
            vars_defined[arg.arg] = func_node.lineno
        
        # Assignments in function body
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    for name in self._extract_names(target):
                        vars_defined[name] = node.lineno
        
        return vars_defined
    
    def _extract_names(self, node: ast.AST) -> Set[str]:
        """Extract variable names from assignment target."""
        names = set()
        
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                names.update(self._extract_names(elt))
        
        return names


class DeadCodeDetector:
    """Unified dead code detection orchestrator."""
    
    def __init__(self):
        self.unused_import_detector = UnusedImportDetector()
        self.unused_variable_detector = UnusedVariableDetector()
        self.unreachable_code_detector = UnreachableCodeDetector()
        self.unused_function_detector = UnusedFunctionDetector()
        self.shadowed_variable_detector = ShadowedVariableDetector()
    
    def detect_all(self, code: str, file_path: str = "unknown.py") -> Dict:
        """Run all dead code detectors."""
        issues = []
        
        # Detect unused imports
        issues.extend(self.unused_import_detector.detect(code, file_path))
        
        # Detect unused variables
        issues.extend(self.unused_variable_detector.detect(code, file_path))
        
        # Detect unreachable code
        issues.extend(self.unreachable_code_detector.detect(code, file_path))
        
        # Detect unused functions
        issues.extend(self.unused_function_detector.detect(code, file_path))
        
        # Detect shadowed variables
        issues.extend(self.shadowed_variable_detector.detect(code, file_path))
        
        return {
            "file": file_path,
            "total_issues": len(issues),
            "issues_by_type": self._categorize_by_type(issues),
            "issues_by_severity": self._categorize_by_severity(issues),
            "detailed_issues": issues,
            "summary": {
                "unused_imports": len([i for i in issues if i['type'] == 'unused_import']),
                "unused_variables": len([i for i in issues if i['type'] == 'unused_variable']),
                "unreachable_code": len([i for i in issues if i['type'] == 'unreachable_code']),
                "unused_functions": len([i for i in issues if i['type'] == 'unused_function']),
                "shadowed_variables": len([i for i in issues if i['type'] == 'shadowed_variable'])
            }
        }
    
    def _categorize_by_type(self, issues: List[Dict]) -> Dict:
        """Group issues by type."""
        categorized = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            if issue_type not in categorized:
                categorized[issue_type] = []
            categorized[issue_type].append(issue)
        return categorized
    
    def _categorize_by_severity(self, issues: List[Dict]) -> Dict:
        """Group issues by severity."""
        categorized = {"high": [], "medium": [], "low": []}
        for issue in issues:
            severity = issue.get("severity", "low")
            categorized[severity].append(issue)
        return categorized
