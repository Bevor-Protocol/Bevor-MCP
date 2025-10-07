import os
from pathlib import Path
from typing import Optional

def find_contracts_folder_in_directory(directory: Path) -> Optional[Path]:
    """
    Find the primary folder containing Solidity (.sol) files in the given directory.
    
    This function searches for folders that contain .sol files, prioritizing common
    naming patterns like 'contracts', 'src', 'source', etc. but will ultimately
    return any folder that contains Solidity files.
    
    Args:
        directory: Root directory to search in
        
    Returns:
        Path to the folder containing .sol files, or None if no such folder is found
    """
    # Common folder names for Solidity contracts
    priority_names = {'contracts', 'src', 'source', 'solidity'}
    
    # Track folders with .sol files and their file counts
    sol_folders = {}
    
    for root, dirs, files in os.walk(directory):
        # Count .sol files in current directory
        sol_count = sum(1 for f in files if f.lower().endswith('.sol'))
        if sol_count > 0:
            sol_folders[Path(root)] = sol_count
            
        # Skip common non-contract directories
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'build', 'test'}]
    
    if not sol_folders:
        return None
        
    # First try to find a priority named folder with .sol files
    for folder in sol_folders:
        if folder.name.lower() in priority_names:
            return folder
            
    # Otherwise return the folder with the most .sol files
    return max(sol_folders.items(), key=lambda x: x[1])[0]