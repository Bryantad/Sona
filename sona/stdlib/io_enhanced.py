# Sona IO Module - Enhanced file and directory operations
# Provides comprehensive I/O capabilities for Sona applications

import os
import shutil
from pathlib import Path
import json
import csv

class SonaIOModule:
    """Enhanced I/O module for Sona applications"""
    
    def __init__(self):
        self.current_dir = os.getcwd()
    
    # File reading/writing operations
    def read_file(self, file_path, encoding="utf-8"):
        """Read entire file content as string"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def write_file(self, file_path, content, encoding="utf-8", append=False):
        """Write content to file"""
        try:
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False
    
    def read_lines(self, file_path, encoding="utf-8"):
        """Read file and return list of lines"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.readlines()
        except Exception as e:
            print(f"Error reading lines from {file_path}: {e}")
            return []
    
    def write_lines(self, file_path, lines, encoding="utf-8", append=False):
        """Write list of lines to file"""
        try:
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding=encoding) as f:
                for line in lines:
                    f.write(str(line) + '\n')
            return True
        except Exception as e:
            print(f"Error writing lines to {file_path}: {e}")
            return False
    
    # Binary file operations
    def read_binary(self, file_path):
        """Read binary file"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading binary file {file_path}: {e}")
            return None
    
    def write_binary(self, file_path, data):
        """Write binary data to file"""
        try:
            with open(file_path, 'wb') as f:
                f.write(data)
            return True
        except Exception as e:
            print(f"Error writing binary file {file_path}: {e}")
            return False
    
    # Directory operations
    def list_directory(self, dir_path="."):
        """List contents of directory"""
        try:
            return os.listdir(dir_path)
        except Exception as e:
            print(f"Error listing directory {dir_path}: {e}")
            return []
    
    def create_directory(self, dir_path, parents=True):
        """Create directory"""
        try:
            if parents:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            else:
                os.mkdir(dir_path)
            return True
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}")
            return False
    
    def remove_directory(self, dir_path, recursive=False):
        """Remove directory"""
        try:
            if recursive:
                shutil.rmtree(dir_path)
            else:
                os.rmdir(dir_path)
            return True
        except Exception as e:
            print(f"Error removing directory {dir_path}: {e}")
            return False
    
    def get_current_directory(self):
        """Get current working directory"""
        return os.getcwd()
    
    def set_current_directory(self, dir_path):
        """Change current working directory"""
        try:
            os.chdir(dir_path)
            self.current_dir = dir_path
            return True
        except Exception as e:
            print(f"Error changing directory to {dir_path}: {e}")
            return False
    
    # File/directory info and manipulation
    def exists(self, path):
        """Check if file or directory exists"""
        return os.path.exists(path)
    
    def is_file(self, path):
        """Check if path is a file"""
        return os.path.isfile(path)
    
    def is_directory(self, path):
        """Check if path is a directory"""
        return os.path.isdir(path)
    
    def get_file_size(self, file_path):
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            print(f"Error getting size of {file_path}: {e}")
            return -1
    
    def get_file_modified_time(self, file_path):
        """Get file modification time"""
        try:
            return os.path.getmtime(file_path)
        except Exception as e:
            print(f"Error getting modification time of {file_path}: {e}")
            return -1
    
    def copy_file(self, src_path, dst_path):
        """Copy file"""
        try:
            shutil.copy2(src_path, dst_path)
            return True
        except Exception as e:
            print(f"Error copying {src_path} to {dst_path}: {e}")
            return False
    
    def move_file(self, src_path, dst_path):
        """Move/rename file"""
        try:
            shutil.move(src_path, dst_path)
            return True
        except Exception as e:
            print(f"Error moving {src_path} to {dst_path}: {e}")
            return False
    
    def delete_file(self, file_path):
        """Delete file"""
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
            return False
    
    # Path operations
    def join_path(self, *parts):
        """Join path components"""
        return os.path.join(*parts)
    
    def get_absolute_path(self, path):
        """Get absolute path"""
        return os.path.abspath(path)
    
    def get_parent_directory(self, path):
        """Get parent directory of path"""
        return os.path.dirname(path)
    
    def get_filename(self, path):
        """Get filename from path"""
        return os.path.basename(path)
    
    def get_file_extension(self, path):
        """Get file extension"""
        return os.path.splitext(path)[1]
    
    def get_filename_without_extension(self, path):
        """Get filename without extension"""
        return os.path.splitext(os.path.basename(path))[0]
    
    # CSV operations
    def read_csv(self, file_path, delimiter=',', encoding="utf-8"):
        """Read CSV file and return list of rows"""
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as f:
                reader = csv.reader(f, delimiter=delimiter)
                return list(reader)
        except Exception as e:
            print(f"Error reading CSV {file_path}: {e}")
            return []
    
    def write_csv(self, file_path, rows, delimiter=',', encoding="utf-8"):
        """Write data to CSV file"""
        try:
            with open(file_path, 'w', encoding=encoding, newline='') as f:
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerows(rows)
            return True
        except Exception as e:
            print(f"Error writing CSV {file_path}: {e}")
            return False
    
    # JSON operations
    def read_json(self, file_path, encoding="utf-8"):
        """Read JSON file"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading JSON {file_path}: {e}")
            return None
    
    def write_json(self, file_path, data, encoding="utf-8", indent=2):
        """Write data to JSON file"""
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error writing JSON {file_path}: {e}")
            return False
    
    # Utility functions
    def find_files(self, directory, pattern="*", recursive=True):
        """Find files matching pattern"""
        try:
            from pathlib import Path
            path = Path(directory)
            if recursive:
                return [str(p) for p in path.rglob(pattern)]
            else:
                return [str(p) for p in path.glob(pattern)]
        except Exception as e:
            print(f"Error finding files in {directory}: {e}")
            return []
    
    def get_temp_directory(self):
        """Get system temporary directory"""
        import tempfile
        return tempfile.gettempdir()
    
    def create_temp_file(self, suffix="", prefix="sona_"):
        """Create temporary file and return path"""
        try:
            import tempfile
            fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(fd)  # Close the file descriptor
            return path
        except Exception as e:
            print(f"Error creating temp file: {e}")
            return None

# Create the module instance
io = SonaIOModule()

# Export for compatibility
__all__ = ['io']
