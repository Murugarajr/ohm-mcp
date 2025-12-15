"""
Import Statement Refactorer - Safely update imports when moving/renaming modules.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ImportRefactorer:
    """Refactor import statements across a project."""
    
    def refactor_imports(
        self,
        project_root: str,
        old_module: str,
        new_module: str,
        file_paths: Optional[List[str]] = None
    ) -> Dict:
        """
        Refactor all imports from old_module to new_module.
        
        Args:
            project_root: Root directory of the project
            old_module: Old module path (e.g., 'myapp.old_module')
            new_module: New module path (e.g., 'myapp.new_module')
            file_paths: Specific files to process (if None, process all .py files)
        
        Returns:
            {
              "files_changed": int,
              "changes": [
                {
                  "file": str,
                  "old_imports": [...],
                  "new_imports": [...],
                  "refactored_code": str
                }
              ],
              "summary": str
            }
        """
        if not file_paths:
            file_paths = self._find_python_files(project_root)
        
        changes = []
        files_changed = 0
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                result = self._refactor_file_imports(
                    code, file_path, old_module, new_module
                )
                
                if result['changed']:
                    changes.append(result)
                    files_changed += 1
            
            except Exception as e:
                changes.append({
                    "file": file_path,
                    "error": str(e),
                    "changed": False
                })
        
        return {
            "files_changed": files_changed,
            "total_files_scanned": len(file_paths),
            "changes": changes,
            "summary": f"Updated imports in {files_changed} file(s)"
        }
    
    def refactor_single_file(
        self,
        code: str,
        file_path: str,
        old_module: str,
        new_module: str
    ) -> Dict:
        """Refactor imports in a single file."""
        return self._refactor_file_imports(code, file_path, old_module, new_module)
    
    def _refactor_file_imports(
        self,
        code: str,
        file_path: str,
        old_module: str,
        new_module: str
    ) -> Dict:
        """Refactor imports in a single file's code."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "file": file_path,
                "error": f"Syntax error: {e}",
                "changed": False
            }
        
        old_imports = []
        new_imports = []
        changed = False
        
        # Process imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if self._matches_module(alias.name, old_module):
                        old_import = self._format_import(node, alias)
                        old_imports.append(old_import)
                        
                        # Update the module name
                        new_name = self._replace_module_name(alias.name, old_module, new_module)
                        alias.name = new_name
                        
                        new_import = self._format_import(node, alias)
                        new_imports.append(new_import)
                        changed = True
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and self._matches_module(node.module, old_module):
                    old_import = self._format_import_from(node)
                    old_imports.append(old_import)
                    
                    # Update the module name
                    node.module = self._replace_module_name(node.module, old_module, new_module)
                    
                    new_import = self._format_import_from(node)
                    new_imports.append(new_import)
                    changed = True
        
        refactored_code = ast.unparse(tree) if changed else code
        
        return {
            "file": file_path,
            "changed": changed,
            "old_imports": old_imports,
            "new_imports": new_imports,
            "refactored_code": refactored_code
        }
    
    def _matches_module(self, import_name: str, target_module: str) -> bool:
        """Check if an import matches the target module."""
        # Exact match
        if import_name == target_module:
            return True
        
        # Submodule match (e.g., myapp.old matches myapp.old.utils)
        if import_name.startswith(target_module + '.'):
            return True
        
        return False
    
    def _replace_module_name(self, current_name: str, old_module: str, new_module: str) -> str:
        """Replace old module name with new module name."""
        if current_name == old_module:
            return new_module
        
        # Replace prefix for submodules
        if current_name.startswith(old_module + '.'):
            suffix = current_name[len(old_module):]
            return new_module + suffix
        
        return current_name
    
    def _format_import(self, node: ast.Import, alias: ast.alias) -> str:
        """Format import statement as string."""
        if alias.asname:
            return f"import {alias.name} as {alias.asname}"
        return f"import {alias.name}"
    
    def _format_import_from(self, node: ast.ImportFrom) -> str:
        """Format from...import statement as string."""
        module = node.module or ''
        level = '.' * node.level
        
        names = []
        for alias in node.names:
            if alias.name == '*':
                names.append('*')
            elif alias.asname:
                names.append(f"{alias.name} as {alias.asname}")
            else:
                names.append(alias.name)
        
        return f"from {level}{module} import {', '.join(names)}"
    
    def _find_python_files(self, root_dir: str) -> List[str]:
        """Find all Python files in a directory tree."""
        python_files = []
        
        for dirpath, _, filenames in os.walk(root_dir):
            # Skip common non-source directories
            if any(skip in dirpath for skip in ['.git', '__pycache__', 'venv', '.venv', 'env']):
                continue
            
            for filename in filenames:
                if filename.endswith('.py'):
                    python_files.append(os.path.join(dirpath, filename))
        
        return python_files


class RelativeImportHandler:
    """Handle relative imports when moving modules."""
    
    def adjust_relative_imports(
        self,
        code: str,
        file_path: str,
        old_package: str,
        new_package: str
    ) -> Dict:
        """
        Adjust relative imports when a file moves to a different package.
        
        Args:
            code: Source code
            file_path: Current file path
            old_package: Old package path (e.g., 'myapp.utils')
            new_package: New package path (e.g., 'myapp.helpers')
        
        Returns:
            {
              "refactored_code": str,
              "changes": [...]
            }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"error": f"Syntax error: {e}"}
        
        changes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level > 0:
                # Relative import detected
                old_import = self._format_relative_import(node)
                
                # Convert relative to absolute based on new package
                absolute_import = self._relative_to_absolute(
                    node, old_package, new_package
                )
                
                if absolute_import:
                    changes.append({
                        "old": old_import,
                        "new": absolute_import,
                        "line": node.lineno
                    })
        
        # For now, return original code with change suggestions
        # Full implementation would rewrite the imports
        return {
            "refactored_code": code,
            "changes": changes,
            "note": "Relative import adjustments detected"
        }
    
    def _format_relative_import(self, node: ast.ImportFrom) -> str:
        """Format relative import as string."""
        level = '.' * node.level
        module = node.module or ''
        names = [alias.name for alias in node.names]
        return f"from {level}{module} import {', '.join(names)}"
    
    def _relative_to_absolute(
        self,
        node: ast.ImportFrom,
        old_package: str,
        new_package: str
    ) -> Optional[str]:
        """Convert relative import to absolute import."""
        # Calculate the absolute module path
        new_package_parts = new_package.split('.')
        
        # Go up 'level' directories
        if node.level > len(new_package_parts):
            return None  # Can't go up that many levels
        
        base_parts = new_package_parts[:-node.level] if node.level > 0 else new_package_parts
        
        if node.module:
            absolute_module = '.'.join(base_parts + [node.module])
        else:
            absolute_module = '.'.join(base_parts)
        
        names = [alias.name for alias in node.names]
        return f"from {absolute_module} import {', '.join(names)}"


class WildcardImportReplacer:
    """Replace wildcard imports with explicit imports."""
    
    def replace_wildcard_imports(
        self,
        code: str,
        file_path: str
    ) -> Dict:
        """
        Replace 'from module import *' with explicit imports.
        
        Returns:
            {
              "wildcard_imports": [...],
              "suggestions": [...],
              "refactored_code": str
            }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"error": f"Syntax error: {e}"}
        
        wildcard_imports = []
        suggestions = []
        
        # Find all wildcard imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        wildcard_import = f"from {node.module} import *"
                        wildcard_imports.append({
                            "line": node.lineno,
                            "statement": wildcard_import,
                            "module": node.module
                        })
                        
                        # Find what names are actually used from this import
                        used_names = self._find_used_names(tree, node.module)
                        
                        if used_names:
                            explicit_import = f"from {node.module} import {', '.join(sorted(used_names))}"
                            suggestions.append({
                                "line": node.lineno,
                                "old": wildcard_import,
                                "new": explicit_import,
                                "used_names": list(used_names)
                            })
        
        return {
            "file": file_path,
            "wildcard_imports": wildcard_imports,
            "suggestions": suggestions,
            "refactored_code": code,  # Would need actual rewriting
            "recommendation": "Replace wildcard imports with explicit imports to improve clarity"
        }
    
    def _find_used_names(self, tree: ast.AST, module: str) -> Set[str]:
        """Find names that are used from a wildcard import."""
        # This is a simplified heuristic - in practice, would need
        # to actually import the module and check its __all__
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                # Heuristic: capitalized names are likely from imports
                if node.id[0].isupper() or '_' in node.id:
                    used_names.add(node.id)
        
        return used_names


class ImportRefactoringOrchestrator:
    """Unified import refactoring orchestrator."""
    
    def __init__(self):
        self.import_refactorer = ImportRefactorer()
        self.relative_handler = RelativeImportHandler()
        self.wildcard_replacer = WildcardImportReplacer()
    
    def refactor_module_rename(
        self,
        project_root: str,
        old_module: str,
        new_module: str,
        file_paths: Optional[List[str]] = None
    ) -> Dict:
        """
        Refactor all imports when renaming a module.
        
        Complete workflow:
        1. Update all imports across the project
        2. Generate patches for each file
        3. Provide summary and recommendations
        """
        result = self.import_refactorer.refactor_imports(
            project_root, old_module, new_module, file_paths
        )
        
        # Add patches
        from .patching import PatchGenerator
        patch_gen = PatchGenerator()
        
        for change in result['changes']:
            if change.get('changed'):
                try:
                    with open(change['file'], 'r') as f:
                        original = f.read()
                    
                    patch = patch_gen.generate_patch(
                        original,
                        change['refactored_code'],
                        change['file']
                    )
                    change['patch'] = patch
                except Exception:
                    pass
        
        return result
    
    def analyze_wildcard_imports(self, code: str, file_path: str) -> Dict:
        """Analyze and suggest replacements for wildcard imports."""
        return self.wildcard_replacer.replace_wildcard_imports(code, file_path)
