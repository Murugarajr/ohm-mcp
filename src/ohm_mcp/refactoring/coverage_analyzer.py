"""
Test Coverage-Driven Refactor Prioritization - Prioritize refactoring based on test coverage.
"""

import ast
import json
import os
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path


class CoverageParser:
    """Parse coverage.py data files."""
    
    def parse_coverage_file(self, coverage_path: str) -> Dict:
        """
        Parse .coverage file or coverage.json.
        
        Args:
            coverage_path: Path to .coverage or .coverage.json file
        
        Returns:
            {
              "files": {
                "file_path": {
                  "executed_lines": [line_numbers],
                  "missing_lines": [line_numbers],
                  "coverage_percent": float
                }
              }
            }
        """
        if not os.path.exists(coverage_path):
            return {"error": f"Coverage file not found: {coverage_path}"}
        
        # Try JSON format first (coverage json output)
        if coverage_path.endswith('.json'):
            return self._parse_json_coverage(coverage_path)
        
        # Try to convert .coverage to JSON format
        try:
            import coverage
            cov = coverage.Coverage(data_file=coverage_path)
            cov.load()
            
            files_data = {}
            for filename in cov.get_data().measured_files():
                analysis = cov.analysis2(filename)
                executed = sorted(analysis[1])
                missing = sorted(analysis[3])
                total = len(executed) + len(missing)
                percent = (len(executed) / total * 100) if total > 0 else 0
                
                files_data[filename] = {
                    "executed_lines": executed,
                    "missing_lines": missing,
                    "total_lines": total,
                    "coverage_percent": round(percent, 2)
                }
            
            return {"files": files_data}
        
        except ImportError:
            return {
                "error": "coverage.py library not installed. Install with: pip install coverage"
            }
        except Exception as e:
            return {"error": f"Failed to parse coverage file: {str(e)}"}
    
    def _parse_json_coverage(self, json_path: str) -> Dict:
        """Parse coverage.json format."""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            files_data = {}
            
            # coverage.json format
            if 'files' in data:
                for filepath, file_data in data['files'].items():
                    executed = file_data.get('executed_lines', [])
                    missing = file_data.get('missing_lines', [])
                    
                    summary = file_data.get('summary', {})
                    percent = summary.get('percent_covered', 0)
                    
                    files_data[filepath] = {
                        "executed_lines": executed,
                        "missing_lines": missing,
                        "total_lines": summary.get('num_statements', 0),
                        "coverage_percent": round(percent, 2)
                    }
            
            return {"files": files_data}
        
        except Exception as e:
            return {"error": f"Failed to parse JSON coverage: {str(e)}"}
    
    def get_function_coverage(
        self,
        coverage_data: Dict,
        file_path: str,
        function_start: int,
        function_end: int
    ) -> Dict:
        """
        Get coverage for a specific function by line range.
        
        Returns:
            {
              "executed_lines": int,
              "total_lines": int,
              "coverage_percent": float,
              "missing_lines": [line_numbers]
            }
        """
        if "error" in coverage_data:
            return coverage_data
        
        file_data = coverage_data.get("files", {}).get(file_path)
        if not file_data:
            return {
                "executed_lines": 0,
                "total_lines": function_end - function_start + 1,
                "coverage_percent": 0.0,
                "missing_lines": list(range(function_start, function_end + 1)),
                "note": "No coverage data for this file"
            }
        
        # Filter to function range
        executed_in_func = [
            line for line in file_data["executed_lines"]
            if function_start <= line <= function_end
        ]
        
        missing_in_func = [
            line for line in file_data["missing_lines"]
            if function_start <= line <= function_end
        ]
        
        total = len(executed_in_func) + len(missing_in_func)
        percent = (len(executed_in_func) / total * 100) if total > 0 else 0
        
        return {
            "executed_lines": len(executed_in_func),
            "total_lines": total,
            "coverage_percent": round(percent, 2),
            "missing_lines": missing_in_func
        }


class ComplexityCoverageAnalyzer:
    """Combine complexity metrics with coverage data."""
    
    def __init__(self):
        self.coverage_parser = CoverageParser()
    
    def analyze_risk_factors(
        self,
        code: str,
        file_path: str,
        coverage_data_path: Optional[str] = None
    ) -> Dict:
        """
        Analyze refactoring risk based on complexity and coverage.
        
        Returns:
            {
              "high_risk_functions": [...],
              "medium_risk_functions": [...],
              "low_risk_functions": [...],
              "recommendations": [...]
            }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error": "Failed to parse code"}
        
        # Get coverage data
        coverage_data = {}
        if coverage_data_path and os.path.exists(coverage_data_path):
            coverage_data = self.coverage_parser.parse_coverage_file(coverage_data_path)
        
        # Analyze each function
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_analysis = self._analyze_function_risk(
                    node, code, file_path, coverage_data
                )
                functions.append(func_analysis)
        
        # Categorize by risk
        high_risk = [f for f in functions if f['risk_level'] == 'high']
        medium_risk = [f for f in functions if f['risk_level'] == 'medium']
        low_risk = [f for f in functions if f['risk_level'] == 'low']
        
        # Sort each category by risk score (descending)
        high_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        medium_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        low_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(high_risk, medium_risk)
        
        return {
            "file": file_path,
            "total_functions": len(functions),
            "high_risk_functions": high_risk,
            "medium_risk_functions": medium_risk,
            "low_risk_functions": low_risk,
            "recommendations": recommendations,
            "summary": {
                "high_risk_count": len(high_risk),
                "medium_risk_count": len(medium_risk),
                "low_risk_count": len(low_risk)
            }
        }
    
    def _analyze_function_risk(
        self,
        func_node: ast.FunctionDef,
        code: str,
        file_path: str,
        coverage_data: Dict
    ) -> Dict:
        """Analyze risk factors for a single function."""
        func_name = func_node.name
        start_line = func_node.lineno
        end_line = func_node.end_lineno or start_line
        
        # Calculate complexity
        complexity = self._calculate_complexity(func_node)
        
        # Get coverage
        if coverage_data and "files" in coverage_data:
            func_coverage = self.coverage_parser.get_function_coverage(
                coverage_data, file_path, start_line, end_line
            )
            coverage_percent = func_coverage.get("coverage_percent", 0)
        else:
            coverage_percent = 0
            func_coverage = {
                "coverage_percent": 0,
                "note": "No coverage data available"
            }
        
        # Calculate lines of code
        lines = code.splitlines()[start_line - 1:end_line]
        loc = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(complexity, coverage_percent, loc)
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        return {
            "function": func_name,
            "line": start_line,
            "end_line": end_line,
            "complexity": complexity,
            "coverage_percent": coverage_percent,
            "lines_of_code": loc,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": self._identify_risk_factors(complexity, coverage_percent, loc),
            "recommendation": self._get_recommendation(risk_level, complexity, coverage_percent)
        }
    
    def _calculate_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        complexity_keywords = [
            ast.If, ast.For, ast.While, ast.And, ast.Or,
            ast.ExceptHandler, ast.With
        ]
        
        for node in ast.walk(func_node):
            if any(isinstance(node, kw) for kw in complexity_keywords):
                complexity += 1
        
        return complexity
    
    def _calculate_risk_score(
        self,
        complexity: int,
        coverage_percent: float,
        loc: int
    ) -> float:
        """
        Calculate overall risk score (0-100, higher = more risky).
        
        Formula: 
        - High complexity increases risk
        - Low coverage increases risk
        - Large LOC increases risk
        """
        # Normalize metrics
        complexity_score = min(complexity / 15.0, 1.0) * 40  # Max 40 points
        coverage_score = (100 - coverage_percent) / 100.0 * 40  # Max 40 points (inverted)
        loc_score = min(loc / 100.0, 1.0) * 20  # Max 20 points
        
        risk_score = complexity_score + coverage_score + loc_score
        
        return round(risk_score, 2)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score."""
        if risk_score >= 70:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"
    
    def _identify_risk_factors(
        self,
        complexity: int,
        coverage_percent: float,
        loc: int
    ) -> List[str]:
        """Identify specific risk factors."""
        factors = []
        
        if complexity > 10:
            factors.append(f"High complexity ({complexity})")
        
        if coverage_percent < 50:
            factors.append(f"Low test coverage ({coverage_percent}%)")
        
        if coverage_percent == 0:
            factors.append("No test coverage")
        
        if loc > 50:
            factors.append(f"Large function ({loc} lines)")
        
        return factors
    
    def _get_recommendation(
        self,
        risk_level: str,
        complexity: int,
        coverage_percent: float
    ) -> str:
        """Get specific recommendation based on risk factors."""
        if risk_level == "high":
            if coverage_percent < 50:
                return (
                    "⚠️ HIGH RISK: Write comprehensive tests BEFORE refactoring. "
                    "Then break down complexity into smaller functions."
                )
            else:
                return (
                    "⚠️ HIGH RISK: High complexity detected. "
                    "Refactor into smaller, focused functions with existing test coverage."
                )
        
        elif risk_level == "medium":
            if coverage_percent < 70:
                return (
                    "⚡ MEDIUM RISK: Add more test coverage before refactoring. "
                    "Focus on edge cases and error paths."
                )
            else:
                return (
                    "⚡ MEDIUM RISK: Good test coverage. "
                    "Consider simplifying logic to reduce complexity."
                )
        
        else:
            return (
                "✅ LOW RISK: Well-tested and simple. "
                "Safe to refactor if needed."
            )
    
    def _generate_recommendations(
        self,
        high_risk: List[Dict],
        medium_risk: List[Dict]
    ) -> List[str]:
        """Generate overall recommendations."""
        recommendations = []
        
        if high_risk:
            recommendations.append(
                f"🔴 URGENT: {len(high_risk)} high-risk function(s) need immediate attention. "
                "Write tests first, then refactor."
            )
            
            # Top 3 high risk
            for func in high_risk[:3]:
                recommendations.append(
                    f"  • {func['function']}() - Risk score: {func['risk_score']} "
                    f"(complexity: {func['complexity']}, coverage: {func['coverage_percent']}%)"
                )
        
        if medium_risk:
            recommendations.append(
                f"🟡 {len(medium_risk)} medium-risk function(s). "
                "Improve test coverage before major refactoring."
            )
        
        if not high_risk and not medium_risk:
            recommendations.append(
                "✅ No high-risk functions detected. Codebase is in good shape!"
            )
        
        return recommendations


class CoverageReporter:
    """Generate coverage reports and prioritization lists."""
    
    def generate_refactor_priority_list(
        self,
        analysis_result: Dict
    ) -> str:
        """Generate a formatted priority list for refactoring."""
        lines = []
        
        lines.append("=" * 70)
        lines.append("REFACTOR PRIORITIZATION REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        lines.append(f"File: {analysis_result['file']}")
        lines.append(f"Total Functions: {analysis_result['total_functions']}")
        lines.append("")
        
        # Summary
        summary = analysis_result['summary']
        lines.append("RISK SUMMARY:")
        lines.append(f"  🔴 High Risk:   {summary['high_risk_count']}")
        lines.append(f"  🟡 Medium Risk: {summary['medium_risk_count']}")
        lines.append(f"  🟢 Low Risk:    {summary['low_risk_count']}")
        lines.append("")
        
        # Recommendations
        lines.append("RECOMMENDATIONS:")
        for rec in analysis_result['recommendations']:
            lines.append(f"  {rec}")
        lines.append("")
        
        # High risk details
        if analysis_result['high_risk_functions']:
            lines.append("HIGH RISK FUNCTIONS (Refactor immediately after adding tests):")
            lines.append("-" * 70)
            
            for func in analysis_result['high_risk_functions']:
                lines.append(f"  {func['function']}() - Line {func['line']}")
                lines.append(f"    Risk Score: {func['risk_score']}/100")
                lines.append(f"    Complexity: {func['complexity']}")
                lines.append(f"    Coverage:   {func['coverage_percent']}%")
                lines.append(f"    LOC:        {func['lines_of_code']}")
                lines.append(f"    Factors:    {', '.join(func['risk_factors'])}")
                lines.append(f"    Action:     {func['recommendation']}")
                lines.append("")
        
        # Medium risk summary
        if analysis_result['medium_risk_functions']:
            lines.append("MEDIUM RISK FUNCTIONS:")
            lines.append("-" * 70)
            
            for func in analysis_result['medium_risk_functions'][:5]:  # Top 5
                lines.append(
                    f"  {func['function']}() - "
                    f"Risk: {func['risk_score']}, "
                    f"Complexity: {func['complexity']}, "
                    f"Coverage: {func['coverage_percent']}%"
                )
            
            if len(analysis_result['medium_risk_functions']) > 5:
                lines.append(f"  ... and {len(analysis_result['medium_risk_functions']) - 5} more")
            lines.append("")
        
        lines.append("=" * 70)
        
        return '\n'.join(lines)


class CoverageAnalyzer:
    """Unified coverage-driven prioritization orchestrator."""
    
    def __init__(self):
        self.complexity_coverage = ComplexityCoverageAnalyzer()
        self.reporter = CoverageReporter()
    
    def prioritize_refactoring(
        self,
        code: str,
        file_path: str,
        coverage_data_path: Optional[str] = None
    ) -> Dict:
        """
        Prioritize refactoring based on complexity and coverage.
        
        Returns full analysis with risk levels and recommendations.
        """
        analysis = self.complexity_coverage.analyze_risk_factors(
            code, file_path, coverage_data_path
        )
        
        if "error" not in analysis:
            # Add formatted report
            analysis["formatted_report"] = self.reporter.generate_refactor_priority_list(analysis)
        
        return analysis
