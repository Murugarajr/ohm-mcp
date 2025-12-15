"""
Metrics Dashboard/Report Generation - Generate comprehensive code quality reports.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class MetricsCollector:
    """Collect various code quality metrics."""
    
    def collect_all_metrics(
        self,
        project_root: str,
        file_paths: List[str],
        skip_heavy_analysis: bool = False
    ) -> Dict:
        """
        Collect all available metrics.
        
        Args:
            project_root: Project root directory
            file_paths: Python files to analyze
            skip_heavy_analysis: Skip time-consuming analyses
        
        Returns:
            Comprehensive metrics dictionary
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "project_root": project_root,
            "files_analyzed": len(file_paths),
            "total_lines": 0,
            "metrics": {}
        }
        
        # Collect basic file metrics
        total_lines = 0
        for file_path in file_paths[:100]:  # Limit to prevent timeout
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    total_lines += lines
            except:
                continue
        
        metrics["total_lines"] = total_lines
        
        # Import analyzers only when needed
        try:
            from .dead_code_detector import DeadCodeDetector
            dead_code_analyzer = DeadCodeDetector()
            metrics["metrics"]["dead_code"] = self._collect_dead_code_metrics(
                dead_code_analyzer, file_paths[:50]  # Limit files
            )
        except Exception as e:
            metrics["metrics"]["dead_code"] = {"error": str(e)}
        
        try:
            from .type_hint_analyzer import TypeHintAnalyzer
            type_analyzer = TypeHintAnalyzer()
            metrics["metrics"]["type_coverage"] = self._collect_type_coverage_metrics(
                type_analyzer, file_paths[:50]
            )
        except Exception as e:
            metrics["metrics"]["type_coverage"] = {"error": str(e)}
        
        if not skip_heavy_analysis:
            try:
                from .performance_analyzer import PerformanceAnalyzer
                perf_analyzer = PerformanceAnalyzer()
                metrics["metrics"]["performance"] = self._collect_performance_metrics(
                    perf_analyzer, file_paths[:30]
                )
            except Exception as e:
                metrics["metrics"]["performance"] = {"error": str(e)}
        
        # Calculate aggregate scores
        metrics["health_score"] = self._calculate_health_score(metrics["metrics"])
        metrics["technical_debt_score"] = self._calculate_technical_debt(metrics["metrics"])
        
        return metrics
    
    def _collect_dead_code_metrics(self, analyzer, file_paths: List[str]) -> Dict:
        """Collect dead code metrics."""
        unused_imports = 0
        unused_variables = 0
        unused_functions = 0
        unreachable_code = 0
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                result = analyzer.detect_all(code, file_path)
                summary = result.get("summary", {})
                
                unused_imports += summary.get("unused_imports", 0)
                unused_variables += summary.get("unused_variables", 0)
                unused_functions += summary.get("unused_functions", 0)
                unreachable_code += summary.get("unreachable_code", 0)
            except:
                continue
        
        return {
            "unused_imports": unused_imports,
            "unused_variables": unused_variables,
            "unused_functions": unused_functions,
            "unreachable_code": unreachable_code,
            "total": unused_imports + unused_variables + unused_functions + unreachable_code
        }
    
    def _collect_type_coverage_metrics(self, analyzer, file_paths: List[str]) -> Dict:
        """Collect type hint coverage metrics."""
        total_functions = 0
        typed_functions = 0
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                result = analyzer.coverage_analyzer.analyze(code, file_path)
                if "error" not in result:
                    total_functions += result.get("total_functions", 0)
                    typed_functions += result.get("typed_functions", 0)
            except:
                continue
        
        coverage_percent = (typed_functions / total_functions * 100) if total_functions > 0 else 0
        
        return {
            "total_functions": total_functions,
            "typed_functions": typed_functions,
            "coverage_percent": round(coverage_percent, 2)
        }
    
    def _collect_performance_metrics(self, analyzer, file_paths: List[str]) -> Dict:
        """Collect performance metrics."""
        nested_loops = 0
        mutable_defaults = 0
        performance_issues = 0
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                result = analyzer.analyze_performance(code, file_path)
                by_type = result.get("issues_by_type", {})
                
                nested_loops += len(by_type.get("nested_loops", []))
                mutable_defaults += len(by_type.get("mutable_default_argument", []))
                performance_issues += result.get("total_issues", 0)
            except:
                continue
        
        return {
            "nested_loops": nested_loops,
            "mutable_defaults": mutable_defaults,
            "total_issues": performance_issues
        }
    
    def _calculate_health_score(self, metrics: Dict) -> float:
        """Calculate overall code health score (0-100)."""
        scores = []
        
        # Type coverage score
        if "type_coverage" in metrics and "error" not in metrics["type_coverage"]:
            scores.append(metrics["type_coverage"].get("coverage_percent", 0))
        
        # Dead code score (inverse)
        if "dead_code" in metrics and "error" not in metrics["dead_code"]:
            total_dead = metrics["dead_code"].get("total", 0)
            dead_score = max(0, 100 - (total_dead * 5))
            scores.append(dead_score)
        
        # Performance score
        if "performance" in metrics and "error" not in metrics["performance"]:
            perf_issues = metrics["performance"].get("total_issues", 0)
            perf_score = max(0, 100 - (perf_issues * 5))
            scores.append(perf_score)
        
        return round(sum(scores) / len(scores) if scores else 50, 2)
    
    def _calculate_technical_debt(self, metrics: Dict) -> float:
        """Calculate technical debt score."""
        debt_points = 0
        
        if "dead_code" in metrics and "error" not in metrics["dead_code"]:
            debt_points += metrics["dead_code"].get("total", 0) * 2
        
        if "performance" in metrics and "error" not in metrics["performance"]:
            debt_points += metrics["performance"].get("total_issues", 0) * 3
        
        return debt_points


class HTMLReportGenerator:
    """Generate HTML dashboard reports."""
    
    def generate_html_report(self, metrics: Dict, output_path: str) -> str:
        """Generate HTML report from metrics."""
        html = self._generate_html(metrics)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def _generate_html(self, metrics: Dict) -> str:
        """Generate HTML content."""
        health_score = metrics.get("health_score", 0)
        health_color = self._get_health_color(health_score)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Quality Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            border-radius: 12px 12px 0 0;
        }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .timestamp {{ font-size: 0.9em; opacity: 0.8; margin-top: 10px; }}
        .summary {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; padding: 30px; }}
        .card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .score-circle {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: conic-gradient({health_color} {health_score}%, #e0e0e0 0);
            margin: 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .score-inner {{
            width: 120px;
            height: 120px;
            background: white;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .score-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: {health_color};
        }}
        .metric-section {{
            margin: 30px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .metric-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-number {{
            display: block;
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            display: block;
            font-size: 0.9em;
            color: #666;
            margin-top: 10px;
        }}
        footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
            border-radius: 0 0 12px 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Code Quality Dashboard</h1>
            <p class="timestamp">Generated: {metrics.get('timestamp', 'N/A')}</p>
        </header>
        
        <div class="summary">
            <div class="card">
                <h2>Health Score</h2>
                <div class="score-circle">
                    <div class="score-inner">
                        <span class="score-value">{health_score}</span>
                        <span>/100</span>
                    </div>
                </div>
                <p style="text-align: center;">{self._get_health_label(health_score)}</p>
            </div>
            
            <div class="card">
                <h3>📁 Overview</h3>
                <p><strong>Files:</strong> {metrics.get('files_analyzed', 0)}</p>
                <p><strong>Lines:</strong> {metrics.get('total_lines', 0):,}</p>
                <p><strong>Tech Debt:</strong> {metrics.get('technical_debt_score', 0)} points</p>
            </div>
        </div>
        
        {self._generate_metrics_sections(metrics.get('metrics', {}))}
        
        <footer>
            <p>Generated by OHM MCP Refactor</p>
        </footer>
    </div>
</body>
</html>"""
        return html
    
    def _generate_metrics_sections(self, metrics: Dict) -> str:
        """Generate metrics sections."""
        sections = []
        
        if "type_coverage" in metrics and "error" not in metrics["type_coverage"]:
            tc = metrics["type_coverage"]
            sections.append(f"""
        <div class="metric-section">
            <h2>📊 Type Coverage</h2>
            <div class="metric-grid">
                <div class="metric-item">
                    <span class="metric-number">{tc.get('coverage_percent', 0)}%</span>
                    <span class="metric-label">Coverage</span>
                </div>
                <div class="metric-item">
                    <span class="metric-number">{tc.get('typed_functions', 0)}/{tc.get('total_functions', 0)}</span>
                    <span class="metric-label">Typed Functions</span>
                </div>
            </div>
        </div>""")
        
        if "dead_code" in metrics and "error" not in metrics["dead_code"]:
            dc = metrics["dead_code"]
            sections.append(f"""
        <div class="metric-section">
            <h2>🗑️ Dead Code</h2>
            <div class="metric-grid">
                <div class="metric-item">
                    <span class="metric-number">{dc.get('unused_imports', 0)}</span>
                    <span class="metric-label">Unused Imports</span>
                </div>
                <div class="metric-item">
                    <span class="metric-number">{dc.get('unused_variables', 0)}</span>
                    <span class="metric-label">Unused Variables</span>
                </div>
                <div class="metric-item">
                    <span class="metric-number">{dc.get('unused_functions', 0)}</span>
                    <span class="metric-label">Unused Functions</span>
                </div>
            </div>
        </div>""")
        
        if "performance" in metrics and "error" not in metrics["performance"]:
            perf = metrics["performance"]
            sections.append(f"""
        <div class="metric-section">
            <h2>⚡ Performance</h2>
            <div class="metric-grid">
                <div class="metric-item">
                    <span class="metric-number">{perf.get('nested_loops', 0)}</span>
                    <span class="metric-label">Nested Loops</span>
                </div>
                <div class="metric-item">
                    <span class="metric-number">{perf.get('total_issues', 0)}</span>
                    <span class="metric-label">Total Issues</span>
                </div>
            </div>
        </div>""")
        
        return '\n'.join(sections)
    
    def _get_health_color(self, score: float) -> str:
        if score >= 80:
            return "#4caf50"
        elif score >= 60:
            return "#ff9800"
        else:
            return "#f44336"
    
    def _get_health_label(self, score: float) -> str:
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Improvement"


class MarkdownReportGenerator:
    """Generate Markdown reports."""
    
    def generate_markdown_report(self, metrics: Dict, output_path: str) -> str:
        md = f"""# 🔍 Code Quality Report

**Generated:** {metrics.get('timestamp', 'N/A')}

## Health Score: {metrics.get('health_score', 0)}/100

## Overview
- Files: {metrics.get('files_analyzed', 0)}
- Lines: {metrics.get('total_lines', 0):,}
- Tech Debt: {metrics.get('technical_debt_score', 0)} points

"""
        
        m = metrics.get('metrics', {})
        
        if "type_coverage" in m and "error" not in m["type_coverage"]:
            tc = m["type_coverage"]
            md += f"""## Type Coverage
- Coverage: {tc.get('coverage_percent', 0)}%
- Typed: {tc.get('typed_functions', 0)}/{tc.get('total_functions', 0)}

"""
        
        if "dead_code" in m and "error" not in m["dead_code"]:
            dc = m["dead_code"]
            md += f"""## Dead Code
- Unused Imports: {dc.get('unused_imports', 0)}
- Unused Variables: {dc.get('unused_variables', 0)}
- Unused Functions: {dc.get('unused_functions', 0)}

"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)
        
        return output_path


class MetricsReporter:
    """Unified metrics reporting orchestrator."""
    
    def __init__(self):
        self.collector = MetricsCollector()
        self.html_generator = HTMLReportGenerator()
        self.markdown_generator = MarkdownReportGenerator()
    
    def generate_report(
        self,
        project_root: str,
        file_paths: List[str],
        output_format: str = "html",
        output_path: Optional[str] = None
    ) -> Dict:
        """Generate code quality report."""
        # Collect metrics (with limits to prevent timeout)
        metrics = self.collector.collect_all_metrics(
            project_root,
            file_paths[:100],  # Limit files
            skip_heavy_analysis=(len(file_paths) > 50)
        )
        
        # Generate output path
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(project_root, "code-quality-reports")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"report_{timestamp}")
        
        # Generate reports
        report_files = {}
        
        if output_format in ["html", "all"]:
            html_path = f"{output_path}.html"
            self.html_generator.generate_html_report(metrics, html_path)
            report_files["html"] = html_path
        
        if output_format in ["markdown", "all"]:
            md_path = f"{output_path}.md"
            self.markdown_generator.generate_markdown_report(metrics, md_path)
            report_files["markdown"] = md_path
        
        if output_format in ["json", "all"]:
            json_path = f"{output_path}.json"
            with open(json_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            report_files["json"] = json_path
        
        return {
            "success": True,
            "metrics": metrics,
            "report_files": report_files,
            "message": f"Report generated: {', '.join(report_files.values())}"
        }
