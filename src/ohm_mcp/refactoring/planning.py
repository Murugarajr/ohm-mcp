class RefactorPlanner:
    """Creates incremental, safe refactoring plans"""

    def create_plan(self, analysis: dict) -> list:
        """Generate step-by-step refactoring plan"""
        plan = []
        issues = analysis.get("detailed_issues", [])

        # Prioritize by severity
        sorted_issues = sorted(issues, key=lambda x:
            {"high": 0, "medium": 1, "low": 2}.get(x.get("severity", "low"), 2))

        for i, issue in enumerate(sorted_issues, 1):
            step = {
                "step": i,
                "type": issue["type"],
                "severity": issue.get("severity", "low"),
                "location": issue.get("location", "unknown"),
                "action": self._generate_action(issue),
                "testing_strategy": self._suggest_tests(issue),
                "rollback_plan": "Git commit before change; revert if tests fail"
            }
            plan.append(step)

        return plan

    def _generate_action(self, issue: dict) -> str:
        """Generate specific refactoring action"""
        action_templates = {
            "long_function": f"Extract method from {issue.get('function', 'function')}",
            "code_duplication": "Extract duplicate code into shared function",
            "high_complexity": f"Simplify {issue.get('function', 'function')} logic",
            "anti_pattern": f"Refactor {issue.get('pattern', 'code')} pattern"
        }
        return action_templates.get(issue["type"], "Review and refactor")

    def _suggest_tests(self, issue: dict) -> str:
        """Suggest testing approach for refactoring"""
        return f"1. Add unit tests for current behavior\n2. Perform refactoring\n3. Verify all tests pass"
    
    def plan_function_refactor(self, function_code: str, function_name: str, file_path: str = "") -> dict:
        """
        Create a refactor plan for a single function.

        Returns:
            {
                "analysis": str,
                "issues_detected": [...],
                "refactor_plan": [...]
            }
        """
        from .analysis import CodeAnalyzer  # avoid circular import if needed
        analyzer = CodeAnalyzer()

        analysis = analyzer.analyze(function_code, file_path)
        issues = analysis.get("detailed_issues", [])
        plan = self.create_plan(analysis)

        reasoning = [
            f"Function '{function_name}' has {len(issues)} issue(s).",
            "Goal: reduce complexity, preserve behavior.",
            "Strategy: extract helpers, add early returns, simplify conditions."
        ]

        return {
            "analysis": "\n".join(reasoning),
            "issues_detected": issues,
            "refactor_plan": plan
        }
