"""
Architecture-level analysis for detecting design smells and SOLID violations.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple


class GodObjectDetector:
    """Detect God Objects (classes that do too much)."""
    
    def __init__(self, max_lines: int = 500, max_methods: int = 20):
        self.max_lines = max_lines
        self.max_methods = max_methods
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """
        Find classes that exceed complexity thresholds.
        
        Returns:
            List of god object violations with metrics.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return [{"error": "Failed to parse code", "file": file_path}]
        
        god_objects = []
        lines = code.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                
                # Count methods
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                method_count = len(methods)
                
                # Count lines (class definition to end of last method)
                start_line = node.lineno
                end_line = node.end_lineno or start_line
                loc = end_line - start_line + 1
                
                # Count attributes (instance variables)
                attributes = self._count_attributes(node)
                
                # Check thresholds
                is_god_object = loc > self.max_lines or method_count > self.max_methods
                
                if is_god_object:
                    god_objects.append({
                        "type": "god_object",
                        "severity": "high" if loc > self.max_lines * 1.5 else "medium",
                        "class_name": class_name,
                        "file": file_path,
                        "location": f"lines {start_line}-{end_line}",
                        "metrics": {
                            "lines_of_code": loc,
                            "method_count": method_count,
                            "attribute_count": attributes
                        },
                        "recommendation": (
                            f"Class '{class_name}' is a God Object. "
                            f"Consider splitting into smaller, focused classes following Single Responsibility Principle. "
                            f"Extract related methods into separate classes."
                        )
                    })
        
        return god_objects
    
    def _count_attributes(self, class_node: ast.ClassDef) -> int:
        """Count instance attributes (self.x assignments)."""
        attributes = set()
        for node in ast.walk(class_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                            attributes.add(target.attr)
        return len(attributes)


class CircularDependencyDetector:
    """Detect circular dependencies between modules."""
    
    def detect(self, project_root: str, module_paths: List[str]) -> List[Dict]:
        """
        Build import graph and find circular dependencies.
        
        Args:
            project_root: Root directory of the project.
            module_paths: List of Python file paths to analyze.
        
        Returns:
            List of circular dependency violations.
        """
        # Build import graph
        graph = self._build_import_graph(project_root, module_paths)
        
        # Find cycles
        cycles = self._find_cycles(graph)
        
        violations = []
        for cycle in cycles:
            violations.append({
                "type": "circular_dependency",
                "severity": "high",
                "cycle": " -> ".join(cycle + [cycle[0]]),
                "modules": cycle,
                "recommendation": (
                    f"Circular dependency detected: {' -> '.join(cycle)}. "
                    "Consider introducing an interface/abstract class, "
                    "moving shared code to a common module, or using dependency injection."
                )
            })
        
        return violations
    
    def _build_import_graph(self, project_root: str, module_paths: List[str]) -> Dict[str, Set[str]]:
        """Build directed graph of module imports."""
        graph = {}
        
        for module_path in module_paths:
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                module_name = self._get_module_name(project_root, module_path)
                imports = self._extract_imports(code, project_root)
                graph[module_name] = set(imports)
                
            except Exception as e:
                # Skip files that can't be read
                continue
        
        return graph
    
    def _get_module_name(self, project_root: str, file_path: str) -> str:
        """Convert file path to module name."""
        rel_path = os.path.relpath(file_path, project_root)
        module = rel_path.replace(os.sep, '.').replace('.py', '')
        return module
    
    def _extract_imports(self, code: str, project_root: str) -> List[str]:
        """Extract local imports from code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    
    def _find_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Find all cycles in the import graph using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:]
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles


class SOLIDViolationDetector:
    """Detect violations of SOLID principles using heuristics."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """
        Detect SOLID principle violations.
        
        Returns:
            List of violations with recommendations.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return [{"error": "Failed to parse code", "file": file_path}]
        
        violations = []
        
        # Analyze each class
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                violations.extend(self._check_srp(node, file_path))
                violations.extend(self._check_ocp(node, file_path))
                violations.extend(self._check_lsp(node, file_path))
                violations.extend(self._check_isp(node, file_path))
                violations.extend(self._check_dip(node, file_path))
        
        return violations
    
    def _check_srp(self, class_node: ast.ClassDef, file_path: str) -> List[Dict]:
        """Single Responsibility Principle: One class, one reason to change."""
        violations = []
        
        # Heuristic: class has too many unrelated methods
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        method_names = [m.name for m in methods if not m.name.startswith('_')]
        
        # Check for unrelated verbs (save, load, validate, send, render, etc.)
        unrelated_verbs = self._detect_unrelated_verbs(method_names)
        
        if len(unrelated_verbs) >= 3:
            violations.append({
                "type": "srp_violation",
                "principle": "Single Responsibility Principle",
                "severity": "medium",
                "class_name": class_node.name,
                "file": file_path,
                "location": f"line {class_node.lineno}",
                "description": f"Class '{class_node.name}' appears to have multiple responsibilities",
                "evidence": f"Contains unrelated method groups: {', '.join(unrelated_verbs)}",
                "recommendation": (
                    "Split this class into smaller classes, each with a single responsibility. "
                    "For example, separate data access, business logic, and presentation concerns."
                )
            })
        
        return violations
    
    def _detect_unrelated_verbs(self, method_names: List[str]) -> List[str]:
        """Detect groups of unrelated method verbs."""
        verb_groups = {
            'data': ['save', 'load', 'read', 'write', 'fetch', 'store'],
            'validation': ['validate', 'check', 'verify', 'ensure'],
            'presentation': ['render', 'display', 'show', 'format', 'draw'],
            'communication': ['send', 'receive', 'notify', 'publish', 'subscribe'],
            'computation': ['calculate', 'compute', 'process', 'transform']
        }
        
        found_groups = set()
        for method in method_names:
            method_lower = method.lower()
            for group_name, verbs in verb_groups.items():
                if any(verb in method_lower for verb in verbs):
                    found_groups.add(group_name)
        
        return list(found_groups)
    
    def _check_ocp(self, class_node: ast.ClassDef, file_path: str) -> List[Dict]:
        """Open/Closed Principle: Open for extension, closed for modification."""
        violations = []
        
        # Heuristic: methods with large if/elif chains (should use polymorphism)
        for method in [n for n in class_node.body if isinstance(n, ast.FunctionDef)]:
            if_count = sum(1 for _ in ast.walk(method) if isinstance(_, ast.If))
            
            if if_count > 5:
                violations.append({
                    "type": "ocp_violation",
                    "principle": "Open/Closed Principle",
                    "severity": "medium",
                    "class_name": class_node.name,
                    "method_name": method.name,
                    "file": file_path,
                    "location": f"line {method.lineno}",
                    "description": f"Method '{method.name}' has {if_count} conditional branches",
                    "recommendation": (
                        "Consider using Strategy pattern or polymorphism to extend behavior "
                        "without modifying existing code. Replace if/elif chains with subclasses."
                    )
                })
        
        return violations
    
    def _check_lsp(self, class_node: ast.ClassDef, file_path: str) -> List[Dict]:
        """Liskov Substitution Principle: Subtypes must be substitutable."""
        violations = []
        
        # Heuristic: overridden methods that raise NotImplementedError
        for method in [n for n in class_node.body if isinstance(n, ast.FunctionDef)]:
            for node in ast.walk(method):
                if isinstance(node, ast.Raise):
                    if isinstance(node.exc, ast.Call):
                        if isinstance(node.exc.func, ast.Name):
                            if node.exc.func.id == 'NotImplementedError':
                                violations.append({
                                    "type": "lsp_violation",
                                    "principle": "Liskov Substitution Principle",
                                    "severity": "low",
                                    "class_name": class_node.name,
                                    "method_name": method.name,
                                    "file": file_path,
                                    "location": f"line {node.lineno}",
                                    "description": f"Method '{method.name}' raises NotImplementedError",
                                    "recommendation": (
                                        "Don't inherit methods you can't implement. "
                                        "Consider using composition or a different abstraction."
                                    )
                                })
        
        return violations
    
    def _check_isp(self, class_node: ast.ClassDef, file_path: str) -> List[Dict]:
        """Interface Segregation Principle: Many specific interfaces > one general."""
        violations = []
        
        # Heuristic: interfaces/base classes with too many methods
        # Check if this is likely a base class (has abstract methods or pass statements)
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        
        if len(methods) > 10:
            has_abstract = any(
                any(isinstance(d, ast.Name) and d.id in ['abstractmethod', 'ABC'] 
                    for d in getattr(m, 'decorator_list', []))
                for m in methods
            )
            
            if has_abstract or class_node.name.endswith('Interface') or class_node.name.startswith('I'):
                violations.append({
                    "type": "isp_violation",
                    "principle": "Interface Segregation Principle",
                    "severity": "medium",
                    "class_name": class_node.name,
                    "file": file_path,
                    "location": f"line {class_node.lineno}",
                    "description": f"Interface '{class_node.name}' has {len(methods)} methods",
                    "recommendation": (
                        "Split this fat interface into smaller, more specific interfaces. "
                        "Clients should not depend on methods they don't use."
                    )
                })
        
        return violations
    
    def _check_dip(self, class_node: ast.ClassDef, file_path: str) -> List[Dict]:
        """Dependency Inversion Principle: Depend on abstractions, not concretions."""
        violations = []
        
        # Heuristic: direct instantiation of concrete classes inside methods
        for method in [n for n in class_node.body if isinstance(n, ast.FunctionDef)]:
            instantiations = []
            
            for node in ast.walk(method):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        # Check if calling a class constructor (uppercase first letter)
                        if node.func.id[0].isupper():
                            instantiations.append(node.func.id)
            
            if len(instantiations) >= 3:
                violations.append({
                    "type": "dip_violation",
                    "principle": "Dependency Inversion Principle",
                    "severity": "low",
                    "class_name": class_node.name,
                    "method_name": method.name,
                    "file": file_path,
                    "location": f"line {method.lineno}",
                    "description": f"Method instantiates {len(instantiations)} concrete classes",
                    "evidence": f"Direct instantiation of: {', '.join(set(instantiations))}",
                    "recommendation": (
                        "Use dependency injection instead of direct instantiation. "
                        "Depend on interfaces/abstract classes, not concrete implementations."
                    )
                })
        
        return violations


class ArchitectureAnalyzer:
    """Unified architecture analysis orchestrator."""
    
    def __init__(self):
        self.god_object_detector = GodObjectDetector()
        self.circular_dep_detector = CircularDependencyDetector()
        self.solid_detector = SOLIDViolationDetector()
    
    def analyze_file(self, code: str, file_path: str = "unknown.py") -> Dict:
        """Analyze a single file for architectural issues."""
        issues = []
        
        # Detect God Objects
        issues.extend(self.god_object_detector.detect(code, file_path))
        
        # Detect SOLID violations
        issues.extend(self.solid_detector.detect(code, file_path))
        
        return {
            "file": file_path,
            "total_issues": len(issues),
            "issues_by_type": self._categorize_by_type(issues),
            "issues_by_severity": self._categorize_by_severity(issues),
            "detailed_issues": issues
        }
    
    def analyze_project(self, project_root: str, module_paths: List[str]) -> Dict:
        """Analyze entire project for architectural issues."""
        all_issues = []
        
        # Analyze each file
        for module_path in module_paths:
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                file_analysis = self.analyze_file(code, module_path)
                all_issues.extend(file_analysis["detailed_issues"])
            except Exception:
                continue
        
        # Detect circular dependencies across files
        circular_deps = self.circular_dep_detector.detect(project_root, module_paths)
        all_issues.extend(circular_deps)
        
        return {
            "project_root": project_root,
            "files_analyzed": len(module_paths),
            "total_issues": len(all_issues),
            "issues_by_type": self._categorize_by_type(all_issues),
            "issues_by_severity": self._categorize_by_severity(all_issues),
            "detailed_issues": all_issues
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
