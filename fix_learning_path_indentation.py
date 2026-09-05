"""
Script to fix the indentation in src/learning_path.py
This adds proper try-except structure for observability tracking.
"""

import re

# Read the file
with open('src/learning_path.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the generate_path method and fix indentation
# The issue is that code after line 323 needs to be indented under the try block

# Pattern: Find from "relevant_docs = " to the end of generate_path method (before "def save_path")
# We need to indent everything between the try block and the except block

lines = content.split('\n')
fixed_lines = []
in_try_block = False
try_start_line = None
indent_needed = False

for i, line in enumerate(lines):
    # Detect the start of the try block in generate_path
    if 'try:' in line and i > 280 and i < 310:  # Around line 300
        in_try_block = True
        try_start_line = i
        fixed_lines.append(line)
        continue
    
    # Detect where indentation is missing (after the validation checks)
    if in_try_block and line.strip().startswith('relevant_docs = '):
        indent_needed = True
    
    # Stop indenting at the except block or next method
    if indent_needed and (line.strip().startswith('except Exception') or line.strip().startswith('def save_path')):
        indent_needed = False
        in_try_block = False
        
        # Add the except block before this line if it's "def save_path"
        if line.strip().startswith('def save_path'):
            # Add proper except block
            fixed_lines.append('')
            fixed_lines.append('        except Exception as e:')
            fixed_lines.append('            # Mark as failed')
            fixed_lines.append('            error_message = str(e)')
            fixed_lines.append('            ')
            fixed_lines.append('            # Log failure metrics')
            fixed_lines.append('            generation_time_ms = (time.time() - generation_start_time) * 1000')
            fixed_lines.append('            self.obs_manager.log_metric("path_generation_success", 0.0, {')
            fixed_lines.append('                "topic": topic,')
            fixed_lines.append('                "expertise_level": expertise_level,')
            fixed_lines.append('                "error": error_message,')
            fixed_lines.append('                "duration_ms": generation_time_ms,')
            fixed_lines.append('                "user_id": user_id')
            fixed_lines.append('            })')
            fixed_lines.append('            ')
            fixed_lines.append('            self.obs_manager.log_event("path_generation_failed", {')
            fixed_lines.append('                "topic": topic,')
            fixed_lines.append('                "expertise_level": expertise_level,')
            fixed_lines.append('                "error": error_message,')
            fixed_lines.append('                "generation_time_ms": generation_time_ms,')
            fixed_lines.append('                "user_id": user_id')
            fixed_lines.append('            })')
            fixed_lines.append('            ')
            fixed_lines.append('            # Re-raise the exception')
            fixed_lines.append('            raise')
            fixed_lines.append('')
    
    # Add indentation if needed
    if indent_needed and line and not line.startswith('        '):
        # Add 4 more spaces of indentation
        if line.startswith('    '):
            fixed_lines.append('    ' + line)
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write back
with open('src/learning_path.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print("✅ Fixed indentation in src/learning_path.py")
print("⚠️  Please review the changes manually to ensure correctness")
