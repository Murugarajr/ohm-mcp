"""
Symbol Renamer - Safely rename variables, functions, and classes across the project.
"""

import ast
import os
from typing import Dict, List, Optional


class SymbolRenamer:
    """Rename symbols (variables, functions, classes) across a codebase."""
    
    def __init__(self):
        self.references = []
    
    def rename_symbol(
        self,
        project_root: str,
        old_name: str,
        new_name: str,
        symbol_type: str,
        scope: str = "project",
        file_path: Optional[str] = None,
        start_line: Optional[int] = None
    ) -> Dict:
        """
        Rename a symbol across the project or specific scope.
        
        Args:
            project_root: Root directory of the project
            old_name: Current symbol name
            new_name: New symbol name
            symbol_type: 'variable', 'function', 'class', 'method', 'attribute'
            scope: 'project', 'file', 'function', 'class'
            file_path: Specific file (for file/function/class scope)
            start_line: Line number (for function/class scope)
        
        Returns:
            {
              "success": bool,
              "files_changed": int,
              "occurrences": int,
              "changes": [
                {
                  "file": str,
                  "line": int,
                  "old_code": str,
                  "new_code": str
                }
              ],
              "refactored_files": {
                "file_path": "new_content"
              }
            }
        """
        # Validate symbol names
        if not self._is_valid_identifier(new_name):
            return {
                "success": False,
                "error": f"Invalid identifier: {new_name}"
            }
        
        # Find all files to process
        if scope == "project":
            files_to_process = self._find_python_files(project_root)
        elif scope == "file" and file_path:
            files_to_process = [os.path.join(project_root, file_path)]
        else:
            return {
                "success": False,
                "error": f"Invalid scope or missing file_path: {scope}"
            }
        
        # Find all occurrences
        all_occurrences = self._find_all_occurrences(
            files_to_process,
            old_name,
            symbol_type,
            scope,
            file_path,
            start_line
        )
        
        # Perform renaming
        refactored_files = {}
        changes = []
        
        for file_path, occurrences in all_occurrences.items():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Rename in reverse order to preserve line numbers
            new_lines = lines.copy()
            
            for occurrence in sorted(occurrences, key=lambda x: x['line'], reverse=True):
                line_idx = occurrence['line'] - 1
                
                if line_idx < len(new_lines):
                    old_line = new_lines[line_idx]
                    new_line = self._replace_symbol_in_line(
                        old_line,
                        old_name,
                        new_name,
                        occurrence['column']
                    )
                    
                    new_lines[line_idx] = new_line
                    
                    changes.append({
                        "file": file_path,
                        "line": occurrence['line'],
                        "old_code": old_line.strip(),
                        "new_code": new_line.strip(),
                        "context": occurrence['context']
                    })
            
            refactored_files[file_path] = '\n'.join(new_lines)
        
        return {
            "success": True,
            "files_changed": len(refactored_files),
            "occurrences": len(changes),
            "changes": changes,
            "refactored_files": refactored_files,
            "summary": f"Renamed '{old_name}' to '{new_name}' in {len(changes)} location(s) across {len(refactored_files)} file(s)"
        }
    
    def _find_all_occurrences(
        self,
        files: List[str],
        symbol_name: str,
        symbol_type: str,
        scope: str,
        target_file: Optional[str],
        target_line: Optional[int]
    ) -> Dict[str, List[Dict]]:
        """Find all occurrences of a symbol."""
        occurrences = {}
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                file_occurrences = self._find_occurrences_in_file(
                    code,
                    file_path,
                    symbol_name,
                    symbol_type,
                    scope,
                    target_file,
                    target_line
                )
                
                if file_occurrences:
                    occurrences[file_path] = file_occurrences
            
            except Exception:
                continue
        
        return occurrences
    
    def _find_occurrences_in_file(
        self,
        code: str,
        file_path: str,
        symbol_name: str,
        symbol_type: str,
        scope: str,
        target_file: Optional[str],
        target_line: Optional[int]
    ) -> List[Dict]:
        """Find occurrences of a symbol in a file."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        occurrences = []
        
        if symbol_type == "class":
            occurrences.extend(self._find_class_occurrences(tree, symbol_name, scope, target_line))
        elif symbol_type == "function":
            occurrences.extend(self._find_function_occurrences(tree, symbol_name, scope, target_line))
        elif symbol_type == "method":
            occurrences.extend(self._find_method_occurrences(tree, symbol_name, scope, target_line))
        elif symbol_type == "variable":
            occurrences.extend(self._find_variable_occurrences(tree, symbol_name, scope, target_line))
        elif symbol_type == "attribute":
            occurrences.extend(self._find_attribute_occurrences(tree, symbol_name))
        else:
            # Find all types
            occurrences.extend(self._find_all_name_occurrences(tree, symbol_name))
        
        return occurrences
    
    def _find_class_occurrences(
        self,
        tree: ast.AST,
        class_name: str,
        scope: str,
        target_line: Optional[int]
    ) -> List[Dict]:
        """Find all occurrences of a class name."""
        occurrences = []
        
        for node in ast.walk(tree):
            # Class definition
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                if not target_line or node.lineno == target_line:
                    occurrences.append({
                        "line": node.lineno,
                        "column": node.col_offset,
                        "context": "class_definition"
                    })
            
            # Class usage (instantiation, inheritance)
            elif isinstance(node, ast.Name) and node.id == class_name:
                occurrences.append({
                    "line": node.lineno,
                    "column": node.col_offset,
                    "context": "class_usage"
                })
        
        return occurrences
    
    def _find_function_occurrences(
        self,
        tree: ast.AST,
        func_name: str,
        scope: str,
        target_line: Optional[int]
    ) -> List[Dict]:
        """Find all occurrences of a function name."""
        occurrences = []
        
        for node in ast.walk(tree):
            # Function definition
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                if not target_line or node.lineno == target_line:
                    occurrences.append({
                        "line": node.lineno,
                        "column": node.col_offset,
                        "context": "function_definition"
                    })
            
            # Function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    occurrences.append({
                        "line": node.func.lineno,
                        "column": node.func.col_offset,
                        "context": "function_call"
                    })
        
        return occurrences
    
    def _find_method_occurrences(
        self,
        tree: ast.AST,
        method_name: str,
        scope: str,
        target_line: Optional[int]
    ) -> List[Dict]:
        """Find all occurrences of a method name."""
        occurrences = []
        
        for node in ast.walk(tree):
            # Method definition
            if isinstance(node, ast.FunctionDef) and node.name == method_name:
                # Check if it's inside a class
                parent_class = self._find_parent_class(tree, node)
                if parent_class:
                    if not target_line or node.lineno == target_line:
                        occurrences.append({
                            "line": node.lineno,
                            "column": node.col_offset,
                            "context": f"method_definition in {parent_class.name}"
                        })
            
            # Method calls (obj.method())
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == method_name:
                    occurrences.append({
                        "line": node.func.lineno,
                        "column": node.func.col_offset,
                        "context": "method_call"
                    })
        
        return occurrences
    
    def _find_variable_occurrences(
        self,
        tree: ast.AST,
        var_name: str,
        scope: str,
        target_line: Optional[int]
    ) -> List[Dict]:
        """Find all occurrences of a variable name."""
        occurrences = []
        
        # If scope is function or class, find only within that scope
        if scope in ["function", "class"] and target_line:
            scope_node = self._find_scope_node(tree, target_line)
            if scope_node:
                tree = scope_node
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == var_name:
                # Determine context
                if isinstance(node.ctx, ast.Store):
                    context = "variable_assignment"
                elif isinstance(node.ctx, ast.Load):
                    context = "variable_usage"
                else:
                    context = "variable_reference"
                
                occurrences.append({
                    "line": node.lineno,
                    "column": node.col_offset,
                    "context": context
                })
        
        return occurrences
    
    def _find_attribute_occurrences(self, tree: ast.AST, attr_name: str) -> List[Dict]:
        """Find all occurrences of an attribute name."""
        occurrences = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == attr_name:
                occurrences.append({
                    "line": node.lineno,
                    "column": node.col_offset,
                    "context": "attribute_access"
                })
        
        return occurrences
    
    def _find_all_name_occurrences(self, tree: ast.AST, name: str) -> List[Dict]:
        """Find all occurrences of a name (fallback for any type)."""
        occurrences = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == name:
                occurrences.append({
                    "line": node.lineno,
                    "column": node.col_offset,
                    "context": "name_usage"
                })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                occurrences.append({
                    "line": node.lineno,
                    "column": node.col_offset,
                    "context": "function_definition"
                })
            elif isinstance(node, ast.ClassDef) and node.name == name:
                occurrences.append({
                    "line": node.lineno,
                    "column": node.col_offset,
                    "context": "class_definition"
                })
        
        return occurrences
    
    def _find_parent_class(self, tree: ast.AST, target_node: ast.AST) -> Optional[ast.ClassDef]:
        """Find parent class of a node."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if target_node in ast.walk(node):
                    return node
        return None
    
    def _find_scope_node(self, tree: ast.AST, line: int) -> Optional[ast.AST]:
        """Find the scope node (function or class) at a specific line."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.lineno == line:
                    return node
        return None
    
    def _replace_symbol_in_line(
        self,
        line: str,
        old_name: str,
        new_name: str,
        column: int
    ) -> str:
        """Replace symbol at specific column, respecting word boundaries."""
        # Simple replacement with word boundary check
        import re
        
        # Create pattern that matches the symbol as a whole word
        pattern = r'\b' + re.escape(old_name) + r'\b'
        
        # Replace first occurrence at or after column
        parts = line.split(old_name)
        if len(parts) > 1:
            # Find the occurrence closest to the column
            current_pos = 0
            for i, part in enumerate(parts[:-1]):
                current_pos += len(part)
                if current_pos >= column or i == 0:
                    # Replace this occurrence
                    result = old_name.join(parts[:i+1]) + new_name + old_name.join(parts[i+1:])
                    return result
        
        # Fallback: simple replace first occurrence
        return line.replace(old_name, new_name, 1)
    
    def _is_valid_identifier(self, name: str) -> bool:
        """Check if name is a valid Python identifier."""
        return name.isidentifier() and not name.startswith('__')
    
    def _find_python_files(self, root_dir: str) -> List[str]:
        """Find all Python files in directory tree."""
        python_files = []
        
        for dirpath, _, filenames in os.walk(root_dir):
            # Skip common non-source directories
            if any(skip in dirpath for skip in ['.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules']):
                continue
            
            for filename in filenames:
                if filename.endswith('.py'):
                    python_files.append(os.path.join(dirpath, filename))
        
        return python_files


class SmartRenamer:
    """Smart renaming with conflict detection and suggestions."""
    
    def __init__(self):
        self.renamer = SymbolRenamer()
    
    def preview_rename(
        self,
        project_root: str,
        old_name: str,
        new_name: str,
        symbol_type: str,
        scope: str = "project",
        file_path: Optional[str] = None
    ) -> Dict:
        """
        Preview what will change without applying.
        
        Returns conflict warnings and impact analysis.
        """
        # Check for conflicts
        conflicts = self._check_conflicts(project_root, new_name, symbol_type)
        
        # Get rename result (without writing files)
        result = self.renamer.rename_symbol(
            project_root,
            old_name,
            new_name,
            symbol_type,
            scope,
            file_path
        )
        
        if not result.get("success"):
            return result
        
        # Add conflict warnings
        result["conflicts"] = conflicts
        result["has_conflicts"] = len(conflicts) > 0
        
        if conflicts:
            result["warning"] = (
                f"New name '{new_name}' conflicts with {len(conflicts)} existing symbol(s). "
                "Renaming may cause shadowing or ambiguity."
            )
        
        # Generate patches
        from .patch_generator import PatchGenerator
        patch_gen = PatchGenerator()
        
        patches = {}
        for file_path, new_content in result["refactored_files"].items():
            with open(file_path, 'r') as f:
                old_content = f.read()
            
            patch = patch_gen.generate_patch(old_content, new_content, file_path)
            patches[file_path] = patch
        
        result["patches"] = patches
        
        return result
    
    def _check_conflicts(
        self,
        project_root: str,
        new_name: str,
        symbol_type: str
    ) -> List[Dict]:
        """Check if new name conflicts with existing symbols."""
        conflicts = []
        
        python_files = self.renamer._find_python_files(project_root)
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                
                tree = ast.parse(code)
                
                # Check for existing symbols with the new name
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == new_name:
                        conflicts.append({
                            "file": file_path,
                            "line": node.lineno,
                            "type": "variable",
                            "message": f"Variable '{new_name}' already exists"
                        })
                    
                    elif isinstance(node, ast.FunctionDef) and node.name == new_name:
                        conflicts.append({
                            "file": file_path,
                            "line": node.lineno,
                            "type": "function",
                            "message": f"Function '{new_name}' already exists"
                        })
                    
                    elif isinstance(node, ast.ClassDef) and node.name == new_name:
                        conflicts.append({
                            "file": file_path,
                            "line": node.lineno,
                            "type": "class",
                            "message": f"Class '{new_name}' already exists"
                        })
            
            except Exception:
                continue
        
        return conflicts


class SymbolRenamingOrchestrator:
    """Unified symbol renaming orchestrator."""
    
    def __init__(self):
        self.renamer = SymbolRenamer()
        self.smart_renamer = SmartRenamer()
    
    def rename_symbol(
        self,
        project_root: str,
        old_name: str,
        new_name: str,
        symbol_type: str,
        scope: str = "project",
        file_path: Optional[str] = None,
        start_line: Optional[int] = None,
        preview_only: bool = True
    ) -> Dict:
        """
        Unified interface for renaming symbols.
        
        Args:
            preview_only: If True, only show what would change
        """
        if preview_only:
            return self.smart_renamer.preview_rename(
                project_root,
                old_name,
                new_name,
                symbol_type,
                scope,
                file_path
            )
        else:
            return self.renamer.rename_symbol(
                project_root,
                old_name,
                new_name,
                symbol_type,
                scope,
                file_path,
                start_line
            )
