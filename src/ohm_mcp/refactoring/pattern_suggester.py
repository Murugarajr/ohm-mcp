"""
Design Pattern Suggester - Recommends applicable design patterns based on code smells.
"""

import ast
from typing import Dict, List, Optional


class StrategyPatternDetector:
    """Detect opportunities for Strategy pattern (long if/elif chains)."""
    
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find long if/elif chains that could use Strategy pattern."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if_elif_chains = self._find_if_elif_chains(node)
                
                for chain in if_elif_chains:
                    if chain['count'] >= self.threshold:
                        suggestions.append({
                            "pattern": "Strategy",
                            "severity": "medium" if chain['count'] < 5 else "high",
                            "location": f"line {chain['line']}",
                            "file": file_path,
                            "function": node.name,
                            "description": f"Found {chain['count']} if/elif branches",
                            "current_code_smell": "Long if/elif chain makes code hard to extend and test",
                            "recommended_pattern": "Strategy Pattern",
                            "rationale": (
                                "Each branch represents a different algorithm/behavior. "
                                "Extract each branch into a separate Strategy class."
                            ),
                            "example_refactor": self._generate_strategy_example(node.name, chain['count']),
                            "benefits": [
                                "Open/Closed Principle: Add new strategies without modifying existing code",
                                "Easier unit testing: Test each strategy independently",
                                "Better readability: Each strategy has a clear name and purpose"
                            ]
                        })
        
        return suggestions
    
    def _find_if_elif_chains(self, func_node: ast.FunctionDef) -> List[Dict]:
        """Find if/elif chains in a function."""
        chains = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.If):
                chain_length = 1
                current = node
                
                # Count elif branches
                while hasattr(current, 'orelse') and len(current.orelse) == 1:
                    if isinstance(current.orelse[0], ast.If):
                        chain_length += 1
                        current = current.orelse[0]
                    else:
                        break
                
                if chain_length >= self.threshold:
                    chains.append({
                        'line': node.lineno,
                        'count': chain_length
                    })
        
        return chains
    
    def _generate_strategy_example(self, function_name: str, branch_count: int) -> str:
        """Generate example Strategy pattern refactor."""
        return f"""
# Before: Long if/elif chain in {function_name}()
def {function_name}(type, data):
    if type == 'A':
        # behavior A
    elif type == 'B':
        # behavior B
    elif type == 'C':
        # behavior C
    # ... {branch_count} branches total

# After: Strategy Pattern
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def execute(self, data):
        pass

class StrategyA(Strategy):
    def execute(self, data):
        # behavior A

class StrategyB(Strategy):
    def execute(self, data):
        # behavior B

class StrategyC(Strategy):
    def execute(self, data):
        # behavior C

# Usage
strategies = {{
    'A': StrategyA(),
    'B': StrategyB(),
    'C': StrategyC()
}}

def {function_name}(type, data):
    strategy = strategies.get(type)
    return strategy.execute(data) if strategy else None
"""


class FactoryPatternDetector:
    """Detect opportunities for Factory pattern (repetitive object creation)."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find repetitive constructors that could use Factory pattern."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        suggestions = []
        
        # Analyze each function/method
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                constructor_calls = self._find_constructor_patterns(node)
                
                if len(constructor_calls) >= 3:  # Multiple related constructors
                    class_names = [c['class_name'] for c in constructor_calls]
                    
                    # Check if they're related (similar names or in same module)
                    if self._are_related_classes(class_names):
                        suggestions.append({
                            "pattern": "Factory",
                            "severity": "medium",
                            "location": f"line {node.lineno}",
                            "file": file_path,
                            "function": node.name,
                            "description": f"Multiple object instantiations: {', '.join(set(class_names))}",
                            "current_code_smell": "Repetitive constructor calls with complex initialization logic",
                            "recommended_pattern": "Factory Pattern",
                            "rationale": (
                                "Centralize object creation logic. "
                                "Encapsulate the decision of which class to instantiate."
                            ),
                            "example_refactor": self._generate_factory_example(class_names),
                            "benefits": [
                                "Single point of control for object creation",
                                "Easier to add new types without changing client code",
                                "Encapsulates creation logic and dependencies"
                            ]
                        })
        
        return suggestions
    
    def _find_constructor_patterns(self, func_node: ast.AST) -> List[Dict]:
        """Find constructor calls with complex arguments."""
        constructors = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                # Check if calling a class constructor (uppercase first letter)
                if isinstance(node.func, ast.Name) and node.func.id[0].isupper():
                    # Check if has multiple arguments or keyword arguments
                    if len(node.args) + len(node.keywords) >= 2:
                        constructors.append({
                            'class_name': node.func.id,
                            'line': node.lineno,
                            'arg_count': len(node.args) + len(node.keywords)
                        })
        
        return constructors
    
    def _are_related_classes(self, class_names: List[str]) -> bool:
        """Check if class names suggest they're related (similar naming pattern)."""
        if len(class_names) < 2:
            return False
        
        # Check for common prefixes or suffixes
        prefixes = set()
        suffixes = set()
        
        for name in class_names:
            if len(name) > 3:
                prefixes.add(name[:3])
                suffixes.add(name[-3:])
        
        # If many share prefix/suffix, they're likely related
        return len(prefixes) <= 2 or len(suffixes) <= 2
    
    def _generate_factory_example(self, class_names: List[str]) -> str:
        """Generate example Factory pattern refactor."""
        unique_classes = list(set(class_names))[:3]  # Show first 3 examples
        
        return f"""
# Before: Direct instantiation scattered across code
def process(type, config):
    if type == 'A':
        obj = {unique_classes[0]}(config['param1'], config['param2'])
    elif type == 'B':
        obj = {unique_classes[1] if len(unique_classes) > 1 else 'ClassB'}(config['param1'], config['param3'])
    # ... more repetitive creation logic
    return obj.process()

# After: Factory Pattern
class ObjectFactory:
    @staticmethod
    def create(type: str, config: dict):
        if type == 'A':
            return {unique_classes[0]}(config['param1'], config['param2'])
        elif type == 'B':
            return {unique_classes[1] if len(unique_classes) > 1 else 'ClassB'}(config['param1'], config['param3'])
        else:
            raise ValueError(f"Unknown type: {{type}}")

# Usage
def process(type, config):
    obj = ObjectFactory.create(type, config)
    return obj.process()

# Even better: Use a registry pattern
class ObjectFactory:
    _registry = {{}}
    
    @classmethod
    def register(cls, name: str, creator):
        cls._registry[name] = creator
    
    @classmethod
    def create(cls, name: str, **kwargs):
        creator = cls._registry.get(name)
        if not creator:
            raise ValueError(f"Unknown type: {{name}}")
        return creator(**kwargs)
"""


class ObserverPatternDetector:
    """Detect opportunities for Observer pattern (callback hell / tight coupling)."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find callback patterns that could use Observer pattern."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                callback_patterns = self._find_callback_patterns(node)
                
                if len(callback_patterns) >= 2:
                    suggestions.append({
                        "pattern": "Observer",
                        "severity": "medium",
                        "location": f"line {node.lineno}",
                        "file": file_path,
                        "context": node.name,
                        "description": f"Found {len(callback_patterns)} callback/notification patterns",
                        "current_code_smell": "Tight coupling between components via callbacks",
                        "recommended_pattern": "Observer Pattern",
                        "rationale": (
                            "Decouple subjects from observers. "
                            "Allow multiple observers to react to state changes independently."
                        ),
                        "example_refactor": self._generate_observer_example(node.name),
                        "benefits": [
                            "Loose coupling: Subject doesn't need to know about observers",
                            "Dynamic subscription: Add/remove observers at runtime",
                            "Open/Closed: Add new observers without changing subject"
                        ]
                    })
        
        return suggestions
    
    def _find_callback_patterns(self, node: ast.AST) -> List[Dict]:
        """Find callback patterns: functions passed as arguments, on_* methods, etc."""
        callbacks = []
        
        # Look for function parameters with 'callback', 'handler', 'listener' in name
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                if any(keyword in arg.arg.lower() for keyword in ['callback', 'handler', 'listener', 'on_']):
                    callbacks.append({
                        'type': 'callback_param',
                        'name': arg.arg,
                        'line': node.lineno
                    })
        
        # Look for methods named on_*, handle_*, notify_*
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if any(item.name.startswith(prefix) for prefix in ['on_', 'handle_', 'notify_', 'trigger_']):
                        callbacks.append({
                            'type': 'event_method',
                            'name': item.name,
                            'line': item.lineno
                        })
        
        # Look for direct function calls in loops (polling pattern)
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if any(name in child.func.attr.lower() for name in ['update', 'notify', 'trigger', 'fire']):
                        callbacks.append({
                            'type': 'notification_call',
                            'name': child.func.attr,
                            'line': child.lineno
                        })
        
        return callbacks
    
    def _generate_observer_example(self, context_name: str) -> str:
        """Generate example Observer pattern refactor."""
        return f"""
# Before: Tight coupling with callbacks
class {context_name}:
    def __init__(self, callback1, callback2, callback3):
        self.callback1 = callback1
        self.callback2 = callback2
        self.callback3 = callback3
    
    def do_something(self):
        result = self._process()
        # Notify all callbacks
        self.callback1(result)
        self.callback2(result)
        self.callback3(result)

# After: Observer Pattern
from abc import ABC, abstractmethod
from typing import List

class Observer(ABC):
    @abstractmethod
    def update(self, data):
        pass

class Subject:
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer):
        self._observers.remove(observer)
    
    def notify(self, data):
        for observer in self._observers:
            observer.update(data)

class {context_name}(Subject):
    def do_something(self):
        result = self._process()
        self.notify(result)  # All observers get notified

# Concrete Observers
class Logger(Observer):
    def update(self, data):
        print(f"Logging: {{data}}")

class MetricsCollector(Observer):
    def update(self, data):
        # collect metrics

class Alerter(Observer):
    def update(self, data):
        # send alerts

# Usage
subject = {context_name}()
subject.attach(Logger())
subject.attach(MetricsCollector())
subject.attach(Alerter())
subject.do_something()  # All observers notified automatically
"""


class DecoratorPatternDetector:
    """Detect opportunities for Decorator pattern (repetitive wrapper logic)."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find wrapper patterns that could use Decorator pattern."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Look for repeated pre/post processing logic
                wrapper_patterns = self._find_wrapper_patterns(node)
                
                if wrapper_patterns['has_pre_post_logic']:
                    suggestions.append({
                        "pattern": "Decorator",
                        "severity": "low",
                        "location": f"line {node.lineno}",
                        "file": file_path,
                        "function": node.name,
                        "description": "Function has pre/post processing logic (logging, validation, caching, etc.)",
                        "current_code_smell": "Cross-cutting concerns mixed with business logic",
                        "recommended_pattern": "Decorator Pattern (Python decorators)",
                        "rationale": (
                            "Extract pre/post processing into reusable decorators. "
                            "Keeps core logic clean and focused."
                        ),
                        "example_refactor": self._generate_decorator_example(node.name),
                        "benefits": [
                            "Separation of concerns: Core logic separated from cross-cutting concerns",
                            "Reusability: Decorators can be applied to multiple functions",
                            "Composability: Stack multiple decorators as needed"
                        ]
                    })
        
        return suggestions
    
    def _find_wrapper_patterns(self, func_node: ast.FunctionDef) -> Dict:
        """Detect pre/post processing patterns."""
        has_logging = False
        has_timing = False
        has_validation = False
        has_caching = False
        has_error_handling = False
        
        # Check function body for common patterns
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr.lower()
                    if any(word in func_name for word in ['log', 'debug', 'info', 'warn', 'error']):
                        has_logging = True
                    if any(word in func_name for word in ['time', 'perf', 'measure']):
                        has_timing = True
                    if any(word in func_name for word in ['validate', 'check', 'verify']):
                        has_validation = True
                    if any(word in func_name for word in ['cache', 'memoize']):
                        has_caching = True
            
            if isinstance(node, ast.Try):
                has_error_handling = True
        
        concern_count = sum([has_logging, has_timing, has_validation, has_caching, has_error_handling])
        
        return {
            'has_pre_post_logic': concern_count >= 2,
            'concerns': [c for c, present in [
                ('logging', has_logging),
                ('timing', has_timing),
                ('validation', has_validation),
                ('caching', has_caching),
                ('error_handling', has_error_handling)
            ] if present]
        }
    
    def _generate_decorator_example(self, function_name: str) -> str:
        """Generate example Decorator pattern refactor."""
        return f"""
# Before: Cross-cutting concerns mixed in
def {function_name}(arg1, arg2):
    # Logging
    logger.info(f"Called {function_name} with {{arg1}}, {{arg2}}")
    
    # Validation
    if not validate_args(arg1, arg2):
        raise ValueError("Invalid arguments")
    
    # Timing
    start = time.time()
    
    # Core business logic
    result = do_actual_work(arg1, arg2)
    
    # More timing
    elapsed = time.time() - start
    logger.info(f"{function_name} took {{elapsed}}s")
    
    return result

# After: Decorator Pattern
import functools
import time
from typing import Callable

def log_calls(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Called {{func.__name__}} with {{args}}, {{kwargs}}")
        result = func(*args, **kwargs)
        return result
    return wrapper

def validate_args(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not all(args):
            raise ValueError("Invalid arguments")
        return func(*args, **kwargs)
    return wrapper

def measure_time(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{{func.__name__}} took {{elapsed:.3f}}s")
        return result
    return wrapper

# Clean, focused business logic
@log_calls
@validate_args
@measure_time
def {function_name}(arg1, arg2):
    return do_actual_work(arg1, arg2)
"""


class TemplateMethodPatternDetector:
    """Detect opportunities for Template Method pattern (similar algorithms with variations)."""
    
    def detect(self, code: str, file_path: str = "unknown.py") -> List[Dict]:
        """Find similar methods that could use Template Method pattern."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        suggestions = []
        
        # Look for classes with similar method names
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                similar_groups = self._find_similar_methods(methods)
                
                for group in similar_groups:
                    if len(group) >= 2:
                        suggestions.append({
                            "pattern": "Template Method",
                            "severity": "low",
                            "location": f"line {node.lineno}",
                            "file": file_path,
                            "class_name": node.name,
                            "description": f"Similar methods: {', '.join(m.name for m in group)}",
                            "current_code_smell": "Duplicated algorithm structure with minor variations",
                            "recommended_pattern": "Template Method Pattern",
                            "rationale": (
                                "Define skeleton of algorithm in base class. "
                                "Let subclasses override specific steps."
                            ),
                            "example_refactor": self._generate_template_example(node.name),
                            "benefits": [
                                "Code reuse: Common algorithm structure defined once",
                                "Flexibility: Subclasses customize only what differs",
                                "Maintainability: Changes to algorithm structure in one place"
                            ]
                        })
        
        return suggestions
    
    def _find_similar_methods(self, methods: List[ast.FunctionDef]) -> List[List[ast.FunctionDef]]:
        """Group methods with similar names."""
        groups = []
        used = set()
        
        for i, method1 in enumerate(methods):
            if i in used:
                continue
            
            group = [method1]
            name1_base = self._extract_base_name(method1.name)
            
            for j, method2 in enumerate(methods[i+1:], i+1):
                if j in used:
                    continue
                
                name2_base = self._extract_base_name(method2.name)
                
                # Check if names are similar
                if name1_base and name1_base == name2_base:
                    group.append(method2)
                    used.add(j)
            
            if len(group) >= 2:
                groups.append(group)
                used.add(i)
        
        return groups
    
    def _extract_base_name(self, method_name: str) -> Optional[str]:
        """Extract base name without suffix (e.g., 'process_xml' -> 'process')."""
        # Common patterns: process_json, process_xml, handle_get, handle_post
        parts = method_name.split('_')
        if len(parts) >= 2:
            return '_'.join(parts[:-1])
        return None
    
    def _generate_template_example(self, class_name: str) -> str:
        """Generate example Template Method pattern refactor."""
        return f"""
# Before: Duplicated algorithm structure
class {class_name}:
    def process_json(self, data):
        # Step 1: Parse
        parsed = json.loads(data)
        # Step 2: Validate
        self.validate(parsed)
        # Step 3: Transform (JSON-specific)
        result = self.transform_json(parsed)
        # Step 4: Save
        self.save(result)
        return result
    
    def process_xml(self, data):
        # Step 1: Parse
        parsed = ET.fromstring(data)
        # Step 2: Validate
        self.validate(parsed)
        # Step 3: Transform (XML-specific)
        result = self.transform_xml(parsed)
        # Step 4: Save
        self.save(result)
        return result

# After: Template Method Pattern
from abc import ABC, abstractmethod

class DataProcessor(ABC):
    def process(self, data):  # Template method
        # Step 1
        parsed = self.parse(data)
        # Step 2
        self.validate(parsed)
        # Step 3 (customizable)
        result = self.transform(parsed)
        # Step 4
        self.save(result)
        return result
    
    @abstractmethod
    def parse(self, data):
        pass
    
    @abstractmethod
    def transform(self, parsed_data):
        pass
    
    def validate(self, data):  # Common implementation
        # shared validation logic
        pass
    
    def save(self, result):  # Common implementation
        # shared save logic
        pass

class JsonProcessor(DataProcessor):
    def parse(self, data):
        return json.loads(data)
    
    def transform(self, parsed_data):
        return self.transform_json(parsed_data)

class XmlProcessor(DataProcessor):
    def parse(self, data):
        return ET.fromstring(data)
    
    def transform(self, parsed_data):
        return self.transform_xml(parsed_data)
"""


class PatternSuggester:
    """Unified design pattern suggestion engine."""
    
    def __init__(self):
        self.strategy_detector = StrategyPatternDetector()
        self.factory_detector = FactoryPatternDetector()
        self.observer_detector = ObserverPatternDetector()
        self.decorator_detector = DecoratorPatternDetector()
        self.template_detector = TemplateMethodPatternDetector()
    
    def suggest_patterns(self, code: str, file_path: str = "unknown.py") -> Dict:
        """Analyze code and suggest applicable design patterns."""
        suggestions = []
        
        # Run all detectors
        suggestions.extend(self.strategy_detector.detect(code, file_path))
        suggestions.extend(self.factory_detector.detect(code, file_path))
        suggestions.extend(self.observer_detector.detect(code, file_path))
        suggestions.extend(self.decorator_detector.detect(code, file_path))
        suggestions.extend(self.template_detector.detect(code, file_path))
        
        return {
            "file": file_path,
            "total_suggestions": len(suggestions),
            "patterns_suggested": list(set(s['pattern'] for s in suggestions)),
            "suggestions_by_pattern": self._group_by_pattern(suggestions),
            "suggestions_by_severity": self._group_by_severity(suggestions),
            "detailed_suggestions": suggestions
        }
    
    def _group_by_pattern(self, suggestions: List[Dict]) -> Dict:
        """Group suggestions by pattern type."""
        grouped = {}
        for suggestion in suggestions:
            pattern = suggestion['pattern']
            if pattern not in grouped:
                grouped[pattern] = []
            grouped[pattern].append(suggestion)
        return grouped
    
    def _group_by_severity(self, suggestions: List[Dict]) -> Dict:
        """Group suggestions by severity."""
        grouped = {"high": [], "medium": [], "low": []}
        for suggestion in suggestions:
            severity = suggestion.get("severity", "low")
            grouped[severity].append(suggestion)
        return grouped
