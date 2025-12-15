class CodeAnalyzer:
    """Analyzes code for refactoring opportunities and tech debt"""

    def __init__(self):
        self.smell_detectors = {
            'long_function': self._detect_long_functions,
            'code_duplication': self._detect_duplication,
            'complexity': self._detect_complexity,
            'anti_patterns': self._detect_anti_patterns
        }

    def analyze(self, code: str, file_path: str = "") -> dict:
        """Comprehensive code analysis"""
        issues = []

        for detector_name, detector_func in self.smell_detectors.items():
            detected = detector_func(code)
            if detected:
                issues.extend(detected)

        return {
            "total_issues": len(issues),
            "issues_by_severity": self._categorize_by_severity(issues),
            "detailed_issues": issues
        }

    def _detect_long_functions(self, code: str) -> list:
        """Detect functions exceeding length thresholds"""
        issues = []
        lines = code.split('\n')
        in_function = False
        function_start = 0
        function_name = ""

        for i, line in enumerate(lines, 1):
            if line.strip().startswith('def '):
                if in_function:
                    length = i - function_start
                    if length > 50:
                        issues.append({
                            "type": "long_function",
                            "severity": "high" if length > 100 else "medium",
                            "location": f"lines {function_start}-{i}",
                            "function": function_name,
                            "description": f"Function is {length} lines long",
                            "recommendation": "Consider breaking into smaller functions"
                        })
                in_function = True
                function_start = i
                function_name = line.split('def ')[1].split('(')[0]

        return issues

    def _detect_duplication(self, code: str) -> list:
        """Detect code duplication patterns"""
        # Simplified duplication detection
        issues = []
        lines = code.split('\n')
        seen_blocks = {}

        for i in range(len(lines) - 3):
            block = '\n'.join(lines[i:i+4])
            if block.strip() and not block.strip().startswith('#'):
                if block in seen_blocks:
                    issues.append({
                        "type": "code_duplication",
                        "severity": "medium",
                        "location": f"lines {i+1} and {seen_blocks[block]+1}",
                        "description": "Duplicate code block detected",
                        "recommendation": "Extract to a reusable function"
                    })
                else:
                    seen_blocks[block] = i

        return issues

    def _detect_complexity(self, code: str) -> list:
        """Detect high cyclomatic complexity"""
        issues = []
        complexity_keywords = ['if ', 'elif ', 'for ', 'while ', 'and ', 'or ', 'try', 'except']
        lines = code.split('\n')

        function_complexity = {}
        current_function = None

        for line in lines:
            if line.strip().startswith('def '):
                current_function = line.split('def ')[1].split('(')[0]
                function_complexity[current_function] = 1
            elif current_function:
                for keyword in complexity_keywords:
                    if keyword in line:
                        function_complexity[current_function] += 1

        for func, complexity in function_complexity.items():
            if complexity > 10:
                issues.append({
                    "type": "high_complexity",
                    "severity": "high" if complexity > 15 else "medium",
                    "function": func,
                    "complexity_score": complexity,
                    "description": f"Cyclomatic complexity: {complexity}",
                    "recommendation": "Simplify logic and extract sub-functions"
                })

        return issues

    def _detect_anti_patterns(self, code: str) -> list:
        """Detect common anti-patterns"""
        issues = []
        anti_patterns = {
            'bare_except': ('except:', 'Bare except clause catches all exceptions'),
            'mutable_default': ('def.*=\\[\\]', 'Mutable default argument'),
            'global_vars': ('global ', 'Global variable usage'),
            'star_import': ('from.*import \\*', 'Star import reduces readability')
        }

        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern_name, (pattern, description) in anti_patterns.items():
                if pattern in line:
                    issues.append({
                        "type": "anti_pattern",
                        "severity": "medium",
                        "location": f"line {i}",
                        "pattern": pattern_name,
                        "description": description,
                        "recommendation": "Refactor to follow best practices"
                    })

        return issues

    def _categorize_by_severity(self, issues: list) -> dict:
        """Group issues by severity"""
        categorized = {"high": [], "medium": [], "low": []}
        for issue in issues:
            severity = issue.get("severity", "low")
            categorized[severity].append(issue)
        return categorized


class FunctionExtractor:
    """Extract individual function definitions from Python source."""
    
    def extract_function(self, file_content: str, function_name: str) -> dict:
        """
        Extract source code for a single top-level function.
        
        Returns:
            {
              "function_name": str,
              "function_code": str,
              "start_line": int,
              "end_line": int
            }
            or {"error": str} if not found.
        """
        lines = file_content.splitlines(keepends=True)
        start = None
        indent = None

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith(f"def {function_name}("):
                start = i
                indent = len(line) - len(stripped)
                break

        if start is None:
            return {"error": f"Function '{function_name}' not found"}

        end = start + 1
        for j in range(start + 1, len(lines)):
            line = lines[j]
            if line.strip() == "" or line.lstrip().startswith("#"):
                end = j + 1
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent and line.lstrip().startswith(("def ", "class ", "@")):
                break
            end = j + 1

        fn_code = "".join(lines[start:end])
        return {
            "function_name": function_name,
            "function_code": fn_code,
            "start_line": start + 1,
            "end_line": end
        }



