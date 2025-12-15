"""
Code Duplication Detector - Find duplicate code blocks and suggest DRY refactoring.
"""

import ast
import hashlib
from typing import Dict, List, Set, Optional, Tuple
from difflib import SequenceMatcher
from collections import defaultdict


class CodeBlock:
    """Represents a block of code for comparison."""
    
    def __init__(self, lines: List[str], start_line: int, file_path: str, context: str = ""):
        self.lines = lines
        self.start_line = start_line
        self.end_line = start_line + len(lines) - 1
        self.file_path = file_path
        self.context = context
        self.content = '\n'.join(lines)
        self.normalized = self._normalize()
        self.hash = self._compute_hash()
    
    def _normalize(self) -> str:
        """Normalize code for comparison (remove whitespace, comments)."""
        normalized_lines = []
        
        for line in self.lines:
            # Remove leading/trailing whitespace
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Remove inline comments
            if '#' in stripped:
                stripped = stripped[:stripped.index('#')].strip()
            
            normalized_lines.append(stripped)
        
        return '\n'.join(normalized_lines)
    
    def _compute_hash(self) -> str:
        """Compute hash of normalized code."""
        return hashlib.md5(self.normalized.encode()).hexdigest()
    
    def similarity(self, other: 'CodeBlock') -> float:
        """Calculate similarity ratio with another code block."""
        return SequenceMatcher(None, self.normalized, other.normalized).ratio()


class TokenBasedDetector:
    """Detect duplicates using token-based comparison."""
    
    def __init__(self, min_lines: int = 6):
        self.min_lines = min_lines
    
    def detect_duplicates(
        self,
        project_root: str,
        file_paths: List[str],
        similarity_threshold: float = 0.9
    ) -> List[Dict]:
        """
        Detect duplicate code blocks using token-based analysis.
        
        Args:
            project_root: Root directory
            file_paths: Python files to analyze
            similarity_threshold: Minimum similarity (0.0-1.0)
        
        Returns:
            List of duplicate groups
        """
        # Extract code blocks from all files
        all_blocks = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                blocks = self._extract_blocks(code, file_path)
                all_blocks.extend(blocks)
            
            except Exception:
                continue
        
        # Find duplicates
        duplicates = self._find_duplicate_blocks(all_blocks, similarity_threshold)
        
        return duplicates
    
    def _extract_blocks(self, code: str, file_path: str) -> List[CodeBlock]:
        """Extract code blocks from a file."""
        lines = code.splitlines()
        blocks = []
        
        # Sliding window approach
        for i in range(len(lines) - self.min_lines + 1):
            block_lines = lines[i:i + self.min_lines]
            
            # Skip blocks that are mostly empty or comments
            content_lines = [l for l in block_lines if l.strip() and not l.strip().startswith('#')]
            if len(content_lines) < self.min_lines // 2:
                continue
            
            block = CodeBlock(block_lines, i + 1, file_path)
            blocks.append(block)
        
        return blocks
    
    def _find_duplicate_blocks(
        self,
        blocks: List[CodeBlock],
        threshold: float
    ) -> List[Dict]:
        """Find duplicate blocks using similarity comparison."""
        # Group blocks by hash for exact matches
        hash_groups = defaultdict(list)
        for block in blocks:
            hash_groups[block.hash].append(block)
        
        duplicates = []
        
        # Process exact duplicates
        for hash_key, group in hash_groups.items():
            if len(group) >= 2:
                duplicates.append({
                    "type": "exact_duplicate",
                    "similarity": 1.0,
                    "line_count": len(group[0].lines),
                    "occurrences": len(group),
                    "locations": [
                        {
                            "file": block.file_path,
                            "start_line": block.start_line,
                            "end_line": block.end_line
                        }
                        for block in group
                    ],
                    "code_sample": group[0].content,
                    "recommendation": self._generate_recommendation(group)
                })
        
        # Find near-duplicates (if threshold < 1.0)
        if threshold < 1.0:
            near_duplicates = self._find_near_duplicates(blocks, threshold)
            duplicates.extend(near_duplicates)
        
        return duplicates
    
    def _find_near_duplicates(
        self,
        blocks: List[CodeBlock],
        threshold: float
    ) -> List[Dict]:
        """Find near-duplicate blocks."""
        near_duplicates = []
        seen_pairs = set()
        
        for i, block1 in enumerate(blocks):
            for j, block2 in enumerate(blocks[i + 1:], i + 1):
                # Skip if same file and overlapping lines
                if block1.file_path == block2.file_path:
                    if self._blocks_overlap(block1, block2):
                        continue
                
                # Skip if already processed
                pair_key = tuple(sorted([id(block1), id(block2)]))
                if pair_key in seen_pairs:
                    continue
                
                # Calculate similarity
                similarity = block1.similarity(block2)
                
                if similarity >= threshold:
                    seen_pairs.add(pair_key)
                    
                    near_duplicates.append({
                        "type": "near_duplicate",
                        "similarity": round(similarity, 3),
                        "line_count": len(block1.lines),
                        "occurrences": 2,
                        "locations": [
                            {
                                "file": block1.file_path,
                                "start_line": block1.start_line,
                                "end_line": block1.end_line
                            },
                            {
                                "file": block2.file_path,
                                "start_line": block2.start_line,
                                "end_line": block2.end_line
                            }
                        ],
                        "code_sample_1": block1.content,
                        "code_sample_2": block2.content,
                        "recommendation": "Extract common logic to a shared function"
                    })
        
        return near_duplicates
    
    def _blocks_overlap(self, block1: CodeBlock, block2: CodeBlock) -> bool:
        """Check if two blocks overlap."""
        return not (block1.end_line < block2.start_line or block2.end_line < block1.start_line)
    
    def _generate_recommendation(self, blocks: List[CodeBlock]) -> str:
        """Generate refactoring recommendation for duplicate blocks."""
        if len(blocks) == 2:
            return "Extract this code into a shared function/method"
        elif len(blocks) <= 5:
            return f"Extract into a shared function. Found {len(blocks)} duplicates across {len(set(b.file_path for b in blocks))} file(s)"
        else:
            return f"HIGH PRIORITY: {len(blocks)} duplicates found across {len(set(b.file_path for b in blocks))} files. Extract to shared utility"


class ASTBasedDetector:
    """Detect duplicates using AST-based structural comparison."""
    
    def detect_duplicate_functions(
        self,
        project_root: str,
        file_paths: List[str],
        similarity_threshold: float = 0.85
    ) -> List[Dict]:
        """
        Detect duplicate functions using AST comparison.
        
        Compares function structure, not just text.
        """
        functions = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                file_functions = self._extract_functions(code, file_path)
                functions.extend(file_functions)
            
            except Exception:
                continue
        
        # Find duplicate functions
        duplicates = self._find_duplicate_functions(functions, similarity_threshold)
        
        return duplicates
    
    def _extract_functions(self, code: str, file_path: str) -> List[Dict]:
        """Extract all functions from code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    "name": node.name,
                    "file": file_path,
                    "line": node.lineno,
                    "end_line": node.end_lineno or node.lineno,
                    "ast": node,
                    "signature": self._get_function_signature(node),
                    "structure": self._get_structure_hash(node),
                    "body_lines": node.end_lineno - node.lineno if node.end_lineno else 1
                }
                functions.append(func_info)
        
        return functions
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Get function signature."""
        args = [arg.arg for arg in node.args.args]
        return f"{node.name}({', '.join(args)})"
    
    def _get_structure_hash(self, node: ast.FunctionDef) -> str:
        """Get structural hash of function (ignoring variable names)."""
        # Extract structure: types of nodes in order
        structure = []
        
        for child in ast.walk(node):
            structure.append(type(child).__name__)
        
        structure_str = '|'.join(structure)
        return hashlib.md5(structure_str.encode()).hexdigest()
    
    def _find_duplicate_functions(
        self,
        functions: List[Dict],
        threshold: float
    ) -> List[Dict]:
        """Find duplicate functions."""
        duplicates = []
        
        # Group by structure hash
        structure_groups = defaultdict(list)
        for func in functions:
            structure_groups[func['structure']].append(func)
        
        for structure, group in structure_groups.items():
            if len(group) >= 2:
                # Further compare these functions
                for i, func1 in enumerate(group):
                    for func2 in group[i + 1:]:
                        similarity = self._compare_functions(func1, func2)
                        
                        if similarity >= threshold:
                            duplicates.append({
                                "type": "duplicate_function",
                                "similarity": round(similarity, 3),
                                "functions": [
                                    {
                                        "name": func1['name'],
                                        "file": func1['file'],
                                        "line": func1['line'],
                                        "signature": func1['signature']
                                    },
                                    {
                                        "name": func2['name'],
                                        "file": func2['file'],
                                        "line": func2['line'],
                                        "signature": func2['signature']
                                    }
                                ],
                                "recommendation": f"Functions '{func1['name']}' and '{func2['name']}' are {int(similarity*100)}% similar. Consider consolidating."
                            })
        
        return duplicates
    
    def _compare_functions(self, func1: Dict, func2: Dict) -> float:
        """Compare two functions and return similarity."""
        # Compare AST structure
        ast1 = ast.dump(func1['ast'])
        ast2 = ast.dump(func2['ast'])
        
        return SequenceMatcher(None, ast1, ast2).ratio()


class DuplicationRefactorSuggester:
    """Suggest refactoring strategies for duplicate code."""
    
    def suggest_refactoring(self, duplicate: Dict) -> Dict:
        """Generate concrete refactoring suggestions."""
        duplicate_type = duplicate.get("type")
        
        if duplicate_type == "exact_duplicate":
            return self._suggest_extract_function(duplicate)
        elif duplicate_type == "near_duplicate":
            return self._suggest_parameterized_function(duplicate)
        elif duplicate_type == "duplicate_function":
            return self._suggest_consolidate_functions(duplicate)
        
        return {"recommendation": "Refactor to reduce duplication"}
    
    def _suggest_extract_function(self, duplicate: Dict) -> Dict:
        """Suggest extracting duplicate code to a function."""
        locations = duplicate['locations']
        code_sample = duplicate['code_sample']
        
        # Generate new function name
        function_name = "extracted_common_logic"
        
        refactor_example = f"""
# Before: Code duplicated in {len(locations)} locations
# Location 1: {locations[0]['file']} line {locations[0]['start_line']}
# Location 2: {locations[1]['file']} line {locations[1]['start_line']}

{code_sample}

# After: Extract to shared function
def {function_name}():
    \"\"\"Common logic extracted from multiple locations.\"\"\"
{chr(10).join('    ' + line for line in code_sample.split(chr(10)))}

# Then replace all {len(locations)} occurrences with:
{function_name}()
"""
        
        return {
            "strategy": "extract_to_function",
            "function_name": function_name,
            "refactor_example": refactor_example,
            "locations_to_replace": locations,
            "estimated_lines_saved": duplicate['line_count'] * (len(locations) - 1)
        }
    
    def _suggest_parameterized_function(self, duplicate: Dict) -> Dict:
        """Suggest parameterized function for near-duplicates."""
        return {
            "strategy": "parameterize_differences",
            "recommendation": (
                "The code blocks are similar but not identical. "
                "Extract common structure into a function and parameterize the differences."
            ),
            "steps": [
                "1. Identify what differs between the blocks",
                "2. Extract common code to a new function",
                "3. Add parameters for the differing parts",
                "4. Replace all occurrences with function calls"
            ]
        }
    
    def _suggest_consolidate_functions(self, duplicate: Dict) -> Dict:
        """Suggest consolidating duplicate functions."""
        functions = duplicate['functions']
        
        return {
            "strategy": "consolidate_functions",
            "recommendation": f"Consolidate '{functions[0]['name']}' and '{functions[1]['name']}'",
            "steps": [
                "1. Compare function implementations carefully",
                "2. Identify differences (parameters, logic variations)",
                "3. Create unified function with parameters for variations",
                "4. Update all call sites",
                "5. Remove redundant function"
            ]
        }


class DuplicationDetector:
    """Unified code duplication detection orchestrator."""
    
    def __init__(self, min_lines: int = 6, similarity_threshold: float = 0.9):
        self.min_lines = min_lines
        self.similarity_threshold = similarity_threshold
        self.token_detector = TokenBasedDetector(min_lines)
        self.ast_detector = ASTBasedDetector()
        self.suggester = DuplicationRefactorSuggester()
    
    def detect_duplicates(
        self,
        project_root: str,
        file_paths: List[str],
        include_near_duplicates: bool = True,
        include_functions: bool = True
    ) -> Dict:
        """
        Comprehensive duplicate detection.
        
        Args:
            project_root: Project root directory
            file_paths: Python files to analyze
            include_near_duplicates: Detect similar (not just exact) code
            include_functions: Detect duplicate functions
        
        Returns:
            {
              "total_duplicates": int,
              "exact_duplicates": [...],
              "near_duplicates": [...],
              "duplicate_functions": [...],
              "summary": {...}
            }
        """
        all_duplicates = []
        
        # Token-based detection
        threshold = self.similarity_threshold if include_near_duplicates else 1.0
        token_duplicates = self.token_detector.detect_duplicates(
            project_root,
            file_paths,
            threshold
        )
        
        exact_dups = [d for d in token_duplicates if d['type'] == 'exact_duplicate']
        near_dups = [d for d in token_duplicates if d['type'] == 'near_duplicate']
        
        all_duplicates.extend(token_duplicates)
        
        # AST-based function detection
        func_duplicates = []
        if include_functions:
            func_duplicates = self.ast_detector.detect_duplicate_functions(
                project_root,
                file_paths,
                self.similarity_threshold
            )
            all_duplicates.extend(func_duplicates)
        
        # Add refactoring suggestions
        for duplicate in all_duplicates:
            duplicate['refactoring'] = self.suggester.suggest_refactoring(duplicate)
        
        # Calculate summary
        summary = self._generate_summary(exact_dups, near_dups, func_duplicates)
        
        return {
            "total_duplicates": len(all_duplicates),
            "exact_duplicates": exact_dups,
            "near_duplicates": near_dups,
            "duplicate_functions": func_duplicates,
            "summary": summary,
            "detailed_duplicates": all_duplicates
        }
    
    def _generate_summary(
        self,
        exact: List[Dict],
        near: List[Dict],
        functions: List[Dict]
    ) -> Dict:
        """Generate duplication summary with metrics."""
        total_duplicated_lines = sum(
            d['line_count'] * (d['occurrences'] - 1)
            for d in exact
        )
        
        unique_files = set()
        for dup in exact + near:
            for loc in dup.get('locations', []):
                unique_files.add(loc['file'])
        
        return {
            "exact_duplicate_count": len(exact),
            "near_duplicate_count": len(near),
            "duplicate_function_count": len(functions),
            "total_duplicated_lines": total_duplicated_lines,
            "files_affected": len(unique_files),
            "severity": self._calculate_severity(total_duplicated_lines, len(exact)),
            "recommendation": self._get_priority_recommendation(exact, near, functions)
        }
    
    def _calculate_severity(self, duplicated_lines: int, duplicate_count: int) -> str:
        """Calculate severity level."""
        if duplicated_lines > 200 or duplicate_count > 10:
            return "high"
        elif duplicated_lines > 50 or duplicate_count > 5:
            return "medium"
        else:
            return "low"
    
    def _get_priority_recommendation(
        self,
        exact: List[Dict],
        near: List[Dict],
        functions: List[Dict]
    ) -> str:
        """Get prioritized recommendation."""
        if not exact and not near and not functions:
            return "✅ No significant code duplication detected"
        
        recommendations = []
        
        if exact:
            recommendations.append(
                f"🔴 {len(exact)} exact duplicate(s) found - HIGH PRIORITY for refactoring"
            )
        
        if near:
            recommendations.append(
                f"🟡 {len(near)} near-duplicate(s) found - consider refactoring"
            )
        
        if functions:
            recommendations.append(
                f"🟠 {len(functions)} duplicate function(s) found - consolidate implementations"
            )
        
        return '\n'.join(recommendations)
    
    def _find_python_files(self, root_dir: str) -> List[str]:
        """Find all Python files in directory."""
        import os
        python_files = []
        
        for dirpath, _, filenames in os.walk(root_dir):
            if any(skip in dirpath for skip in ['.git', '__pycache__', 'venv', '.venv']):
                continue
            
            for filename in filenames:
                if filename.endswith('.py'):
                    python_files.append(os.path.join(dirpath, filename))
        
        return python_files
