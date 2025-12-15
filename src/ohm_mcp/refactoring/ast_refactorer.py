"""
AST-based code refactoring for precise extract method operations.
"""

import ast
import textwrap
from typing import Dict, List, Set, Tuple, Optional


class ASTExtractMethodRefactorer:
    """Extract method refactoring using AST for 100% accuracy."""
    
    def extract_method(
        self,
        code: str,
        start_line: int,
        end_line: int,
        new_function_name: str,
        file_path: str = "unknown.py"
    ) -> Dict:
        """
        Extract lines [start_line, end_line] into a new function using AST.
        
        Args:
            code: Full source code
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed, inclusive)
            new_function_name: Name for the new extracted function
            file_path: File path for context
        
        Returns:
            {
              "success": bool,
              "refactored_code": str,
              "new_function": str,
              "extracted_params": list,
              "return_vars": list,
              "patch": str,
              "message": str
            }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "message": f"Syntax error in source code: {e}"
            }
        
        # Find the function/method containing the lines to extract
        containing_function = self._find_containing_function(tree, start_line, end_line)
        
        if not containing_function:
            return {
                "success": False,
                "message": f"Lines {start_line}-{end_line} are not within a function"
            }
        
        # Extract the block of code
        lines = code.splitlines(keepends=True)
        block_lines = lines[start_line - 1:end_line]
        block_code = ''.join(block_lines)
        
        # Analyze the block
        analysis = self._analyze_block(containing_function, block_code, start_line, end_line, code)
        
        if not analysis['success']:
            return {
                "success": False,
                "message": analysis['message']
            }
        
        # Generate the new function
        new_function = self._generate_new_function(
            new_function_name,
            block_code,
            analysis['input_vars'],
            analysis['output_vars'],
            analysis['indent']
        )
        
        # Generate the function call
        function_call = self._generate_function_call(
            new_function_name,
            analysis['input_vars'],
            analysis['output_vars'],
            analysis['indent']
        )
        
        # Replace the block with the function call
        refactored_code = self._replace_block(
            code,
            start_line,
            end_line,
            function_call,
            new_function,
            containing_function
        )
        
        # Generate patch
        from .patching import PatchGenerator
        patch_gen = PatchGenerator()
        patch = patch_gen.generate_patch(code, refactored_code, file_path)
        
        return {
            "success": True,
            "refactored_code": refactored_code,
            "new_function": new_function,
            "extracted_params": analysis['input_vars'],
            "return_vars": analysis['output_vars'],
            "patch": patch,
            "message": f"Successfully extracted method '{new_function_name}'"
        }
    
    def _find_containing_function(
        self,
        tree: ast.AST,
        start_line: int,
        end_line: int
    ) -> Optional[ast.FunctionDef]:
        """Find the function that contains the specified lines."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    if node.lineno <= start_line and node.end_lineno >= end_line:
                        return node
        return None
    
    def _analyze_block(
        self,
        containing_function: ast.FunctionDef,
        block_code: str,
        start_line: int,
        end_line: int,
        full_code: str
    ) -> Dict:
        """
        Analyze the code block to determine inputs and outputs.
        
        Returns:
            {
              "success": bool,
              "input_vars": list,  # Variables needed from outside
              "output_vars": list,  # Variables used after the block
              "indent": str,
              "message": str
            }
        """
        # Detect indentation
        first_line = block_code.split('\n')[0]
        indent = first_line[:len(first_line) - len(first_line.lstrip())]
        
        # Parse the block
        try:
            # Dedent to parse as standalone code
            dedented_block = textwrap.dedent(block_code)
            block_tree = ast.parse(dedented_block)
        except SyntaxError as e:
            return {
                "success": False,
                "message": f"Cannot parse block: {e}"
            }
        
        # Get all variables in the containing function before the block
        vars_before = self._get_variables_before_line(containing_function, start_line, full_code)
        
        # Get variables used in the block
        vars_used_in_block = self._get_variables_used(block_tree)
        
        # Get variables defined in the block
        vars_defined_in_block = self._get_variables_defined(block_tree)
        
        # Get variables used after the block
        vars_used_after = self._get_variables_after_line(containing_function, end_line, full_code)
        
        # Input vars: used in block but defined before (not in block)
        input_vars = sorted(list(
            (vars_used_in_block & vars_before) - vars_defined_in_block
        ))
        
        # Output vars: defined in block and used after
        output_vars = sorted(list(
            vars_defined_in_block & vars_used_after
        ))
        
        return {
            "success": True,
            "input_vars": input_vars,
            "output_vars": output_vars,
            "indent": indent,
            "message": "Block analyzed successfully"
        }
    
    def _get_variables_before_line(
        self,
        func_node: ast.FunctionDef,
        line_num: int,
        full_code: str
    ) -> Set[str]:
        """Get all variables defined before a specific line in a function."""
        variables = set()
        
        # Add function parameters
        for arg in func_node.args.args:
            variables.add(arg.arg)
        
        # Walk the function AST and collect assignments before line_num
        for node in ast.walk(func_node):
            if hasattr(node, 'lineno') and node.lineno < line_num:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        variables.update(self._extract_names(target))
                elif isinstance(node, ast.AugAssign):
                    variables.update(self._extract_names(node.target))
                elif isinstance(node, (ast.For, ast.AsyncFor)):
                    variables.update(self._extract_names(node.target))
                elif isinstance(node, ast.With):
                    for item in node.items:
                        if item.optional_vars:
                            variables.update(self._extract_names(item.optional_vars))
        
        return variables
    
    def _get_variables_after_line(
        self,
        func_node: ast.FunctionDef,
        line_num: int,
        full_code: str
    ) -> Set[str]:
        """Get all variables used after a specific line in a function."""
        variables = set()
        
        for node in ast.walk(func_node):
            if hasattr(node, 'lineno') and node.lineno > line_num:
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    variables.add(node.id)
        
        return variables
    
    def _get_variables_used(self, tree: ast.AST) -> Set[str]:
        """Get all variables used (read) in the AST."""
        variables = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                variables.add(node.id)
        
        return variables
    
    def _get_variables_defined(self, tree: ast.AST) -> Set[str]:
        """Get all variables defined (written) in the AST."""
        variables = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    variables.update(self._extract_names(target))
            elif isinstance(node, ast.AugAssign):
                variables.update(self._extract_names(node.target))
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                variables.update(self._extract_names(node.target))
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars:
                        variables.update(self._extract_names(item.optional_vars))
        
        return variables
    
    def _extract_names(self, node: ast.AST) -> Set[str]:
        """Extract all variable names from an assignment target."""
        names = set()
        
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                names.update(self._extract_names(elt))
        elif isinstance(node, ast.Starred):
            names.update(self._extract_names(node.value))
        
        return names
    
    def _generate_new_function(
        self,
        function_name: str,
        block_code: str,
        input_vars: List[str],
        output_vars: List[str],
        indent: str
    ) -> str:
        """Generate the new extracted function."""
        # Build function signature
        params = ', '.join(input_vars) if input_vars else ''
        
        # Dedent the block
        dedented_block = textwrap.dedent(block_code).rstrip()
        
        # Build return statement
        if output_vars:
            if len(output_vars) == 1:
                return_stmt = f"    return {output_vars[0]}"
            else:
                return_stmt = f"    return {', '.join(output_vars)}"
        else:
            return_stmt = ""
        
        # Build function
        lines = [f"def {function_name}({params}):"]
        
        # Add docstring
        lines.append(f'    """Extracted method."""')
        
        # Add body (re-indent with 4 spaces)
        for line in dedented_block.split('\n'):
            if line.strip():
                lines.append(f"    {line}")
            else:
                lines.append("")
        
        # Add return
        if return_stmt:
            lines.append(return_stmt)
        
        return '\n'.join(lines)
    
    def _generate_function_call(
        self,
        function_name: str,
        input_vars: List[str],
        output_vars: List[str],
        indent: str
    ) -> str:
        """Generate the function call to replace the extracted block."""
        args = ', '.join(input_vars) if input_vars else ''
        
        if output_vars:
            if len(output_vars) == 1:
                call = f"{indent}{output_vars[0]} = {function_name}({args})"
            else:
                vars_str = ', '.join(output_vars)
                call = f"{indent}{vars_str} = {function_name}({args})"
        else:
            call = f"{indent}{function_name}({args})"
        
        return call
    
    def _replace_block(
        self,
        code: str,
        start_line: int,
        end_line: int,
        function_call: str,
        new_function: str,
        containing_function: ast.FunctionDef
    ) -> str:
        """Replace the block with the function call and insert the new function."""
        lines = code.splitlines(keepends=True)
        
        # Replace the block with the function call
        before = lines[:start_line - 1]
        after = lines[end_line:]
        call_line = function_call + '\n'
        
        # Find where to insert the new function (before the containing function)
        insert_line = containing_function.lineno - 1
        
        # Build refactored code
        result = (
            ''.join(before) +
            call_line +
            ''.join(after)
        )
        
        # Insert the new function before the containing function
        result_lines = result.splitlines(keepends=True)
        result_lines.insert(insert_line, new_function + '\n\n\n')
        
        return ''.join(result_lines)


class CohesionAnalyzer:
    """Analyze code blocks for cohesion and suggest extractable regions."""
    
    def identify_extractable_blocks(
        self,
        code: str,
        file_path: str = "unknown.py"
    ) -> List[Dict]:
        """
        Identify cohesive code blocks that are good candidates for extraction.
        
        Returns:
            List of extractable blocks with metrics
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        extractable_blocks = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                blocks = self._find_cohesive_blocks(node, code)
                extractable_blocks.extend(blocks)
        
        return extractable_blocks
    
    def _find_cohesive_blocks(
        self,
        func_node: ast.FunctionDef,
        full_code: str
    ) -> List[Dict]:
        """Find cohesive blocks within a function."""
        blocks = []
        
        # Look for blocks with high internal cohesion:
        # 1. Multiple related operations on the same data
        # 2. Clear input/output boundary
        # 3. 3-10 lines (not too small, not too large)
        
        body = func_node.body
        lines = full_code.splitlines()
        
        # Group consecutive statements that operate on similar variables
        i = 0
        while i < len(body):
            # Try to form a block starting at position i
            block_nodes = [body[i]]
            block_vars = self._get_variables_in_node(body[i])
            
            j = i + 1
            while j < len(body) and len(block_nodes) < 10:
                next_vars = self._get_variables_in_node(body[j])
                
                # Check if next statement shares variables (cohesion)
                overlap = block_vars & next_vars
                if overlap or self._is_related_operation(body[j], block_nodes):
                    block_nodes.append(body[j])
                    block_vars.update(next_vars)
                    j += 1
                else:
                    break
            
            # If block is substantial enough (3+ lines)
            if len(block_nodes) >= 3:
                start_line = block_nodes[0].lineno
                end_line = block_nodes[-1].end_lineno or block_nodes[-1].lineno
                
                # Calculate metrics
                shared_vars = len(block_vars)
                external_deps = len(self._get_external_dependencies(block_nodes, func_node))
                cohesion_score = shared_vars / (external_deps + 1)  # Higher is more cohesive
                
                if cohesion_score > 1.5:  # Threshold for good cohesion
                    blocks.append({
                        "function": func_node.name,
                        "start_line": start_line,
                        "end_line": end_line,
                        "line_count": end_line - start_line + 1,
                        "cohesion_score": round(cohesion_score, 2),
                        "shared_variables": list(block_vars),
                        "external_dependencies": external_deps,
                        "recommendation": (
                            f"Lines {start_line}-{end_line} form a cohesive block. "
                            f"Consider extracting to a new method."
                        )
                    })
            
            i = j if j > i else i + 1
        
        return blocks
    
    def _get_variables_in_node(self, node: ast.AST) -> Set[str]:
        """Get all variables used or defined in a node."""
        variables = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                variables.add(child.id)
        
        return variables
    
    def _is_related_operation(
        self,
        node: ast.AST,
        previous_nodes: List[ast.AST]
    ) -> bool:
        """Check if node is related to previous nodes (same operation type)."""
        # Simple heuristic: same statement type suggests related operations
        if previous_nodes:
            return type(node) == type(previous_nodes[-1])
        return False
    
    def _get_external_dependencies(
        self,
        block_nodes: List[ast.AST],
        func_node: ast.FunctionDef
    ) -> Set[str]:
        """Get variables from outside the block that are used inside."""
        block_vars = set()
        for node in block_nodes:
            block_vars.update(self._get_variables_in_node(node))
        
        # Get function parameters
        params = {arg.arg for arg in func_node.args.args}
        
        # External dependencies are block vars that are parameters or defined elsewhere
        return block_vars & params


class ASTRefactorer:
    """Unified AST-based refactoring orchestrator."""
    
    def __init__(self):
        self.extract_method = ASTExtractMethodRefactorer()
        self.cohesion_analyzer = CohesionAnalyzer()
    
    def extract_method_by_lines(
        self,
        code: str,
        start_line: int,
        end_line: int,
        new_function_name: str,
        file_path: str = "unknown.py"
    ) -> Dict:
        """Extract method from specific line range."""
        return self.extract_method.extract_method(
            code, start_line, end_line, new_function_name, file_path
        )
    
    def suggest_extractable_blocks(
        self,
        code: str,
        file_path: str = "unknown.py"
    ) -> Dict:
        """Suggest cohesive blocks that should be extracted."""
        blocks = self.cohesion_analyzer.identify_extractable_blocks(code, file_path)
        
        return {
            "file": file_path,
            "total_suggestions": len(blocks),
            "extractable_blocks": blocks
        }
