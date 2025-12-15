"""
Performance Hotspot Analysis - Identify inefficient algorithms and suggest optimizations.
"""

import ast
from typing import Dict, List, Set, Optional, Tuple


class ComplexityAnalyzer:
    """Analyze algorithmic complexity patterns."""
    
    def detect_complexity_issues(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Detect O(n²) and worse complexity patterns."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Detect nested loops
                nested_loops = self._detect_nested_loops(node)
                if nested_loops:
                    issues.append({
                        "type": "nested_loops",
                        "severity": "high",
                        "location": f"line {node.lineno}",
                        "file": file_path,
                        "function": node.name,
                        "nesting_level": nested_loops['level'],
                        "complexity": f"O(n^{nested_loops['level']})",
                        "description": f"Nested loops with depth {nested_loops['level']} detected",
                        "problem": f"Complexity is O(n^{nested_loops['level']}), can be slow for large datasets",
                        "recommendation": "Consider using hash maps, sets, or optimized algorithms",
                        "refactor_example": self._generate_nested_loop_optimization(nested_loops)
                    })
                
                # Detect quadratic list operations
                quadratic_ops = self._detect_quadratic_list_ops(node)
                if quadratic_ops:
                    issues.extend(quadratic_ops)
        
        return issues
    
    def _detect_nested_loops(self, func_node: ast.FunctionDef) -> Optional[Dict]:
        """Detect nested loops and calculate depth."""
        max_depth = 0
        deepest_location = None
        
        def check_nesting(node, depth=0):
            nonlocal max_depth, deepest_location
            
            if isinstance(node, (ast.For, ast.While)):
                depth += 1
                if depth > max_depth:
                    max_depth = depth
                    deepest_location = node.lineno
                
                # Recursively check children
                for child in ast.iter_child_nodes(node):
                    check_nesting(child, depth)
            else:
                for child in ast.iter_child_nodes(node):
                    check_nesting(child, depth)
        
        check_nesting(func_node)
        
        if max_depth >= 2:
            return {
                "level": max_depth,
                "location": deepest_location
            }
        
        return None
    
    def _detect_quadratic_list_ops(self, func_node: ast.FunctionDef) -> List[Dict]:
        """Detect O(n²) list operations like 'x in list' inside loops."""
        issues = []
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                # Check for 'in' operations on lists inside loop
                for child in ast.walk(node):
                    if isinstance(child, ast.Compare):
                        for op, comparator in zip(child.ops, child.comparators):
                            if isinstance(op, ast.In):
                                # Check if comparator is a list
                                if isinstance(comparator, (ast.List, ast.Name)):
                                    issues.append({
                                        "type": "quadratic_membership_test",
                                        "severity": "medium",
                                        "location": f"line {child.lineno}",
                                        "file": func_node.name,
                                        "function": func_node.name,
                                        "description": "Membership test ('in') on list inside loop",
                                        "problem": "List membership testing is O(n), making this O(n²)",
                                        "recommendation": "Convert list to set for O(1) lookup",
                                        "refactor_example": "# Before: if x in my_list\n# After: my_set = set(my_list); if x in my_set"
                                    })
        
        return issues
    
    def _generate_nested_loop_optimization(self, nested_info: Dict) -> str:
        """Generate example optimization for nested loops."""
        if nested_info['level'] == 2:
            return """
# Before: O(n²) nested loops
for item1 in list1:
    for item2 in list2:
        if item1 == item2:
            result.append(item1)

# After: O(n) using set intersection
set1 = set(list1)
set2 = set(list2)
result = list(set1 & set2)

# Or use dictionary for lookup
lookup = {item: True for item in list2}
result = [item for item in list1 if item in lookup]
"""
        elif nested_info['level'] == 3:
            return """
# Before: O(n³) triple nested loops
for i in list1:
    for j in list2:
        for k in list3:
            # operations

# After: Consider algorithms like:
# - Hash maps for lookups
# - Sorting + binary search
# - Dynamic programming
# - Divide and conquer
"""
        return "Consider algorithmic optimization based on specific use case"


class RedundantWorkDetector:
    """Detect redundant computations and repeated work."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Detect redundant work patterns."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Detect repeated function calls
                repeated_calls = self._detect_repeated_calls(node)
                if repeated_calls:
                    issues.extend(repeated_calls)
                
                # Detect repeated list comprehensions
                repeated_comps = self._detect_repeated_comprehensions(node)
                if repeated_comps:
                    issues.extend(repeated_comps)
                
                # Detect loop invariant code
                invariant_code = self._detect_loop_invariants(node)
                if invariant_code:
                    issues.extend(invariant_code)
        
        return issues
    
    def _detect_repeated_calls(self, func_node: ast.FunctionDef) -> List[Dict]:
        """Detect same function called multiple times with same arguments."""
        issues = []
        call_counts = {}
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                call_str = ast.unparse(node)
                
                if call_str not in call_counts:
                    call_counts[call_str] = []
                call_counts[call_str].append(node.lineno)
        
        for call, lines in call_counts.items():
            if len(lines) >= 3:  # Called 3+ times
                issues.append({
                    "type": "repeated_function_call",
                    "severity": "low",
                    "location": f"lines {', '.join(map(str, lines[:3]))}",
                    "file": func_node.name,
                    "function": func_node.name,
                    "call": call,
                    "occurrences": len(lines),
                    "description": f"Function call '{call}' repeated {len(lines)} times",
                    "problem": "Repeated expensive calls waste computation",
                    "recommendation": "Cache result in a variable or use @functools.lru_cache",
                    "refactor_example": f"""
# Before:
result1 = {call}
result2 = {call}
result3 = {call}

# After:
cached_result = {call}
result1 = cached_result
result2 = cached_result
result3 = cached_result

# Or use caching decorator:
@functools.lru_cache(maxsize=128)
def expensive_function(...):
    ...
"""
                })
        
        return issues
    
    def _detect_repeated_comprehensions(self, func_node: ast.FunctionDef) -> List[Dict]:
        """Detect repeated list/dict comprehensions."""
        issues = []
        comp_counts = {}
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
                comp_str = ast.unparse(node)
                
                if comp_str not in comp_counts:
                    comp_counts[comp_str] = []
                comp_counts[comp_str].append(node.lineno)
        
        for comp, lines in comp_counts.items():
            if len(lines) >= 2:
                issues.append({
                    "type": "repeated_comprehension",
                    "severity": "medium",
                    "location": f"lines {', '.join(map(str, lines))}",
                    "file": func_node.name,
                    "function": func_node.name,
                    "comprehension": comp,
                    "occurrences": len(lines),
                    "description": f"Comprehension repeated {len(lines)} times",
                    "problem": "Repeated comprehensions waste memory and CPU",
                    "recommendation": "Compute once and reuse the result"
                })
        
        return issues
    
    def _detect_loop_invariants(self, func_node: ast.FunctionDef) -> List[Dict]:
        """Detect code inside loops that doesn't depend on loop variable."""
        issues = []
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                loop_var = None
                if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                    loop_var = node.target.id
                
                # Check for function calls that don't use loop variable
                for child in node.body:
                    if isinstance(child, ast.Assign):
                        if loop_var and not self._uses_variable(child.value, loop_var):
                            issues.append({
                                "type": "loop_invariant_code",
                                "severity": "low",
                                "location": f"line {child.lineno}",
                                "file": func_node.name,
                                "function": func_node.name,
                                "description": "Code inside loop doesn't depend on loop variable",
                                "problem": "Loop-invariant code executed repeatedly",
                                "recommendation": "Move computation outside the loop"
                            })
        
        return issues
    
    def _uses_variable(self, node: ast.AST, var_name: str) -> bool:
        """Check if a node uses a specific variable."""
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id == var_name:
                return True
        return False


class AntiPatternDetector:
    """Detect Python-specific performance anti-patterns."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Detect performance anti-patterns."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        issues = []
        
        # Detect mutable default arguments
        issues.extend(self._detect_mutable_defaults(tree, file_path))
        
        # Detect inefficient string concatenation
        issues.extend(self._detect_string_concat(tree, file_path))
        
        # Detect unnecessary deep copies
        issues.extend(self._detect_unnecessary_copies(tree, file_path))
        
        # Detect missing generator usage
        issues.extend(self._detect_missing_generators(tree, file_path))
        
        return issues
    
    def _detect_mutable_defaults(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Detect mutable default arguments (list, dict, set)."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            "type": "mutable_default_argument",
                            "severity": "high",
                            "location": f"line {node.lineno}",
                            "file": file_path,
                            "function": node.name,
                            "description": f"Function '{node.name}' has mutable default argument",
                            "problem": "Mutable defaults are shared across calls, causing bugs and memory leaks",
                            "recommendation": "Use None as default and create mutable in function body",
                            "refactor_example": """
# Before: DANGEROUS
def process(items=[]):
    items.append(1)
    return items

# After: SAFE
def process(items=None):
    if items is None:
        items = []
    items.append(1)
    return items
"""
                        })
        
        return issues
    
    def _detect_string_concat(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Detect inefficient string concatenation in loops."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Look for string concatenation with +=
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign):
                        if isinstance(child.op, ast.Add):
                            if isinstance(child.target, ast.Name):
                                issues.append({
                                    "type": "inefficient_string_concatenation",
                                    "severity": "medium",
                                    "location": f"line {child.lineno}",
                                    "file": file_path,
                                    "description": "String concatenation with += in loop",
                                    "problem": "String concatenation creates new strings (O(n²) complexity)",
                                    "recommendation": "Use str.join() or list accumulation",
                                    "refactor_example": """
# Before: O(n²)
result = ""
for item in items:
    result += str(item)

# After: O(n)
parts = []
for item in items:
    parts.append(str(item))
result = "".join(parts)

# Or use comprehension:
result = "".join(str(item) for item in items)
"""
                                })
        
        return issues
    
    def _detect_unnecessary_copies(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Detect unnecessary deep copies."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for copy.deepcopy or list.copy()
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['copy', 'deepcopy']:
                        issues.append({
                            "type": "potential_unnecessary_copy",
                            "severity": "low",
                            "location": f"line {node.lineno}",
                            "file": file_path,
                            "description": "Deep copy detected",
                            "problem": "Deep copies are expensive; ensure they're necessary",
                            "recommendation": "Use shallow copy if possible, or pass references"
                        })
        
        return issues
    
    def _detect_missing_generators(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Detect where generators would be more efficient than lists."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Look for large list comprehensions that are only iterated
                for child in ast.walk(node):
                    if isinstance(child, ast.ListComp):
                        # Check if list is only used in a for loop
                        parent_context = self._find_parent_context(tree, child)
                        if parent_context and isinstance(parent_context, ast.For):
                            issues.append({
                                "type": "list_comprehension_to_generator",
                                "severity": "low",
                                "location": f"line {child.lineno}",
                                "file": file_path,
                                "function": node.name,
                                "description": "List comprehension used only for iteration",
                                "problem": "List comprehensions load entire result in memory",
                                "recommendation": "Use generator expression for memory efficiency",
                                "refactor_example": """
# Before: Loads all items in memory
result = [process(x) for x in large_list]
for item in result:
    use(item)

# After: Processes items one at a time
result = (process(x) for x in large_list)  # Generator
for item in result:
    use(item)
"""
                            })
        
        return issues
    
    def _find_parent_context(self, tree: ast.AST, target_node: ast.AST) -> Optional[ast.AST]:
        """Find parent node of a target node (simplified)."""
        # This is a simplified implementation
        # Real implementation would track parent relationships
        return None


class PerformanceAnalyzer:
    """Unified performance analysis orchestrator."""
    
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.redundant_work_detector = RedundantWorkDetector()
        self.anti_pattern_detector = AntiPatternDetector()
    
    def analyze_performance(self, code: str, file_path: str = "unknown.py") -> Dict:
        """Comprehensive performance analysis."""
        issues = []
        
        # Detect complexity issues
        issues.extend(self.complexity_analyzer.detect_complexity_issues(code, file_path))
        
        # Detect redundant work
        issues.extend(self.redundant_work_detector.detect(code, file_path))
        
        # Detect anti-patterns
        issues.extend(self.anti_pattern_detector.detect(code, file_path))
        
        return {
            "file": file_path,
            "total_issues": len(issues),
            "issues_by_type": self._categorize_by_type(issues),
            "issues_by_severity": self._categorize_by_severity(issues),
            "detailed_issues": issues,
            "summary": self._generate_summary(issues)
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
    
    def _generate_summary(self, issues: List[Dict]) -> str:
        """Generate performance summary."""
        if not issues:
            return "✅ No performance issues detected"
        
        by_severity = self._categorize_by_severity(issues)
        
        lines = []
        lines.append(f"Found {len(issues)} performance issue(s):")
        
        if by_severity["high"]:
            lines.append(f"  🔴 {len(by_severity['high'])} high-severity issues (immediate attention needed)")
        
        if by_severity["medium"]:
            lines.append(f"  🟡 {len(by_severity['medium'])} medium-severity issues")
        
        if by_severity["low"]:
            lines.append(f"  🟢 {len(by_severity['low'])} low-severity issues (optimization opportunities)")
        
        return '\n'.join(lines)
