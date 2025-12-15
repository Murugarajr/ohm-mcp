"""
Type Hint Coverage & Migration Assistant - Analyze and improve type annotations.
"""

import ast
from typing import Dict, List, Set, Optional, Tuple, Any


class TypeHintCoverageAnalyzer:
    """Analyze type hint coverage in Python code."""
    
    def analyze(self, code: str, file_path: str = "unknown.py") -> Dict:
        """
        Analyze type hint coverage in the code.
        
        Returns:
            {
              "coverage_percent": float,
              "total_functions": int,
              "typed_functions": int,
              "missing_hints": list
            }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error": "Failed to parse code"}
        
        functions = self._collect_functions(tree)
        
        total_functions = len(functions)
        typed_functions = sum(1 for f in functions if f['is_fully_typed'])
        
        coverage = (typed_functions / total_functions * 100) if total_functions > 0 else 0
        
        missing_hints = [f for f in functions if not f['is_fully_typed']]
        
        return {
            "file": file_path,
            "coverage_percent": round(coverage, 2),
            "total_functions": total_functions,
            "typed_functions": typed_functions,
            "untyped_functions": total_functions - typed_functions,
            "missing_hints": missing_hints,
            "grade": self._get_coverage_grade(coverage)
        }
    
    def _collect_functions(self, tree: ast.AST) -> List[Dict]:
        """Collect all functions with their type annotation status."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip dunder methods
                if node.name.startswith('__') and node.name.endswith('__'):
                    continue
                
                func_info = self._analyze_function(node)
                functions.append(func_info)
        
        return functions
    
    def _analyze_function(self, func_node: ast.FunctionDef) -> Dict:
        """Analyze type annotations for a single function."""
        # Check return type
        has_return_type = func_node.returns is not None
        
        # Check parameter types
        params = []
        all_params_typed = True
        
        for arg in func_node.args.args:
            # Skip 'self' and 'cls'
            if arg.arg in ['self', 'cls']:
                continue
            
            has_annotation = arg.annotation is not None
            if not has_annotation:
                all_params_typed = False
            
            params.append({
                'name': arg.arg,
                'has_type': has_annotation,
                'type': ast.unparse(arg.annotation) if arg.annotation else None
            })
        
        # Check if function is a property/setter (special case)
        is_property = any(
            isinstance(d, ast.Name) and d.id in ['property', 'setter', 'getter', 'deleter']
            for d in func_node.decorator_list
        )
        
        is_fully_typed = has_return_type and all_params_typed and len(params) > 0
        
        # If function has no params and no explicit return, it might be considered typed
        if len(params) == 0 and func_node.name not in ['__init__']:
            is_fully_typed = has_return_type
        
        return {
            'name': func_node.name,
            'line': func_node.lineno,
            'is_async': isinstance(func_node, ast.AsyncFunctionDef),
            'is_property': is_property,
            'has_return_type': has_return_type,
            'return_type': ast.unparse(func_node.returns) if func_node.returns else None,
            'parameters': params,
            'all_params_typed': all_params_typed,
            'is_fully_typed': is_fully_typed
        }
    
    def _get_coverage_grade(self, coverage: float) -> str:
        """Get a letter grade for type hint coverage."""
        if coverage >= 90:
            return "A (Excellent)"
        elif coverage >= 75:
            return "B (Good)"
        elif coverage >= 50:
            return "C (Fair)"
        elif coverage >= 25:
            return "D (Poor)"
        else:
            return "F (Needs Improvement)"


class TypeHintSuggester:
    """Suggest type hints for untyped functions."""
    
    def suggest_hints(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Generate type hint suggestions for untyped functions."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip dunder methods
                if node.name.startswith('__') and node.name.endswith('__'):
                    continue
                
                suggestion = self._suggest_for_function(node, code)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_for_function(self, func_node: ast.FunctionDef, full_code: str) -> Optional[Dict]:
        """Suggest type hints for a single function."""
        missing_hints = []
        
        # Check return type
        if func_node.returns is None:
            inferred_return = self._infer_return_type(func_node)
            missing_hints.append({
                'kind': 'return',
                'suggested_type': inferred_return
            })
        
        # Check parameter types
        for arg in func_node.args.args:
            if arg.arg in ['self', 'cls']:
                continue
            
            if arg.annotation is None:
                inferred_param_type = self._infer_parameter_type(func_node, arg.arg)
                missing_hints.append({
                    'kind': 'parameter',
                    'name': arg.arg,
                    'suggested_type': inferred_param_type
                })
        
        if not missing_hints:
            return None
        
        # Generate annotated signature
        annotated_signature = self._generate_annotated_signature(func_node, missing_hints)
        
        return {
            "function": func_node.name,
            "line": func_node.lineno,
            "file": file_path,
            "missing_hints": missing_hints,
            "current_signature": self._get_current_signature(func_node),
            "suggested_signature": annotated_signature,
            "recommendation": f"Add type hints to improve code clarity and catch type errors early"
        }
    
    def _infer_return_type(self, func_node: ast.FunctionDef) -> str:
        """Infer return type from function body."""
        # Look for return statements
        return_types = set()
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                if node.value is None:
                    return_types.add('None')
                else:
                    inferred = self._infer_type_from_node(node.value)
                    return_types.add(inferred)
        
        # If no return statements found
        if not return_types:
            return 'None'
        
        # If multiple different types returned
        if len(return_types) > 1:
            return f"Union[{', '.join(sorted(return_types))}]"
        
        return return_types.pop()
    
    def _infer_parameter_type(self, func_node: ast.FunctionDef, param_name: str) -> str:
        """Infer parameter type from usage in function body."""
        # Look for operations on the parameter
        usages = []
        
        for node in ast.walk(func_node):
            # Check if parameter is used in binary operations
            if isinstance(node, ast.BinOp):
                if self._uses_name(node, param_name):
                    usages.append(self._infer_from_binop(node))
            
            # Check if parameter is compared
            elif isinstance(node, ast.Compare):
                if self._uses_name(node, param_name):
                    usages.append('Any')
            
            # Check if parameter is called (likely a function)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == param_name:
                    usages.append('Callable')
            
            # Check if parameter is subscripted (list/dict access)
            elif isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id == param_name:
                    if isinstance(node.slice, ast.Constant):
                        if isinstance(node.slice.value, int):
                            usages.append('List[Any]')
                        elif isinstance(node.slice.value, str):
                            usages.append('Dict[str, Any]')
            
            # Check if parameter is iterated
            elif isinstance(node, ast.For):
                if isinstance(node.iter, ast.Name) and node.iter.id == param_name:
                    usages.append('Iterable[Any]')
        
        if usages:
            # Return most specific type found
            return usages[0]
        
        return 'Any'
    
    def _infer_type_from_node(self, node: ast.AST) -> str:
        """Infer type from an AST node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return 'bool'
            elif isinstance(node.value, int):
                return 'int'
            elif isinstance(node.value, float):
                return 'float'
            elif isinstance(node.value, str):
                return 'str'
            elif node.value is None:
                return 'None'
        
        elif isinstance(node, ast.List):
            if node.elts:
                elem_types = {self._infer_type_from_node(e) for e in node.elts}
                if len(elem_types) == 1:
                    return f"List[{elem_types.pop()}]"
            return 'List[Any]'
        
        elif isinstance(node, ast.Dict):
            return 'Dict[str, Any]'
        
        elif isinstance(node, ast.Set):
            return 'Set[Any]'
        
        elif isinstance(node, ast.Tuple):
            if node.elts:
                types = [self._infer_type_from_node(e) for e in node.elts]
                return f"Tuple[{', '.join(types)}]"
            return 'Tuple[Any, ...]'
        
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # Common constructors
                if node.func.id in ['list', 'List']:
                    return 'List[Any]'
                elif node.func.id in ['dict', 'Dict']:
                    return 'Dict[str, Any]'
                elif node.func.id in ['set', 'Set']:
                    return 'Set[Any]'
                elif node.func.id in ['str']:
                    return 'str'
                elif node.func.id in ['int']:
                    return 'int'
                elif node.func.id in ['float']:
                    return 'float'
                elif node.func.id in ['bool']:
                    return 'bool'
        
        return 'Any'
    
    def _infer_from_binop(self, node: ast.BinOp) -> str:
        """Infer type from binary operation."""
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
            return 'Union[int, float]'
        elif isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor)):
            return 'int'
        return 'Any'
    
    def _uses_name(self, node: ast.AST, name: str) -> bool:
        """Check if a node uses a specific variable name."""
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id == name:
                return True
        return False
    
    def _get_current_signature(self, func_node: ast.FunctionDef) -> str:
        """Get current function signature as string."""
        args = []
        for arg in func_node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        signature = f"def {func_node.name}({', '.join(args)})"
        
        if func_node.returns:
            signature += f" -> {ast.unparse(func_node.returns)}"
        
        signature += ":"
        return signature
    
    def _generate_annotated_signature(self, func_node: ast.FunctionDef, missing_hints: List[Dict]) -> str:
        """Generate fully annotated function signature."""
        # Build parameter list with types
        args = []
        param_hints = {h['name']: h['suggested_type'] for h in missing_hints if h['kind'] == 'parameter'}
        
        for arg in func_node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            elif arg.arg in param_hints:
                arg_str += f": {param_hints[arg.arg]}"
            args.append(arg_str)
        
        signature = f"def {func_node.name}({', '.join(args)})"
        
        # Add return type
        if func_node.returns:
            signature += f" -> {ast.unparse(func_node.returns)}"
        else:
            return_hint = next((h for h in missing_hints if h['kind'] == 'return'), None)
            if return_hint:
                signature += f" -> {return_hint['suggested_type']}"
        
        signature += ":"
        return signature


class TypeStubGenerator:
    """Generate .pyi stub files for untyped code."""
    
    def generate_stub(self, code: str, file_path: str = "unknown.py") -> Dict:
        """Generate a .pyi stub file content."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error": "Failed to parse code"}
        
        stub_lines = []
        stub_lines.append("# Type stub generated by ohm-mcp-refactor")
        stub_lines.append("from typing import Any, List, Dict, Optional, Union, Callable, Tuple")
        stub_lines.append("")
        
        # Process classes and functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                stub_lines.extend(self._generate_class_stub(node))
                stub_lines.append("")
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stub_lines.append(self._generate_function_stub(node))
                stub_lines.append("")
        
        stub_content = '\n'.join(stub_lines)
        stub_file_path = file_path.replace('.py', '.pyi')
        
        return {
            "stub_file": stub_file_path,
            "stub_content": stub_content,
            "message": f"Generated type stub for {file_path}"
        }
    
    def _generate_class_stub(self, class_node: ast.ClassDef) -> List[str]:
        """Generate stub for a class."""
        lines = []
        
        # Class definition
        if class_node.bases:
            bases = ', '.join(ast.unparse(b) for b in class_node.bases)
            lines.append(f"class {class_node.name}({bases}):")
        else:
            lines.append(f"class {class_node.name}:")
        
        # Process methods
        has_methods = False
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lines.append("    " + self._generate_function_stub(node))
                has_methods = True
        
        if not has_methods:
            lines.append("    ...")
        
        return lines
    
    def _generate_function_stub(self, func_node: ast.FunctionDef) -> str:
        """Generate stub signature for a function."""
        # Build parameters
        params = []
        for arg in func_node.args.args:
            param_str = arg.arg
            if arg.annotation:
                param_str += f": {ast.unparse(arg.annotation)}"
            else:
                param_str += ": Any"
            params.append(param_str)
        
        # Build signature
        prefix = "async def" if isinstance(func_node, ast.AsyncFunctionDef) else "def"
        signature = f"{prefix} {func_node.name}({', '.join(params)})"
        
        # Add return type
        if func_node.returns:
            signature += f" -> {ast.unparse(func_node.returns)}"
        else:
            signature += " -> Any"
        
        signature += ": ..."
        
        return signature


class TypeHintMigrator:
    """Assist in migrating untyped code to typed code."""
    
    def generate_migration_plan(self, code: str, file_path: str = "unknown.py") -> Dict:
        """Generate a migration plan for adding type hints."""
        analyzer = TypeHintCoverageAnalyzer()
        suggester = TypeHintSuggester()
        
        coverage = analyzer.analyze(code, file_path)
        suggestions = suggester.suggest_hints(code, file_path)
        
        # Prioritize functions
        priority_order = []
        
        for suggestion in suggestions:
            # Score based on function characteristics
            priority_score = 0
            
            # Public functions are higher priority
            if not suggestion['function'].startswith('_'):
                priority_score += 10
            
            # Functions with many parameters benefit more from typing
            param_count = len([h for h in suggestion['missing_hints'] if h['kind'] == 'parameter'])
            priority_score += param_count * 2
            
            # Functions missing return type
            if any(h['kind'] == 'return' for h in suggestion['missing_hints']):
                priority_score += 5
            
            priority_order.append({
                'function': suggestion['function'],
                'line': suggestion['line'],
                'priority_score': priority_score,
                'current_signature': suggestion['current_signature'],
                'suggested_signature': suggestion['suggested_signature']
            })
        
        # Sort by priority
        priority_order.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return {
            "file": file_path,
            "current_coverage": coverage['coverage_percent'],
            "target_coverage": 100.0,
            "functions_to_migrate": len(suggestions),
            "estimated_time_minutes": len(suggestions) * 2,  # Rough estimate
            "migration_steps": priority_order,
            "recommendation": self._get_migration_recommendation(coverage['coverage_percent'])
        }
    
    def _get_migration_recommendation(self, current_coverage: float) -> str:
        """Get migration strategy recommendation."""
        if current_coverage < 25:
            return (
                "Start with high-priority public functions. "
                "Add return types first, then parameter types. "
                "Use mypy to validate changes incrementally."
            )
        elif current_coverage < 75:
            return (
                "Continue adding types to remaining public APIs. "
                "Focus on functions with complex signatures. "
                "Consider enabling strict mypy checking."
            )
        else:
            return (
                "Nearly complete! Add types to remaining private functions. "
                "Enable strict mypy mode and fix any remaining issues. "
                "Consider marking the module as fully typed (py.typed)."
            )


class TypeHintAnalyzer:
    """Unified type hint analysis orchestrator."""
    
    def __init__(self):
        self.coverage_analyzer = TypeHintCoverageAnalyzer()
        self.suggester = TypeHintSuggester()
        self.stub_generator = TypeStubGenerator()
        self.migrator = TypeHintMigrator()
    
    def analyze_full(self, code: str, file_path: str = "unknown.py") -> Dict:
        """Comprehensive type hint analysis."""
        try:
            coverage = self.coverage_analyzer.analyze(code, file_path)
            suggestions = self.suggester.suggest_hints(code, file_path)
            migration_plan = self.migrator.generate_migration_plan(code, file_path)
            
            return {
                "file": file_path,
                "coverage": coverage,
                "total_suggestions": len(suggestions),
                "suggestions": suggestions,
                "migration_plan": migration_plan,
                "success": True
            }
        except Exception as e:
            return {
                "file": file_path,
                "success": False,
                "error": str(e),
                "message": f"Error analyzing type hints: {str(e)}"
            }
    
    def analyze_coverage_only(self, code: str, file_path: str = "unknown.py") -> Dict:
        """Simplified analysis - coverage only."""
        try:
            return self.coverage_analyzer.analyze(code, file_path)
        except Exception as e:
            return {
                "file": file_path,
                "success": False,
                "error": str(e)
            }


