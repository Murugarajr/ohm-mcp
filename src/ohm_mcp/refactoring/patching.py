class PatchGenerator:
    """Generates unified diff patches for changes"""

    def generate_patch(self, original: str, modified: str, file_path: str = "code.py") -> str:
        """Create unified diff patch"""
        import difflib

        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=''
        )

        return ''.join(diff)
    
    def apply_function_patch(
        self,
        original_file: str,
        function_name: str,
        old_function_code: str,
        new_function_code: str,
        file_path: str = "code.py"
    ) -> str:
        """
        Generate patch for replacing a single function in a file.
        
        Safety: refuses if old_function_code is not found exactly once.
        """
        occurrences = original_file.count(old_function_code)
        if occurrences != 1:
            return (
                f"Refused: expected '{function_name}' exactly once, "
                f"found {occurrences} times."
            )

        modified = original_file.replace(old_function_code, new_function_code, 1)
        return self.generate_patch(original_file, modified, file_path)
