# pylint: disable=too-many-lines
"""
MCP Server for Code Refactoring and Reviews
Expert Software Architect + Senior Code Reviewer
"""

import asyncio
import os
import json
import logging
from typing import Any, List, Optional

from ohm_mcp.refactoring import (
    CodeAnalyzer,
    PatchGenerator,
    RefactorPlanner,
    FunctionExtractor,
    ArchitectureAnalyzer,
    PatternSuggester,
    ASTRefactorer,
    DeadCodeDetector,
    TypeHintAnalyzer,
    TestGenerator,
    CoverageAnalyzer,
    ImportRefactoringOrchestrator,
    DependencyInjectionRefactorer,
    PerformanceAnalyzer,
    AutomatedRefactoringExecutor,
    SymbolRenamingOrchestrator,
    DuplicationDetector,
    MetricsReporter
)

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("code-refactoring-assistant")

# Configure logging (NEVER use print() for stdio-based servers)
# For stdio transport, only log critical errors to avoid interfering with protocol
logging.getLogger().handlers.clear()

# Optional: Enable file logging if OHM_MCP_LOG_PATH is set
log_path = os.environ.get("OHM_MCP_LOG_PATH")
if log_path:
    # Write detailed logs to file when explicitly configured
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)  # Only log errors, not to stdout/stderr

# ============================================================================
# CORE ANALYSIS ENGINE
# ============================================================================

# ============================================================================
# MCP TOOLS
# ============================================================================

analyzer = CodeAnalyzer()
planner = RefactorPlanner()
patch_gen = PatchGenerator()
extractor = FunctionExtractor()
arch_analyzer = ArchitectureAnalyzer()
pattern_suggester = PatternSuggester()
ast_refactorer = ASTRefactorer()
dead_code_detector = DeadCodeDetector()
type_hint_analyzer = TypeHintAnalyzer()
test_generator = TestGenerator()
coverage_analyzer = CoverageAnalyzer()
import_refactorer = ImportRefactoringOrchestrator()
di_refactorer = DependencyInjectionRefactorer()
performance_analyzer = PerformanceAnalyzer()

# Use environment variable for project root, or fallback to a safe writable directory
# When run via npx, os.getcwd() often returns '/' which is read-only
cwd = os.getcwd()
if cwd == '/' or not os.access(cwd, os.W_OK):
    # Use /tmp as fallback for backup/log directories when no proper project root
    default_project_root = os.environ.get("OHM_MCP_PROJECT_ROOT", "/tmp/ohm-mcp-workspace")
    os.makedirs(default_project_root, exist_ok=True)
else:
    default_project_root = cwd

automated_executor = AutomatedRefactoringExecutor(default_project_root)
symbol_renamer = SymbolRenamingOrchestrator()
duplication_detector = DuplicationDetector(min_lines=6, similarity_threshold=0.9)
metrics_reporter = MetricsReporter()


@mcp.tool()
def analyze_codebase(
    code: str,
    file_path: str = "unknown.py",
    include_analysis: bool = True,
    include_plan: bool = True,
) -> str:
    """
    Comprehensive code analysis for refactoring opportunities.

    Args:
        code: The source code to analyze
        file_path: Path to the file for contex
        include_analysis: Include detailed issue analysis
        include_plan: Include refactoring plan

    Returns:
        JSON formatted analysis with issues and refactoring plan
    """
    try:
        logger.info("Analyzing %s", file_path)

        analysis = analyzer.analyze(code, file_path)
        result = {
            "file": file_path,
            "analysis": analysis if include_analysis else None,
            "issues_detected": analysis["detailed_issues"],
            "refactor_plan": planner.create_plan(analysis) if include_plan else None,
        }

        return json.dumps(result, indent=2)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Analysis error: %s", str(e))
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_refactor_patch(
    original_code: str, refactored_code: str, file_path: str = "code.py"
) -> str:
    """
    Generate unified diff patch for proposed refactoring.

    Args:
        original_code: Original source code
        refactored_code: Refactored version
        file_path: File path for patch contex

    Returns:
        Unified diff format patch
    """
    try:
        patch = patch_gen.generate_patch(
            original_code, refactored_code, file_path)
        return patch if patch else "No changes detected"

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Patch generation error: %s", str(e))
        return f"Error generating patch: {str(e)}"


@mcp.tool()
def explain_refactoring(issue_type: str, context: Optional[str] = "") -> str:
    """
    Explain refactoring patterns and reasoning.

    Args:
        issue_type: Type of refactoring (e.g., 'extract_method', 'simplify_conditional')
        context: Additional context about the code

    Returns:
        Detailed explanation of the refactoring approach
    """
    explanations = {
        "extract_method": """
Extract Method Refactoring:
- Identify cohesive code blocks (3-10 lines)
- Create new function with descriptive name
- Pass required data as parameters
- Replace original code with function call
- Benefits: Improves readability, enables reuse, reduces complexity
""".strip(),
        "long_function": """
Long Function Refactoring:
- Break into logical sub-functions
- Each function should do ONE thing
- Aim for <20 lines per function
- Use meaningful names that explain inten
- Maintain single level of abstraction
""".strip(),
        "code_duplication": """
Remove Duplication:
- Identify duplicate patterns (DRY principle)
- Extract to shared function or class
- Parameterize differences
- Consider template method or strategy pattern for complex cases
""".strip(),
        "high_complexity": """
Reduce Complexity:
- Decompose complex conditionals
- Use guard clauses (early returns)
- Replace nested conditions with polymorphism
- Extract condition logic to named functions
- Aim for cyclomatic complexity < 10
""".strip(),
    }

    explanation = explanations.get(
        issue_type,
        "General refactoring: Improve code clarity, maintainability, and testability incrementally",
    )

    if context:
        explanation += f"\n\nContext: {context}"

    return explanation


@mcp.tool()
def suggest_tests() -> str:
    """
    Suggest test cases for refactoring validation.

    Returns:
        Test strategy and example code
    """
    return (
        "Test Strategy:\n\n"
        "1. Characterization tests before refactoring.\n"
        "2. Run tests after each small change.\n"
        "3. Add new tests for extracted functions.\n"
        "4. Compare outputs and check coverage.\n\n"
        "Example pytest structure:\n\n"
        "def test_original_behavior():\n"
        "    result = original_function(input_data)\n"
        "    assert result == expected_output\n\n"
        "def test_refactored_behavior():\n"
        "    result = refactored_function(input_data)\n"
        "    assert result == expected_output"
    )


@mcp.tool()
def extract_function_code(file_content: str, function_name: str) -> dict:
    """Extract a single function's source code from a file."""
    return extractor.extract_function(file_content, function_name)


@mcp.tool()
def propose_function_refactor(
    function_code: str, function_name: str, file_path: str = "unknown.py"
) -> dict:
    """Propose refactor plan for a single function."""
    return planner.plan_function_refactor(function_code, function_name, file_path)


@mcp.tool()
def apply_function_refactor(
    original_file: str,
    function_name: str,
    old_function_code: str,
    new_function_code: str,
    file_path: str = "code.py",
) -> str:
    """Apply a single-function refactor patch."""
    return patch_gen.apply_function_patch(
        original_file, function_name, old_function_code, new_function_code, file_path
    )


@mcp.tool()
def suggest_design_patterns(code: str, file_path: str = "unknown.py") -> dict:
    """
    Analyze code and suggest applicable design patterns.

    Detects:
    - Strategy: Long if/elif chains
    - Factory: Repetitive object creation
    - Observer: Callback hell / tight coupling
    - Decorator: Cross-cutting concerns
    - Template Method: Similar algorithms with variations

    Args:
        code: Source code to analyze
        file_path: File path for contex

    Returns:
        JSON with pattern suggestions, examples, and refactoring guidance
    """
    return pattern_suggester.suggest_patterns(code, file_path)


@mcp.tool()
def analyze_architecture(
    code: Optional[str] = None,
    file_path: str = "unknown.py",
    project_root_param: Optional[str] = None,
    module_paths: Optional[List[Any]] = None,
) -> dict:
    """
    Analyze architecture-level issues: God Objects, Circular Dependencies, SOLID violations.

    Args:
        code: Single file code (for file-level analysis)
        file_path: Path to the file
        project_root_param: Root directory (for project-level analysis)
        module_paths: List of Python files to analyze (for project-level)

    Returns:
        JSON with god_objects, circular_deps, solid_violations, metrics
    """
    if code:
        # Single file analysis
        return arch_analyzer.analyze_file(code, file_path)
    if project_root_param and module_paths:
        # Project-wide analysis
        return arch_analyzer.analyze_project(project_root_param, module_paths)
    return {"error": "Provide either 'code' or 'project_root' + 'module_paths'"}


@mcp.tool()
def extract_method_ast(
    code: str,
    start_line: int,
    end_line: int,
    new_function_name: str,
    file_path: str = "unknown.py"
) -> dict:
    """
    Extract lines [start_line, end_line] into a new function using AST.

    Automatically detects:
    - Required parameters (variables from outside the block)
    - Return values (variables used after the block)
    - Proper indentation and scoping

    Args:
        code: Full source code
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed, inclusive)
        new_function_name: Name for the extracted function
        file_path: File path for contex

    Returns:
        {
          "success": bool,
          "refactored_code": str,
          "new_function": str,
          "extracted_params": list,
          "return_vars": list,
          "patch": str
        }
    """
    return ast_refactorer.extract_method_by_lines(
        code, start_line, end_line, new_function_name, file_path
    )


@mcp.tool()
def suggest_extractable_methods(code: str, file_path: str = "unknown.py") -> dict:
    """
    Identify cohesive code blocks that should be extracted into methods.

    Uses cohesion analysis to find blocks with:
    - High internal cohesion (related operations)
    - Clear input/output boundaries
    - Reasonable size (3-10 lines)

    Args:
        code: Source code to analyze
        file_path: File path for contex

    Returns:
        JSON with extractable blocks, cohesion scores, and line ranges
    """
    return ast_refactorer.suggest_extractable_blocks(code, file_path)


@mcp.tool()
def detect_dead_code(code: str, file_path: str = "unknown.py") -> dict:
    """
    Detect dead code, unused imports, variables, and functions.

    Finds:
    - Unused imports
    - Unused variables (assigned but never read)
    - Unreachable code (after return, raise, break, continue)
    - Unused functions (defined but never called)
    - Shadowed variables (inner scope hides outer scope)

    Args:
        code: Source code to analyze
        file_path: File path for contex

    Returns:
        JSON with dead code issues categorized by type and severity
    """
    return dead_code_detector.detect_all(code, file_path)


@mcp.tool()
def generate_type_stub(code: str, file_path: str = "unknown.py") -> dict:
    """
    Generate a .pyi type stub file for the given code.

    Creates a stub file with:
    - Function signatures with inferred types
    - Class structures
    - Proper imports from typing module

    Args:
        code: Source code to generate stub for
        file_path: File path for context (stub will be .pyi)

    Returns:
        {
          "stub_file": str,
          "stub_content": str,
          "message": str
        }
    """
    return type_hint_analyzer.stub_generator.generate_stub(code, file_path)


@mcp.tool()
def analyze_type_hints(code: str, file_path: str = "unknown.py") -> dict:
    """
    Analyze type hint coverage and suggest missing annotations.

    Provides:
    - Coverage percentage and grade
    - List of functions missing type hints
    - Suggested type annotations (inferred from usage)
    - Migration plan with priorities

    Args:
        code: Source code to analyze
        file_path: File path for contex

    Returns:
        JSON with coverage metrics, suggestions, and migration plan
    """
    try:
        result = type_hint_analyzer.analyze_full(code, file_path)
        return result
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Type hint analysis error: %s", str(e))
        return {
            "file": file_path,
            "success": False,
            "error": str(e),
            "message": "Error analyzing type hints. Check the log for details."
        }


@mcp.tool()
def generate_characterization_tests(
    code: str,
    file_path: str = "unknown.py"
) -> dict:
    """
    Auto-generate characterization tests to capture current behavior.

    Generates pytest tests with:
    - Happy path test cases
    - Edge cases (empty inputs, None, zero, negative, etc.)
    - Test structure ready to run with pytes

    Use these tests BEFORE refactoring to ensure behavior is preserved.

    Args:
        code: Source code to generate tests for
        file_path: File path for contex

    Returns:
        {
          "test_file": str,
          "test_content": str (ready to save and run),
          "functions_tested": int,
          "test_cases_generated": in
        }
    """
    return test_generator.generate_characterization_tests(code, file_path)


@mcp.tool()
def generate_test_for_function(
    code: str,
    function_name: str,
    file_path: str = "unknown.py"
) -> dict:
    """
    Generate characterization tests for a specific function.

    Args:
        code: Source code containing the function
        function_name: Name of the function to tes
        file_path: File path for contex

    Returns:
        {
          "function": str,
          "test_content": str (ready to run),
          "test_cases": list,
          "test_case_count": in
        }
    """
    return test_generator.generate_test_for_specific_function(code, function_name, file_path)


@mcp.tool()
def prioritize_by_coverage(
    code: str,
    file_path: str = "unknown.py",
    coverage_data_path: Optional[str] = None
) -> dict:
    """
    Prioritize refactoring based on test coverage and complexity.

    Calculates risk score for each function based on:
    - Cyclomatic complexity (higher = riskier)
    - Test coverage % (lower = riskier)
    - Lines of code (larger = riskier)

    Functions are categorized as high/medium/low risk.

    Args:
        code: Source code to analyze
        file_path: File path for context
        coverage_data_path: Path to .coverage or coverage.json file (optional)

    Returns:
        {
          "high_risk_functions": [...],
          "medium_risk_functions": [...],
          "low_risk_functions": [...],
          "recommendations": [...],
          "formatted_report": str (human-readable report)
        }
    """
    return coverage_analyzer.prioritize_refactoring(code, file_path, coverage_data_path)


@mcp.tool()
def refactor_imports(
    project_root_param: str,
    old_module: str,
    new_module: str,
    file_paths: Optional[List[str]] = None
) -> dict:
    """
    Safely refactor all imports when renaming/moving a module.

    Uses AST-based rewriting to handle:
    - Direct imports (import old_module)
    - From imports (from old_module import X)
    - Submodule imports (from old_module.sub import Y)
    - Import aliases (import old_module as alias)

    Args:
        project_root: Root directory of the project
        old_module: Old module path (e.g., 'myapp.old_name')
        new_module: New module path (e.g., 'myapp.new_name')
        file_paths: Optional list of specific files to process

    Returns:
        {
          "files_changed": int,
          "changes": [
            {
              "file": str,
              "old_imports": [...],
              "new_imports": [...],
              "refactored_code": str,
              "patch": str
            }
          ],
          "summary": str
        }
    """
    return import_refactorer.refactor_module_rename(
        project_root_param, old_module, new_module, file_paths
    )


@mcp.tool()
def refactor_single_file_imports(
    code: str,
    file_path: str,
    old_module: str,
    new_module: str
) -> dict:
    """
    Refactor imports in a single file.

    Args:
        code: Source code
        file_path: File path for context
        old_module: Old module path
        new_module: New module path

    Returns:
        {
          "changed": bool,
          "old_imports": [...],
          "new_imports": [...],
          "refactored_code": str
        }
    """
    return import_refactorer.import_refactorer.refactor_single_file(
        code, file_path, old_module, new_module
    )


@mcp.tool()
def analyze_wildcard_imports(code: str, file_path: str = "unknown.py") -> dict:
    """
    Find wildcard imports (from module import *) and suggest explicit replacements.

    Analyzes which names are actually used and suggests:
    from module import * → from module import name1, name2, name3

    Args:
        code: Source code to analyze
        file_path: File path for context

    Returns:
        {
          "wildcard_imports": [...],
          "suggestions": [
            {
              "old": "from module import *",
              "new": "from module import x, y, z",
              "used_names": [...]
            }
          ]
        }
    """
    return import_refactorer.analyze_wildcard_imports(code, file_path)


@mcp.tool()
def analyze_tight_coupling(code: str, file_path: str = "unknown.py") -> dict:
    """
    Detect tight coupling and suggest dependency injection.

    Identifies:
    - Global variable usage in functions
    - Hard-coded class instantiation
    - Singleton patterns
    - Static method dependencies

    Provides concrete DI refactoring examples for each issue.

    Args:
        code: Source code to analyze
        file_path: File path for context

    Returns:
        {
          "total_issues": int,
          "issues_by_type": {...},
          "detailed_issues": [
            {
              "type": str,
              "severity": str,
              "description": str,
              "problem": str,
              "recommendation": str,
              "refactor_example": str
            }
          ]
        }
    """
    return di_refactorer.analyze_coupling(code, file_path)


@mcp.tool()
def suggest_di_refactor(
    code: str,
    class_name: str,
    file_path: str = "unknown.py"
) -> dict:
    """
    Generate dependency injection refactor for a specific class.

    Analyzes class dependencies and generates:
    - Refactored class with constructor injection
    - List of identified dependencies
    - Before/after code comparison

    Args:
        code: Source code containing the class
        class_name: Name of the class to refactor
        file_path: File path for context

    Returns:
        {
          "dependencies_identified": [...],
          "current_code": str,
          "refactored_code": str (with DI),
          "changes": [...]
        }
    """
    return di_refactorer.suggest_di_for_class(code, class_name, file_path)


@mcp.tool()
def analyze_performance(code: str, file_path: str = "unknown.py") -> dict:
    """
    Identify performance hotspots and inefficient patterns.

    Detects:
    - Nested loops (O(n²) and worse complexity)
    - Quadratic list operations (membership tests in loops)
    - Repeated function calls (missing caching)
    - Loop-invariant code (should move outside loop)
    - Mutable default arguments (memory leaks)
    - Inefficient string concatenation
    - Unnecessary deep copies
    - Missing generator usage

    Provides optimization suggestions with before/after examples.

    Args:
        code: Source code to analyze
        file_path: File path for context

    Returns:
        {
          "total_issues": int,
          "issues_by_type": {...},
          "issues_by_severity": {"high": [...], "medium": [...], "low": [...]},
          "detailed_issues": [
            {
              "type": str,
              "severity": str,
              "description": str,
              "problem": str,
              "recommendation": str,
              "refactor_example": str
            }
          ],
          "summary": str
        }
    """
    return performance_analyzer.analyze_performance(code, file_path)


@mcp.tool()
def apply_refactoring(  # pylint: disable=too-many-arguments
    refactoring_type: str,
    file_path: str,
    parameters: dict,
    *,
    dry_run: bool = True,
    run_tests: bool = True,
    auto_rollback: bool = True
) -> dict:
    """
    Automatically apply refactoring with safety checks.

    Features:
    - Creates automatic backup before changes
    - Applies refactoring
    - Runs tests to validate changes
    - Automatically rolls back if tests fail
    - Logs all operations for audit trail

    Args:
        refactoring_type: Type of refactoring
            - 'extract_method': Extract code into new function
            - 'refactor_imports': Update import statements
        file_path: Relative path to file (from project root)
        parameters: Refactoring-specific parameters
            For extract_method: {start_line, end_line, new_function_name}
            For refactor_imports: {old_module, new_module}
        dry_run: If True, show changes without applying (default: True)
        run_tests: Run tests after applying (default: True)
        auto_rollback: Rollback if tests fail (default: True)

    Returns:
        {
          "success": bool,
          "operation_id": str,
          "changes_applied": bool,
          "backup_path": str,
          "test_results": {...},
          "message": str
        }

    Example:
        # Dry run (safe preview)
        apply_refactoring(
            "extract_method",
            "myapp/utils.py",
            {"start_line": 45, "end_line": 60, "new_function_name": "calculate_total"},
            dry_run=True
        )

        # Apply with tests
        apply_refactoring(
            "extract_method",
            "myapp/utils.py",
            {"start_line": 45, "end_line": 60, "new_function_name": "calculate_total"},
            dry_run=False,
            run_tests=True,
            auto_rollback=True
        )
    """
    return automated_executor.apply_refactoring(
        refactoring_type,
        file_path,
        parameters,
        dry_run,
        run_tests,
        auto_rollback
    )


@mcp.tool()
def rollback_refactoring(operation_id: str) -> dict:
    """
    Rollback a previously applied refactoring.

    Args:
        operation_id: ID of operation to rollback (from apply_refactoring result)

    Returns:
        {
          "success": bool,
          "files_restored": list,
          "message": str
        }
    """
    return automated_executor.rollback_operation(operation_id)


@mcp.tool()
def show_refactoring_history(limit: int = 10) -> dict:
    """
    Show history of refactoring operations.

    Args:
        limit: Maximum number of operations to show

    Returns:
        {
          "history": [
            {
              "operation_id": str,
              "timestamp": str,
              "operation_type": str,
              "files_affected": list,
              "status": str,
              "test_results": dict
            }
          ]
        }
    """
    history = automated_executor.get_operation_history(limit)
    return {"history": history, "total": len(history)}


@mcp.tool()
def cleanup_old_backups(keep_days: int = 7) -> dict:
    """
    Clean up old backup files.

    Args:
        keep_days: Keep backups from last N days

    Returns:
        {
          "success": bool,
          "message": str
        }
    """
    try:
        automated_executor.cleanup_backups(keep_days)
        return {
            "success": True,
            "message": f"Cleaned up backups older than {keep_days} days"
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def rename_symbol(  # pylint: disable=too-many-arguments
    project_root_path: str,
    old_name: str,
    new_name: str,
    symbol_type: str,
    scope: str = "project",
    *,
    file_path: Optional[str] = None,
    start_line: Optional[int] = None,
    preview_only: bool = True
) -> dict:
    """
    Safely rename variables, functions, classes, or methods across the project.

    Features:
    - AST-based analysis (100% accurate)
    - Respects scope and context
    - Detects naming conflicts
    - Shows all occurrences before applying
    - Generates unified diffs
    - Updates docstrings and comments

    Args:
        project_root: Root directory of the project
        old_name: Current symbol name
        new_name: New symbol name (must be valid Python identifier)
        symbol_type: Type of symbol to rename
            - 'variable': Local/global variables
            - 'function': Function names
            - 'class': Class names
            - 'method': Method names
            - 'attribute': Class attributes
        scope: Where to apply renaming
            - 'project': Entire project (default)
            - 'file': Single file only
            - 'function': Within specific function
            - 'class': Within specific class
        file_path: File path (required for 'file', 'function', 'class' scope)
        start_line: Line number (required for 'function', 'class' scope)
        preview_only: If True, show changes without applying (default: True)

    Returns:
        {
          "success": bool,
          "files_changed": int,
          "occurrences": int,
          "conflicts": [...],  # Existing symbols with new name
          "has_conflicts": bool,
          "changes": [
            {
              "file": str,
              "line": int,
              "old_code": str,
              "new_code": str,
              "context": str
            }
          ],
          "patches": {
            "file_path": "unified_diff"
          },
          "refactored_files": {
            "file_path": "new_content"
          }
        }

    Examples:
        # Preview rename variable in entire project
        rename_symbol(
            "/path/to/project",
            "old_var",
            "new_var",
            "variable",
            scope="project",
            preview_only=True
        )

        # Rename function in specific file
        rename_symbol(
            "/path/to/project",
            "process_data",
            "transform_data",
            "function",
            scope="file",
            file_path="myapp/utils.py",
            preview_only=True
        )

        # Rename class across project (apply changes)
        rename_symbol(
            "/path/to/project",
            "OldClass",
            "NewClass",
            "class",
            scope="project",
            preview_only=False
        )
    """
    return symbol_renamer.rename_symbol(
        project_root_path,
        old_name,
        new_name,
        symbol_type,
        scope,
        file_path,
        start_line,
        preview_only
    )


@mcp.tool()
def detect_code_duplicates(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    project_root_param: str,
    file_paths: Optional[List[str]] = None,
    min_lines: int = 6,
    similarity_threshold: float = 0.9,
    include_near_duplicates: bool = True,
    include_functions: bool = True
) -> dict:
    """
    Detect duplicate and similar code blocks (DRY violations).

    Uses both token-based and AST-based detection:
    - Exact duplicates: Identical code blocks
    - Near duplicates: Similar code (90%+ similarity)
    - Duplicate functions: Functions with same structure

    Args:
        project_root: Root directory of the project
        file_paths: Specific files to analyze (None = all Python files)
        min_lines: Minimum lines for a block to be considered (default: 6)
        similarity_threshold: Minimum similarity ratio 0.0-1.0 (default: 0.9)
        include_near_duplicates: Detect similar (not just exact) code
        include_functions: Detect duplicate functions via AST comparison

    Returns:
        {
          "total_duplicates": int,
          "exact_duplicates": [
            {
              "type": "exact_duplicate",
              "similarity": 1.0,
              "line_count": int,
              "occurrences": int,
              "locations": [
                {"file": str, "start_line": int, "end_line": int}
              ],
              "code_sample": str,
              "recommendation": str,
              "refactoring": {
                "strategy": str,
                "function_name": str,
                "refactor_example": str,
                "estimated_lines_saved": int
              }
            }
          ],
          "near_duplicates": [...],
          "duplicate_functions": [
            {
              "type": "duplicate_function",
              "similarity": float,
              "functions": [
                {"name": str, "file": str, "line": int}
              ],
              "recommendation": str
            }
          ],
          "summary": {
            "exact_duplicate_count": int,
            "near_duplicate_count": int,
            "duplicate_function_count": int,
            "total_duplicated_lines": int,
            "files_affected": int,
            "severity": "high|medium|low",
            "recommendation": str
          }
        }

    Example:
        # Detect in entire project
        detect_code_duplicates("/path/to/project")

        # Detect in specific files with custom threshold
        detect_code_duplicates(
            "/path/to/project",
            file_paths=["app/utils.py", "app/helpers.py"],
            min_lines=4,
            similarity_threshold=0.85
        )
    """
    # Find files if not specified
    if file_paths is None:
        file_paths = []
        for dirpath, _, filenames in os.walk(project_root_param):
            # Skip common non-source directories
            skip_dirs = ['.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules']
            if any(skip in dirpath for skip in skip_dirs):
                continue
            for filename in filenames:
                if filename.endswith('.py'):
                    file_paths.append(os.path.join(dirpath, filename))
    else:
        # Convert relative paths to absolute
        file_paths = [
            os.path.join(project_root_param, fp) if not os.path.isabs(fp) else fp
            for fp in file_paths
        ]

    # Update detector settings
    duplication_detector.min_lines = min_lines
    duplication_detector.similarity_threshold = similarity_threshold
    duplication_detector.token_detector.min_lines = min_lines

    return duplication_detector.detect_duplicates(
        project_root_param,
        file_paths,
        include_near_duplicates,
        include_functions
    )


@mcp.tool()
def generate_quality_report(
    project_root: str,
    output_format: str = "html"
) -> dict:
    """
    Generate code quality dashboard report.

    Fast, lightweight report generation.

    Args:
        project_root: Root directory of the project
        output_format: 'html', 'markdown', 'json', or 'all'

    Returns:
        Report paths and basic metrics
    """
    # Find Python files (limited to prevent timeout)
    file_paths = []
    for dirpath, _, filenames in os.walk(project_root):
        if any(skip in dirpath for skip in [
            '.git', '__pycache__', 'venv', '.venv', 'node_modules'
        ]):
            continue
        for filename in filenames:
            if filename.endswith('.py'):
                file_paths.append(os.path.join(dirpath, filename))
                if len(file_paths) >= 100:  # Limit to prevent timeout
                    break
        if len(file_paths) >= 100:
            break

    try:
        result = metrics_reporter.generate_report(
            project_root,
            file_paths,
            output_format
        )
        return result
    except Exception as e:  # pylint: disable=broad-exception-caught
        return {
            "success": False,
            "error": f"Report generation failed: {str(e)}"
        }


@mcp.resource("refactoring://guidelines")
def refactoring_guidelines() -> str:
    """Provide general refactoring guidelines and best practices."""
    return """
Refactoring Guidelines:

1. **Understand the Code**: Before refactoring, ensure you understand
   what the code does and its dependencies.

2. **Small, Incremental Changes**: Make small changes and test frequently
   to avoid introducing bugs.

3. **Preserve Behavior**: Refactoring should not change the external
   behavior of the code.

4. **Improve Readability**: Use meaningful names, reduce complexity, and
   follow coding standards.

5. **DRY Principle**: Eliminate duplication by extracting common code into
   reusable functions or classes.

6. **SOLID Principles**: Aim for Single Responsibility, Open/Closed, Liskov
   Substitution, Interface Segregation, and Dependency Inversion.

7. **Test Coverage**: Ensure adequate test coverage before and after
   refactoring.

8. **Version Control**: Commit frequently and use branches for complex
   refactorings.

9. **Performance**: Be aware of performance implications of changes.

10. **Documentation**: Update comments and documentation as needed.
"""


def main() -> None:
    # MCP server startup code
    logger.info("Starting Code Refactoring MCP Server (stdio)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
