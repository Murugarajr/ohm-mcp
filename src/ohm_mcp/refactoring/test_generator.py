"""
Characterization Test Generator - Auto-generate tests to capture current behavior.
"""

import ast
import textwrap
from typing import Dict, List, Optional, Set, Tuple, Any


class CharacterizationTestGenerator:
    """Generate pytest tests that capture current behavior of functions."""
    
    def generate_tests_for_file(
        self,
        code: str,
        file_path: str = "unknown.py"
    ) -> Dict:
        """
        Generate characterization tests for all functions in a file.
        
        Returns:
            {
              "test_file": str,
              "test_content": str,
              "functions_tested": int,
              "test_cases_generated": int
            }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error": "Failed to parse code"}
        
        # Collect all testable functions
        functions = self._collect_testable_functions(tree, code)
        
        # Generate tests
        test_lines = []
        test_lines.extend(self._generate_test_header(file_path))
        test_lines.append("")
        
        total_test_cases = 0
        
        for func_info in functions:
            test_code = self._generate_test_for_function(func_info)
            test_lines.extend(test_code)
            test_lines.append("")
            total_test_cases += func_info['test_case_count']
        
        test_content = '\n'.join(test_lines)
        
        # Determine test file name
        if file_path.endswith('.py'):
            base_name = file_path[:-3]
            test_file = f"test_{base_name.split('/')[-1]}.py"
        else:
            test_file = f"test_{file_path}.py"
        
        return {
            "test_file": test_file,
            "test_content": test_content,
            "functions_tested": len(functions),
            "test_cases_generated": total_test_cases,
            "message": f"Generated {total_test_cases} test cases for {len(functions)} functions"
        }
    
    def generate_test_for_function(
        self,
        code: str,
        function_name: str,
        file_path: str = "unknown.py"
    ) -> Dict:
        """
        Generate characterization tests for a specific function.
        
        Returns:
            {
              "function": str,
              "test_content": str,
              "test_cases": list
            }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error": "Failed to parse code"}
        
        # Find the specific function
        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    func_node = node
                    break
        
        if not func_node:
            return {"error": f"Function '{function_name}' not found"}
        
        func_info = self._analyze_function(func_node, code)
        
        # Generate header
        test_lines = self._generate_test_header(file_path)
        test_lines.append("")
        
        # Generate test
        test_lines.extend(self._generate_test_for_function(func_info))
        
        return {
            "function": function_name,
            "test_content": '\n'.join(test_lines),
            "test_cases": func_info['test_cases'],
            "test_case_count": func_info['test_case_count']
        }
    
    def _collect_testable_functions(self, tree: ast.AST, full_code: str) -> List[Dict]:
        """Collect all functions that should have tests."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip private functions and dunder methods
                if node.name.startswith('_'):
                    continue
                
                # Skip if already a test function
                if node.name.startswith('test_'):
                    continue
                
                func_info = self._analyze_function(node, full_code)
                if func_info['params']:  # Only test functions with parameters
                    functions.append(func_info)
        
        return functions
    
    def _analyze_function(self, func_node: ast.FunctionDef, full_code: str) -> Dict:
        """Analyze a function and prepare test generation info."""
        # Get parameters
        params = []
        for arg in func_node.args.args:
            if arg.arg in ['self', 'cls']:
                continue
            
            param_type = self._infer_param_type(func_node, arg.arg)
            param_info = {
                'name': arg.arg,
                'type': param_type,
                'annotation': ast.unparse(arg.annotation) if arg.annotation else None
            }
            params.append(param_info)
        
        # Detect return type
        return_type = self._infer_return_type(func_node)
        
        # Generate test cases
        test_cases = self._generate_test_cases(func_node.name, params, return_type)
        
        return {
            'name': func_node.name,
            'line': func_node.lineno,
            'params': params,
            'return_type': return_type,
            'has_side_effects': self._has_side_effects(func_node),
            'test_cases': test_cases,
            'test_case_count': len(test_cases)
        }
    
    def _infer_param_type(self, func_node: ast.FunctionDef, param_name: str) -> str:
        """Infer parameter type from usage."""
        # Look for type checks, operations, comparisons
        for node in ast.walk(func_node):
            # Check isinstance calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'isinstance':
                    if len(node.args) >= 2:
                        if isinstance(node.args[0], ast.Name) and node.args[0].id == param_name:
                            if isinstance(node.args[1], ast.Name):
                                return node.args[1].id
            
            # Check comparisons with None
            if isinstance(node, ast.Compare):
                if isinstance(node.left, ast.Name) and node.left.id == param_name:
                    for op, comparator in zip(node.ops, node.comparators):
                        if isinstance(comparator, ast.Constant) and comparator.value is None:
                            return 'Optional'
            
            # Check list operations
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id == param_name:
                    return 'list'
            
            # Check iteration
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Name) and node.iter.id == param_name:
                    return 'iterable'
        
        return 'Any'
    
    def _infer_return_type(self, func_node: ast.FunctionDef) -> str:
        """Infer return type from return statements."""
        return_types = set()
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                if node.value is None:
                    return_types.add('None')
                elif isinstance(node.value, ast.Constant):
                    return_types.add(type(node.value.value).__name__)
                elif isinstance(node.value, ast.List):
                    return_types.add('list')
                elif isinstance(node.value, ast.Dict):
                    return_types.add('dict')
                elif isinstance(node.value, ast.Call):
                    return_types.add('object')
        
        if not return_types:
            return 'None'
        elif len(return_types) == 1:
            return return_types.pop()
        else:
            return 'Union'
    
    def _has_side_effects(self, func_node: ast.FunctionDef) -> bool:
        """Detect if function has side effects (I/O, global state, etc.)."""
        for node in ast.walk(func_node):
            # Check for print statements
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['print', 'open', 'write', 'input']:
                        return True
            
            # Check for global keyword
            if isinstance(node, ast.Global):
                return True
            
            # Check for attribute assignment (modifying objects)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        return True
        
        return False
    
    def _generate_test_cases(
        self,
        func_name: str,
        params: List[Dict],
        return_type: str
    ) -> List[Dict]:
        """Generate test cases based on parameter types."""
        if not params:
            # No parameters - simple test
            return [{
                'description': 'basic execution',
                'inputs': {},
                'expected_behavior': 'executes without error'
            }]
        
        test_cases = []
        
        # Generate happy path test
        happy_inputs = {}
        for param in params:
            happy_inputs[param['name']] = self._get_sample_value(param['type'], 'happy')
        
        test_cases.append({
            'description': 'happy path',
            'inputs': happy_inputs,
            'expected_behavior': 'returns valid result'
        })
        
        # Generate edge cases for each parameter
        for param in params:
            edge_values = self._get_edge_cases(param['type'])
            
            for edge_case in edge_values:
                edge_inputs = happy_inputs.copy()
                edge_inputs[param['name']] = edge_case['value']
                
                test_cases.append({
                    'description': f"{param['name']} - {edge_case['case']}",
                    'inputs': edge_inputs,
                    'expected_behavior': edge_case['behavior']
                })
        
        return test_cases
    
    def _get_sample_value(self, param_type: str, scenario: str) -> Any:
        """Get sample value for a parameter type."""
        type_samples = {
            'str': '"test_string"',
            'int': '42',
            'float': '3.14',
            'bool': 'True',
            'list': '[1, 2, 3]',
            'dict': '{"key": "value"}',
            'tuple': '(1, 2)',
            'set': '{1, 2, 3}',
            'iterable': '[1, 2, 3]',
            'Optional': 'None',
            'Any': '42'
        }
        
        return type_samples.get(param_type, '"sample_value"')
    
    def _get_edge_cases(self, param_type: str) -> List[Dict]:
        """Get edge case values for a parameter type."""
        edge_cases = {
            'str': [
                {'case': 'empty string', 'value': '""', 'behavior': 'handles empty input'},
                {'case': 'None', 'value': 'None', 'behavior': 'handles None or raises TypeError'}
            ],
            'int': [
                {'case': 'zero', 'value': '0', 'behavior': 'handles zero'},
                {'case': 'negative', 'value': '-1', 'behavior': 'handles negative numbers'}
            ],
            'list': [
                {'case': 'empty list', 'value': '[]', 'behavior': 'handles empty list'},
                {'case': 'None', 'value': 'None', 'behavior': 'handles None or raises TypeError'}
            ],
            'dict': [
                {'case': 'empty dict', 'value': '{}', 'behavior': 'handles empty dictionary'}
            ],
            'iterable': [
                {'case': 'empty iterable', 'value': '[]', 'behavior': 'handles empty iterable'}
            ]
        }
        
        return edge_cases.get(param_type, [])
    
    def _generate_test_header(self, file_path: str) -> List[str]:
        """Generate test file header with imports."""
        module_name = file_path.replace('.py', '').replace('/', '.').replace('\\', '.')
        if module_name.startswith('.'):
            module_name = module_name[1:]
        
        return [
            '"""',
            'Characterization tests - Auto-generated by ohm-mcp-refactor',
            'These tests capture current behavior before refactoring.',
            '"""',
            '',
            'import pytest',
            f'from {module_name} import *',
            ''
        ]
    
    def _generate_test_for_function(self, func_info: Dict) -> List[str]:
        """Generate test code for a single function."""
        lines = []
        func_name = func_info['name']
        
        # Add function-level comment
        lines.append(f"# Tests for {func_name}()")
        lines.append("")
        
        for i, test_case in enumerate(func_info['test_cases'], 1):
            test_name = f"test_{func_name}_{test_case['description'].replace(' ', '_').replace('-', '_')}"
            
            lines.append(f"def {test_name}():")
            lines.append(f'    """Test {test_case["description"]}."""')
            
            # Generate test body
            if func_info['params']:
                # Build function call
                args = ', '.join(f"{name}={test_case['inputs'][name]}" 
                                for name in test_case['inputs'].keys())
                
                if func_info['has_side_effects']:
                    lines.append(f"    # Function has side effects - verify it executes")
                    lines.append(f"    result = {func_name}({args})")
                    lines.append(f"    # TODO: Add assertions to verify expected behavior")
                    lines.append(f"    assert result is not None or result is None  # Placeholder")
                else:
                    if func_info['return_type'] == 'None':
                        lines.append(f"    # Function returns None")
                        lines.append(f"    result = {func_name}({args})")
                        lines.append(f"    assert result is None")
                    else:
                        lines.append(f"    # Expected: {test_case['expected_behavior']}")
                        lines.append(f"    result = {func_name}({args})")
                        lines.append(f"    # TODO: Replace with actual expected value")
                        lines.append(f"    assert result is not None  # Placeholder assertion")
            else:
                lines.append(f"    result = {func_name}()")
                lines.append(f"    assert result is not None or result is None  # Adjust as needed")
            
            lines.append("")
        
        return lines


class TestCaseEnhancer:
    """Enhance generated tests with more sophisticated test cases."""
    
    def add_property_based_tests(self, func_info: Dict) -> List[str]:
        """Generate property-based tests using hypothesis."""
        lines = []
        func_name = func_info['name']
        
        lines.append(f"# Property-based tests for {func_name}()")
        lines.append("from hypothesis import given, strategies as st")
        lines.append("")
        
        # Generate hypothesis strategy based on parameter types
        strategies = []
        for param in func_info['params']:
            strategy = self._get_hypothesis_strategy(param['type'])
            strategies.append(f"st.{strategy}")
        
        decorators = ', '.join(strategies)
        lines.append(f"@given({decorators})")
        lines.append(f"def test_{func_name}_property_based({', '.join(p['name'] for p in func_info['params'])}):")
        lines.append(f'    """Property-based test to find edge cases."""')
        lines.append(f"    try:")
        
        args = ', '.join(p['name'] for p in func_info['params'])
        lines.append(f"        result = {func_name}({args})")
        lines.append(f"        # Add property assertions here")
        lines.append(f"        assert result is not None or result is None")
        lines.append(f"    except Exception as e:")
        lines.append(f"        # Document exceptions found during property testing")
        lines.append(f"        pytest.fail(f'Unexpected exception: {{e}}')")
        lines.append("")
        
        return lines
    
    def _get_hypothesis_strategy(self, param_type: str) -> str:
        """Get hypothesis strategy for parameter type."""
        strategies = {
            'str': 'text()',
            'int': 'integers()',
            'float': 'floats(allow_nan=False, allow_infinity=False)',
            'bool': 'booleans()',
            'list': 'lists(integers())',
            'dict': 'dictionaries(text(), integers())'
        }
        return strategies.get(param_type, 'text()')


class TestGenerator:
    """Unified test generation orchestrator."""
    
    def __init__(self):
        self.char_test_gen = CharacterizationTestGenerator()
        self.enhancer = TestCaseEnhancer()
    
    def generate_characterization_tests(
        self,
        code: str,
        file_path: str = "unknown.py",
        include_property_tests: bool = False
    ) -> Dict:
        """Generate complete test suite for a file."""
        result = self.char_test_gen.generate_tests_for_file(code, file_path)
        
        if include_property_tests and 'error' not in result:
            # Note: property-based tests require hypothesis library
            result['note'] = "Add hypothesis library for property-based tests: pip install hypothesis"
        
        return result
    
    def generate_test_for_specific_function(
        self,
        code: str,
        function_name: str,
        file_path: str = "unknown.py"
    ) -> Dict:
        """Generate tests for a specific function only."""
        return self.char_test_gen.generate_test_for_function(code, function_name, file_path)
