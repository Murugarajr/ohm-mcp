"""
Automated Refactoring Executor - Apply refactorings with safety checks and rollback.
"""

import os
import shutil
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BackupManager:
    """Manage file backups for safe rollback."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.backup_dir = os.path.join(project_root, ".ohm-refactor-backups")
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Create backup directory if it doesn't exist."""
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, file_path: str, operation_id: str) -> str:
        """
        Create a backup of a file before refactoring.
        
        Args:
            file_path: Path to file to backup
            operation_id: Unique ID for this refactoring operation
        
        Returns:
            Path to backup file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relative_path = os.path.relpath(file_path, self.project_root)
        backup_name = f"{operation_id}_{timestamp}_{relative_path.replace(os.sep, '_')}"
        backup_path = os.path.join(self.backup_dir, backup_name)

        # Copy file
        shutil.copy2(file_path, backup_path)

        return backup_path

    def restore_backup(self, backup_path: str, original_path: str) -> bool:
        """
        Restore a file from backup.
        
        Args:
            backup_path: Path to backup file
            original_path: Original file path to restore to
        
        Returns:
            True if restored successfully
        """
        if not os.path.exists(backup_path):
            return False

        shutil.copy2(backup_path, original_path)
        return True

    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        backups = []

        if not os.path.exists(self.backup_dir):
            return backups

        for filename in os.listdir(self.backup_dir):
            filepath = os.path.join(self.backup_dir, filename)
            stat = os.stat(filepath)

            backups.append({
                "filename": filename,
                "path": filepath,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })

        return sorted(backups, key=lambda x: x['created'], reverse=True)

    def cleanup_old_backups(self, keep_days: int = 7):
        """Remove backups older than specified days."""
        if not os.path.exists(self.backup_dir):
            return

        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)

        for filename in os.listdir(self.backup_dir):
            filepath = os.path.join(self.backup_dir, filename)
            if os.path.getctime(filepath) < cutoff_time:
                os.remove(filepath)


class TestRunner:
    """Run tests to validate refactoring."""

    def __init__(self, project_root: str):
        self.project_root = project_root

    def detect_test_framework(self) -> str:
        """Detect which test framework is used."""
        # Check for pytest
        if os.path.exists(os.path.join(self.project_root, "pytest.ini")) or \
           os.path.exists(os.path.join(self.project_root, "setup.cfg")):
            return "pytest"

        # Check for unittest
        if any(f.startswith("test_") for f in os.listdir(self.project_root) if f.endswith(".py")):
            return "pytest"  # Default to pytest for simplicity

        return "pytest"

    def run_tests(
        self,
        test_path: Optional[str] = None,
        timeout: int = 300
    ) -> Dict:
        """
        Run tests using detected framework.
        
        Args:
            test_path: Specific test file or directory (None = all tests)
            timeout: Maximum time in seconds
        
        Returns:
            {
              "success": bool,
              "tests_run": int,
              "failures": int,
              "errors": int,
              "output": str,
              "duration": float
            }
        """
        framework = self.detect_test_framework()

        if framework == "pytest":
            return self._run_pytest(test_path, timeout)
        else:
            return self._run_unittest(test_path, timeout)

    def _run_pytest(self, test_path: Optional[str], timeout: int) -> Dict:
        """Run pytest."""
        cmd = ["pytest", "-v", "--tb=short"]

        if test_path:
            cmd.append(test_path)

        try:
            start_time = datetime.now()

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

            duration = (datetime.now() - start_time).total_seconds()

            # Parse pytest output
            output = result.stdout + result.stderr

            # Simple parsing (could be enhanced)
            success = result.returncode == 0

            return {
                "success": success,
                "framework": "pytest",
                "exit_code": result.returncode,
                "output": output,
                "duration": duration
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "framework": "pytest",
                "error": f"Tests timed out after {timeout} seconds"
            }

        except FileNotFoundError:
            return {
                "success": False,
                "framework": "pytest",
                "error": "pytest not found. Install with: pip install pytest"
            }

    def _run_unittest(self, test_path: Optional[str], timeout: int) -> Dict:
        """Run unittest."""
        cmd = ["python", "-m", "unittest", "discover"]

        if test_path:
            cmd.extend(["-s", test_path])

        try:
            start_time = datetime.now()

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

            duration = (datetime.now() - start_time).total_seconds()
            output = result.stdout + result.stderr

            return {
                "success": result.returncode == 0,
                "framework": "unittest",
                "exit_code": result.returncode,
                "output": output,
                "duration": duration
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "framework": "unittest",
                "error": f"Tests timed out after {timeout} seconds"
            }


class OperationLogger:
    """Log refactoring operations for audit trail."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.log_file = os.path.join(project_root, ".ohm-refactor-history.json")

    def log_operation(
        self,
        operation_id: str,
        operation_type: str,
        files_affected: List[str],
        parameters: Dict,
        status: str,
        backup_paths: List[str],
        test_results: Optional[Dict] = None
    ):
        """Log a refactoring operation."""
        history = self._load_history()

        entry = {
            "operation_id": operation_id,
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,
            "files_affected": files_affected,
            "parameters": parameters,
            "status": status,
            "backup_paths": backup_paths,
            "test_results": test_results
        }

        history.append(entry)
        self._save_history(history)

    def _load_history(self) -> List[Dict]:
        """Load operation history."""
        if not os.path.exists(self.log_file):
            return []

        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def _save_history(self, history: List[Dict]):
        """Save operation history."""
        with open(self.log_file, 'w') as f:
            json.dump(history, f, indent=2)

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent operation history."""
        history = self._load_history()
        return history[-limit:]


class AutomatedRefactoringExecutor:
    """Execute refactorings automatically with safety checks."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.backup_manager = BackupManager(project_root)
        self.test_runner = TestRunner(project_root)
        self.logger = OperationLogger(project_root)

    def apply_refactoring(
        self,
        refactoring_type: str,
        file_path: str,
        parameters: Dict,
        dry_run: bool = True,
        run_tests: bool = True,
        auto_rollback: bool = True
    ) -> Dict:
        """
        Apply refactoring with automatic backup and testing.
        
        Args:
            refactoring_type: Type of refactoring (e.g., 'extract_method')
            file_path: File to refactor
            parameters: Refactoring parameters
            dry_run: If True, only show what would happen
            run_tests: If True, run tests after refactoring
            auto_rollback: If True, rollback on test failure
        
        Returns:
            {
              "success": bool,
              "operation_id": str,
              "changes_applied": bool,
              "backup_path": str,
              "test_results": dict,
              "message": str
            }
        """
        operation_id = f"{refactoring_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Validate file exists
        full_path = os.path.join(self.project_root, file_path)
        if not os.path.exists(full_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        # Read original code
        with open(full_path, 'r', encoding='utf-8') as f:
            original_code = f.read()

        # Execute refactoring
        refactored_code, refactor_result = self._execute_refactoring(
            refactoring_type,
            original_code,
            file_path,
            parameters
        )

        if not refactor_result.get("success"):
            return refactor_result

        # Dry run: show changes without applying
        if dry_run:
            from .patching import PatchGenerator
            patch_gen = PatchGenerator()
            patch = patch_gen.generate_patch(original_code, refactored_code, file_path)

            return {
                "success": True,
                "operation_id": operation_id,
                "dry_run": True,
                "changes_preview": patch,
                "refactored_code": refactored_code,
                "message": "Dry run completed. No changes applied.",
                "parameters": parameters
            }

        # Create backup
        backup_path = self.backup_manager.create_backup(full_path, operation_id)

        # Apply changes
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(refactored_code)

            changes_applied = True
        except Exception as e:
            return {
                "success": False,
                "operation_id": operation_id,
                "error": f"Failed to write changes: {str(e)}"
            }

        # Run tests if requested
        test_results = None
        if run_tests:
            test_results = self.test_runner.run_tests()

            # Rollback if tests fail
            if not test_results["success"] and auto_rollback:
                self.backup_manager.restore_backup(backup_path, full_path)

                self.logger.log_operation(
                    operation_id,
                    refactoring_type,
                    [file_path],
                    parameters,
                    "ROLLED_BACK",
                    [backup_path],
                    test_results
                )

                return {
                    "success": False,
                    "operation_id": operation_id,
                    "changes_applied": False,
                    "rolled_back": True,
                    "backup_path": backup_path,
                    "test_results": test_results,
                    "message": "Refactoring rolled back due to test failures",
                    "error": "Tests failed after refactoring"
                }

        # Log success
        self.logger.log_operation(
            operation_id,
            refactoring_type,
            [file_path],
            parameters,
            "SUCCESS",
            [backup_path],
            test_results
        )

        return {
            "success": True,
            "operation_id": operation_id,
            "changes_applied": True,
            "backup_path": backup_path,
            "test_results": test_results,
            "message": "Refactoring applied successfully",
            "refactored_code": refactored_code
        }

    def _execute_refactoring(
        self,
        refactoring_type: str,
        code: str,
        file_path: str,
        parameters: Dict
    ) -> Tuple[str, Dict]:
        """Execute the actual refactoring logic."""
        # Import refactoring modules
        from .ast_refactorer import ASTRefactorer
        from .import_refactorer import ImportRefactoringOrchestrator
        from .type_hint_analyzer import TypeHintAnalyzer

        try:
            if refactoring_type == "extract_method":
                refactorer = ASTRefactorer()
                result = refactorer.extract_method_by_lines(
                    code,
                    parameters["start_line"],
                    parameters["end_line"],
                    parameters["new_function_name"],
                    file_path
                )
                return result.get("refactored_code", code), result

            elif refactoring_type == "refactor_imports":
                refactorer = ImportRefactoringOrchestrator()
                result = refactorer.import_refactorer.refactor_single_file(
                    code,
                    file_path,
                    parameters["old_module"],
                    parameters["new_module"]
                )
                return result.get("refactored_code", code), result

            elif refactoring_type == "add_type_hints":
                # This would need implementation - placeholder
                return code, {
                    "success": False,
                    "error": "Type hint addition not yet implemented for auto-apply"
                }

            else:
                return code, {
                    "success": False,
                    "error": f"Unknown refactoring type: {refactoring_type}"
                }

        except Exception as e:
            return code, {
                "success": False,
                "error": f"Refactoring failed: {str(e)}"
            }

    def rollback_operation(self, operation_id: str) -> Dict:
        """
        Rollback a specific refactoring operation.
        
        Args:
            operation_id: ID of operation to rollback
        
        Returns:
            {
              "success": bool,
              "files_restored": list,
              "message": str
            }
        """
        # Find operation in history
        history = self.logger.get_history(limit=100)
        operation = None

        for entry in history:
            if entry["operation_id"] == operation_id:
                operation = entry
                break

        if not operation:
            return {
                "success": False,
                "error": f"Operation not found: {operation_id}"
            }

        # Restore from backups
        files_restored = []

        for i, file_path in enumerate(operation["files_affected"]):
            backup_path = operation["backup_paths"][i]
            full_path = os.path.join(self.project_root, file_path)

            if self.backup_manager.restore_backup(backup_path, full_path):
                files_restored.append(file_path)

        # Log rollback
        self.logger.log_operation(
            f"ROLLBACK_{operation_id}",
            "rollback",
            operation["files_affected"],
            {"original_operation": operation_id},
            "SUCCESS",
            operation["backup_paths"]
        )

        return {
            "success": True,
            "operation_id": operation_id,
            "files_restored": files_restored,
            "message": f"Successfully rolled back operation {operation_id}"
        }

    def get_operation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent refactoring operations."""
        return self.logger.get_history(limit)

    def cleanup_backups(self, keep_days: int = 7):
        """Clean up old backup files."""
        self.backup_manager.cleanup_old_backups(keep_days)
