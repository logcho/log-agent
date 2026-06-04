import os
import shutil
import fnmatch
from datetime import datetime
from langchain_core.tools import tool

@tool
def get_current_directory() -> str:
    """Get the current working directory of the agent's process.
    
    Returns:
        str: The absolute path of the current working directory.
    """
    try:
        return os.getcwd()
    except Exception as e:
        return f"Error getting current directory: {str(e)}"


@tool
def change_current_directory(path: str) -> str:
    """Change the current working directory of the process.
    
    Args:
        path (str): The relative or absolute path of the target directory.
        
    Returns:
        str: Confirmation message or error message.
    """
    try:
        os.chdir(path)
        return f"Successfully changed directory to: {os.getcwd()}"
    except FileNotFoundError:
        return f"Error: Directory '{path}' not found."
    except PermissionError:
        return f"Error: Permission denied to access '{path}'."
    except Exception as e:
        return f"Error changing directory: {str(e)}"


@tool
def list_directory(path: str = ".") -> str:
    """List the contents of a directory.
    
    Args:
        path (str, optional): The directory path to list. Defaults to ".".
        
    Returns:
        str: A formatted list of directory contents indicating type (FILE/DIR) or an error.
    """
    try:
        items = os.listdir(path)
        if not items:
            return f"Directory '{path}' is empty."
        
        formatted_items = []
        # Sort items: directories first, then files
        dirs = []
        files = []
        
        for item in sorted(items):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                dirs.append(f"[DIR]  {item}/")
            else:
                files.append(f"[FILE] {item}")
                
        return "\n".join(dirs + files)
    except FileNotFoundError:
        return f"Error: Path '{path}' not found."
    except PermissionError:
        return f"Error: Permission denied for path '{path}'."
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@tool
def create_directory(path: str) -> str:
    """Create a new directory recursively. If parent directories do not exist, they will be created.
    
    Args:
        path (str): The path of the directory to create.
        
    Returns:
        str: Success message or error message.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"Successfully created directory (including any parent directories) at: {os.path.abspath(path)}"
    except PermissionError:
        return f"Error: Permission denied to create directory at '{path}'."
    except Exception as e:
        return f"Error creating directory: {str(e)}"


@tool
def remove_path(path: str, recursive: bool = False) -> str:
    """Remove a file or directory from the filesystem.
    
    Args:
        path (str): The target file or directory path.
        recursive (bool, optional): If True and target is a directory, recursively deletes all contents. Defaults to False.
        
    Returns:
        str: Success message or error message.
    """
    try:
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
            
        if os.path.isdir(path):
            if recursive:
                shutil.rmtree(path)
                return f"Successfully deleted directory recursively: {os.path.abspath(path)}"
            else:
                os.rmdir(path)
                return f"Successfully deleted empty directory: {os.path.abspath(path)}"
        else:
            os.remove(path)
            return f"Successfully deleted file: {os.path.abspath(path)}"
    except OSError as e:
        # Standard OSError includes directory not empty if recursive=False
        return f"Error deleting path: {e.strerror} (Code {e.errno})"
    except Exception as e:
        return f"Error deleting path: {str(e)}"


@tool
def move_or_rename(source: str, destination: str) -> str:
    """Rename or move a file or directory to a new location.
    
    Args:
        source (str): The source file or directory path.
        destination (str): The destination file or directory path.
        
    Returns:
        str: Success message or error message.
    ```"""
    try:
        shutil.move(source, destination)
        return f"Successfully moved/renamed '{source}' to '{destination}'"
    except FileNotFoundError:
        return f"Error: Source '{source}' not found."
    except PermissionError:
        return f"Error: Permission denied moving '{source}' to '{destination}'."
    except Exception as e:
        return f"Error moving/renaming: {str(e)}"


@tool
def get_metadata(path: str) -> str:
    """Retrieve metadata information for a file or directory (size, modification time, exists, type).
    
    Args:
        path (str): Path of the file or directory.
        
    Returns:
        str: A formatted string of file metadata or an error.
    """
    try:
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
            
        stat_info = os.stat(path)
        size = stat_info.st_size
        mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        is_dir = os.path.isdir(path)
        path_type = "Directory" if is_dir else "File"
        
        info = [
            f"Path: {os.path.abspath(path)}",
            f"Type: {path_type}",
            f"Size: {size} bytes",
            f"Last Modified: {mtime}",
        ]
        return "\n".join(info)
    except Exception as e:
        return f"Error retrieving metadata: {str(e)}"


@tool
def find_files(pattern: str, path: str = ".") -> str:
    """Find files recursively matching a wildcard pattern (e.g. '*.py', 'temp*') under a specified path.
    
    Args:
        pattern (str): The wildcard pattern to match.
        path (str, optional): The root path to start search. Defaults to ".".
        
    Returns:
        str: A formatted list of matching file paths or a 'not found' message.
    """
    try:
        matches = []
        for root, _, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, pattern):
                # Get relative path for clean display
                full_path = os.path.join(root, filename)
                matches.append(full_path)
                
        if not matches:
            return f"No files matching '{pattern}' found in '{path}'."
        return "\n".join(matches)
    except Exception as e:
        return f"Error finding files: {str(e)}"


@tool
def read_file(path: str) -> str:
    """Read the full content of a file as a string.
    
    Args:
        path (str): The path to the file.
        
    Returns:
        str: Content of the file or error message.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{path}' not found."
    except PermissionError:
        return f"Error: Permission denied reading '{path}'."
    except UnicodeDecodeError:
        return f"Error: File '{path}' is not a valid text file (decoding failed)."
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. If the file exists, it will be overwritten. If not, it will be created.
    
    Args:
        path (str): The path to write/create the file.
        content (str): The content to write into the file.
        
    Returns:
        str: Success message or error message.
    """
    try:
        # Create directory if it doesn't exist
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to file: {os.path.abspath(path)}"
    except PermissionError:
        return f"Error: Permission denied writing to '{path}'."
    except Exception as e:
        return f"Error writing file: {str(e)}"


# Export all defined OS tools as a list
os_toolset = [
    get_current_directory,
    change_current_directory,
    list_directory,
    create_directory,
    remove_path,
    move_or_rename,
    get_metadata,
    find_files,
    read_file,
    write_file
]
