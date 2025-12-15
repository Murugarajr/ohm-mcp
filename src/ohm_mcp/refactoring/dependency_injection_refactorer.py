"""
Dependency Injection Refactorer - Identify tight coupling and suggest DI patterns.
"""

import ast
from typing import Dict, List, Set, Optional, Tuple


class TightCouplingDetector:
    """Detect tight coupling patterns that should use dependency injection."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """
        Detect tight coupling issues.
        
        Returns:
            List of coupling issues with recommendations
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        issues = []
        
        # Detect global variable usage
        issues.extend(self._detect_global_usage(tree, file_path))
        
        # Detect hard-coded instantiation
        issues.extend(self._detect_hardcoded_instantiation(tree, file_path))
        
        # Detect singleton patterns
        issues.extend(self._detect_singletons(tree, file_path))
        
        # Detect static method dependencies
        issues.extend(self._detect_static_dependencies(tree, file_path))
        
        return issues
    
    def _detect_global_usage(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Detect usage of global variables in functions/methods."""
        issues = []
        
        # Find module-level variables
        module_vars = set()
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        module_vars.add(target.id)
        
        # Check functions for global usage
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                globals_used = self._find_global_usage_in_function(node, module_vars)
                
                if globals_used:
                    issues.append({
                        "type": "global_variable_usage",
                        "severity": "medium",
                        "location": f"line {node.lineno}",
                        "file": file_path,
                        "function": node.name,
                        "globals_used": list(globals_used),
                        "description": f"Function '{node.name}' uses global variables: {', '.join(globals_used)}",
                        "problem": "Global variables create hidden dependencies and make testing difficult",
                        "recommendation": "Use constructor injection or pass as parameters",
                        "refactor_example": self._generate_global_di_example(node.name, globals_used)
                    })
        
        return issues
    
    def _find_global_usage_in_function(
        self,
        func_node: ast.FunctionDef,
        module_vars: Set[str]
    ) -> Set[str]:
        """Find global variables used in a function."""
        # Get function parameters and local variables
        local_vars = set()
        
        # Parameters
        for arg in func_node.args.args:
            local_vars.add(arg.arg)
        
        # Local assignments
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        local_vars.add(target.id)
        
        # Find names that are used but not local
        used_names = set()
        for node in ast.walk(func_node):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
        
        # Globals are used names that are in module_vars but not local
        globals_used = (used_names & module_vars) - local_vars
        
        # Filter out builtins and common constants
        globals_used = {
            name for name in globals_used
            if name not in ['True', 'False', 'None']
        }
        
        return globals_used
    
    def _detect_hardcoded_instantiation(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Detect hard-coded class instantiation inside methods."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip __init__ methods (instantiation here is often intentional)
                if node.name == '__init__':
                    continue
                
                instantiations = self._find_class_instantiations(node)
                
                if len(instantiations) >= 2:  # Multiple instantiations suggest tight coupling
                    issues.append({
                        "type": "hardcoded_instantiation",
                        "severity": "medium",
                        "location": f"line {node.lineno}",
                        "file": file_path,
                        "function": node.name,
                        "instantiations": instantiations,
                        "description": f"Function '{node.name}' creates {len(instantiations)} objects directly",
                        "problem": "Hard-coded instantiation makes code difficult to test and extend",
                        "recommendation": "Use constructor injection or factory pattern",
                        "refactor_example": self._generate_di_example(node.name, instantiations)
                    })
        
        return issues
    
    def _find_class_instantiations(self, func_node: ast.FunctionDef) -> List[Dict]:
        """Find class instantiations in a function."""
        instantiations = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                # Check if calling a class constructor (uppercase first letter)
                if isinstance(node.func, ast.Name):
                    if node.func.id[0].isupper():
                        instantiations.append({
                            "class": node.func.id,
                            "line": node.lineno
                        })
                
                # Check for attribute-based instantiation (e.g., module.Class())
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr[0].isupper():
                        instantiations.append({
                            "class": node.func.attr,
                            "line": node.lineno
                        })
        
        return instantiations
    
    def _detect_singletons(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Detect singleton patterns."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                is_singleton = self._is_singleton_pattern(node)
                
                if is_singleton:
                    issues.append({
                        "type": "singleton_pattern",
                        "severity": "low",
                        "location": f"line {node.lineno}",
                        "file": file_path,
                        "class": node.name,
                        "description": f"Class '{node.name}' uses singleton pattern",
                        "problem": "Singletons create global state and make testing difficult",
                        "recommendation": "Use dependency injection instead of singletons",
                        "refactor_example": self._generate_singleton_di_example(node.name)
                    })
        
        return issues
    
    def _is_singleton_pattern(self, class_node: ast.ClassDef) -> bool:
        """Check if a class implements singleton pattern."""
        has_instance_attr = False
        has_new_or_init = False
        
        for node in class_node.body:
            # Check for _instance class variable
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id in ['_instance', '__instance', 'instance']:
                            has_instance_attr = True
            
            # Check for __new__ or getInstance methods
            if isinstance(node, ast.FunctionDef):
                if node.name in ['__new__', 'getInstance', 'get_instance']:
                    has_new_or_init = True
        
        return has_instance_attr and has_new_or_init
    
    def _detect_static_dependencies(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Detect static method calls that should be injected."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                static_calls = self._find_static_calls(node)
                
                if len(static_calls) >= 3:  # Multiple static calls suggest coupling
                    issues.append({
                        "type": "static_method_dependencies",
                        "severity": "low",
                        "location": f"line {node.lineno}",
                        "file": file_path,
                        "function": node.name,
                        "static_calls": static_calls,
                        "description": f"Function '{node.name}' makes {len(static_calls)} static method calls",
                        "problem": "Static method calls create hidden dependencies",
                        "recommendation": "Inject dependencies as interfaces",
                        "refactor_example": "Use dependency injection with abstract interfaces"
                    })
        
        return issues
    
    def _find_static_calls(self, func_node: ast.FunctionDef) -> List[str]:
        """Find static method calls in a function."""
        static_calls = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Class.method() pattern
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id[0].isupper():  # Likely a class
                            call_str = f"{node.func.value.id}.{node.func.attr}()"
                            static_calls.append(call_str)
        
        return static_calls
    
    def _generate_global_di_example(self, func_name: str, globals_used: Set[str]) -> str:
        """Generate example of injecting global dependencies."""
        globals_list = list(globals_used)
        
        return f"""
# Before: Using global variables
{globals_list[0]} = SomeService()

def {func_name}():
    result = {globals_list[0]}.do_something()
    return result

# After: Dependency injection
class MyClass:
    def __init__(self, {', '.join(f'{g}_service' for g in globals_list)}):
        {''.join(f'self.{g}_service = {g}_service\n        ' for g in globals_list)}
    
    def {func_name}(self):
        result = self.{globals_list[0]}_service.do_something()
        return result

# Usage
service = SomeService()
obj = MyClass({', '.join(f'{g}_service=service' for g in globals_list)})
obj.{func_name}()
"""
    
    def _generate_di_example(self, func_name: str, instantiations: List[Dict]) -> str:
        """Generate example of dependency injection."""
        classes = [inst['class'] for inst in instantiations[:2]]
        
        return f"""
# Before: Hard-coded instantiation
def {func_name}():
    service1 = {classes[0]}()
    service2 = {classes[1] if len(classes) > 1 else 'OtherService'}()
    result = service1.process(service2.get_data())
    return result

# After: Constructor injection
class MyClass:
    def __init__(self, service1: {classes[0]}, service2: {classes[1] if len(classes) > 1 else 'OtherService'}):
        self.service1 = service1
        self.service2 = service2
    
    def {func_name}(self):
        result = self.service1.process(self.service2.get_data())
        return result

# Usage (with dependency injection container)
service1 = {classes[0]}()
service2 = {classes[1] if len(classes) > 1 else 'OtherService'}()
obj = MyClass(service1, service2)
obj.{func_name}()
"""
    
    def _generate_singleton_di_example(self, class_name: str) -> str:
        """Generate example of replacing singleton with DI."""
        return f"""
# Before: Singleton pattern
class {class_name}:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Usage
service = {class_name}()  # Always returns same instance

# After: Dependency injection (no singleton)
class {class_name}:
    def __init__(self):
        # Normal initialization
        pass

# Usage with DI container or manual injection
service = {class_name}()  # Create once
app = Application(service)  # Inject where needed
worker = Worker(service)     # Reuse same instance if needed

# Or use a DI container (e.g., dependency-injector, injector)
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    service = providers.Singleton({class_name})
    app = providers.Factory(Application, service=service)
"""


class DIRefactorSuggester:
    """Generate concrete refactoring suggestions for DI."""
    
    def suggest_di_refactor(
        self,
        code: str,
        class_name: str,
        file_path: str = "unknown.py"
    ) -> Dict:
        """
        Suggest DI refactor for a specific class.
        
        Returns:
            {
              "current_code": str,
              "refactored_code": str,
              "changes": [...],
              "dependencies_identified": [...]
            }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error": "Failed to parse code"}
        
        # Find the class
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_node = node
                break
        
        if not class_node:
            return {"error": f"Class '{class_name}' not found"}
        
        # Identify dependencies
        dependencies = self._identify_dependencies(class_node)
        
        # Generate refactored version
        refactored_class = self._generate_di_class(class_node, dependencies)
        
        return {
            "class": class_name,
            "file": file_path,
            "dependencies_identified": dependencies,
            "current_code": ast.unparse(class_node),
            "refactored_code": refactored_class,
            "changes": [
                "Added constructor with dependency parameters",
                "Replaced direct instantiation with injected dependencies",
                "Stored dependencies as instance variables"
            ]
        }
    
    def _identify_dependencies(self, class_node: ast.ClassDef) -> List[Dict]:
        """Identify dependencies in a class."""
        dependencies = []
        seen_classes = set()
        
        for node in ast.walk(class_node):
            # Find class instantiations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id[0].isupper() and node.func.id not in seen_classes:
                        dependencies.append({
                            "class": node.func.id,
                            "suggested_param": node.func.id.lower() + "_service"
                        })
                        seen_classes.add(node.func.id)
        
        return dependencies
    
    def _generate_di_class(self, class_node: ast.ClassDef, dependencies: List[Dict]) -> str:
        """Generate refactored class with DI."""
        lines = []
        
        # Class definition
        if class_node.bases:
            bases = ', '.join(ast.unparse(b) for b in class_node.bases)
            lines.append(f"class {class_node.name}({bases}):")
        else:
            lines.append(f"class {class_node.name}:")
        
        # Constructor with DI
        if dependencies:
            params = ', '.join(f"{dep['suggested_param']}" for dep in dependencies)
            lines.append(f"    def __init__(self, {params}):")
            lines.append('        """Initialize with injected dependencies."""')
            
            for dep in dependencies:
                lines.append(f"        self.{dep['suggested_param']} = {dep['suggested_param']}")
            lines.append("")
        else:
            lines.append("    def __init__(self):")
            lines.append('        """Initialize."""')
            lines.append("        pass")
            lines.append("")
        
        # Other methods (simplified - would need full implementation)
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name != '__init__':
                lines.append(f"    def {node.name}(self{self._get_params_str(node)}):")
                lines.append(f'        """TODO: Refactor to use injected dependencies."""')
                lines.append("        pass")
                lines.append("")
        
        return '\n'.join(lines)
    
    def _get_params_str(self, func_node: ast.FunctionDef) -> str:
        """Get parameter string for a function."""
        params = []
        for arg in func_node.args.args[1:]:  # Skip 'self'
            params.append(arg.arg)
        
        return ', ' + ', '.join(params) if params else ''


class DependencyInjectionRefactorer:
    """Unified DI refactoring orchestrator."""
    
    def __init__(self):
        self.coupling_detector = TightCouplingDetector()
        self.di_suggester = DIRefactorSuggester()
    
    def analyze_coupling(self, code: str, file_path: str = "unknown.py") -> Dict:
        """Analyze code for tight coupling issues."""
        issues = self.coupling_detector.detect(code, file_path)
        
        return {
            "file": file_path,
            "total_issues": len(issues),
            "issues_by_type": self._categorize_by_type(issues),
            "issues_by_severity": self._categorize_by_severity(issues),
            "detailed_issues": issues,
            "summary": self._generate_summary(issues)
        }
    
    def suggest_di_for_class(
        self,
        code: str,
        class_name: str,
        file_path: str = "unknown.py"
    ) -> Dict:
        """Generate DI refactor suggestion for a specific class."""
        return self.di_suggester.suggest_di_refactor(code, class_name, file_path)
    
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
    
    def _generate_summary(self, issues: List[Dict]) -> str:
        """Generate summary of coupling issues."""
        if not issues:
            return "✅ No tight coupling issues detected"
        
        by_type = self._categorize_by_type(issues)
        
        summary_lines = []
        summary_lines.append(f"Found {len(issues)} coupling issue(s):")
        
        if "global_variable_usage" in by_type:
            count = len(by_type["global_variable_usage"])
            summary_lines.append(f"  • {count} global variable usage(s)")
        
        if "hardcoded_instantiation" in by_type:
            count = len(by_type["hardcoded_instantiation"])
            summary_lines.append(f"  • {count} hard-coded instantiation(s)")
        
        if "singleton_pattern" in by_type:
            count = len(by_type["singleton_pattern"])
            summary_lines.append(f"  • {count} singleton pattern(s)")
        
        if "static_method_dependencies" in by_type:
            count = len(by_type["static_method_dependencies"])
            summary_lines.append(f"  • {count} static method dependencies")
        
        return '\n'.join(summary_lines)
