"""
compression - File compression utilities for Sona stdlib

Provides utilities for working with compressed files:
- zip: Create ZIP archive from directory
- unzip: Extract ZIP archive
- gzip: Compress file with gzip
- tar: Create TAR archive with optional compression
"""

import zipfile
import gzip as _gzip
import tarfile
import os
import shutil


def zip(source_dir, output_file=None):
    """
    Create a ZIP archive from a directory.

    Args:
        source_dir: Directory to compress
        output_file: Output ZIP file path (default: source_dir + '.zip')

    Returns:
        Path to created ZIP file

    Example:
        compression.zip("myproject", "myproject.zip")
        compression.zip("data")  # Creates data.zip
    """
    if output_file is None:
        output_file = source_dir.rstrip('/\\') + '.zip'

    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zf.write(file_path, arcname)

    return output_file


def unzip(zip_file, dest_dir=None):
    """
    Extract a ZIP archive.

    Args:
        zip_file: Path to ZIP file
        dest_dir: Destination directory (default: current directory)

    Returns:
        Path to extraction directory

    Example:
        compression.unzip("archive.zip", "extracted")
        compression.unzip("data.zip")  # Extracts to current directory
    """
    if dest_dir is None:
        dest_dir = os.getcwd()

    dest_dir = os.path.abspath(dest_dir)

    with zipfile.ZipFile(zip_file, 'r') as zf:
        # Security: Validate all paths to prevent path traversal
        for member in zf.namelist():
            member_path = os.path.abspath(os.path.join(dest_dir, member))
            if not member_path.startswith(dest_dir):
                raise ValueError(f"Path traversal attempt detected: {member}")
        zf.extractall(dest_dir)

    return dest_dir


def gzip(input_file, output_file=None):
    """
    Compress a file with gzip.

    Args:
        input_file: File to compress
        output_file: Output file path (default: input_file + '.gz')

    Returns:
        Path to compressed file

    Example:
        compression.gzip("data.txt", "data.txt.gz")
        compression.gzip("log.txt")  # Creates log.txt.gz
    """
    if output_file is None:
        output_file = input_file + '.gz'

    with open(input_file, 'rb') as f_in:
        with _gzip.open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return output_file


def gunzip(input_file, output_file=None):
    """
    Decompress a gzip file.

    Args:
        input_file: Gzipped file to decompress
        output_file: Output file path (default: removes .gz extension)

    Returns:
        Path to decompressed file

    Example:
        compression.gunzip("data.txt.gz", "data.txt")
        compression.gunzip("log.txt.gz")  # Creates log.txt
    """
    if output_file is None:
        if input_file.endswith('.gz'):
            output_file = input_file[:-3]
        else:
            output_file = input_file + '.decompressed'

    with _gzip.open(input_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return output_file


def tar(source_dir, output_file=None, mode='gz'):
    """
    Create a TAR archive with optional compression.

    Args:
        source_dir: Directory to archive
        output_file: Output TAR file path (default: source_dir + extension)
        mode: Compression mode:
            - 'gz': gzip compression (default) → .tar.gz
            - 'bz2': bzip2 compression → .tar.bz2
            - 'xz': xz compression → .tar.xz
            - '': no compression → .tar

    Returns:
        Path to created TAR file

    Example:
        compression.tar("project", "project.tar.gz", mode="gz")
        compression.tar("data", mode="bz2")  # Creates data.tar.bz2
        compression.tar("logs", mode="")     # Creates logs.tar (no compression)
    """
    # Determine output file and tar mode
    if output_file is None:
        base = source_dir.rstrip('/\\')
        if mode == 'gz':
            output_file = base + '.tar.gz'
        elif mode == 'bz2':
            output_file = base + '.tar.bz2'
        elif mode == 'xz':
            output_file = base + '.tar.xz'
        else:
            output_file = base + '.tar'

    # Determine tar open mode
    if mode == 'gz':
        tar_mode = 'w:gz'
    elif mode == 'bz2':
        tar_mode = 'w:bz2'
    elif mode == 'xz':
        tar_mode = 'w:xz'
    else:
        tar_mode = 'w'

    with tarfile.open(output_file, tar_mode) as tf:
        tf.add(source_dir, arcname=os.path.basename(source_dir))

    return output_file


def untar(tar_file, dest_dir=None):
    """
    Extract a TAR archive (supports gz, bz2, xz compression).

    Args:
        tar_file: Path to TAR file
        dest_dir: Destination directory (default: current directory)

    Returns:
        Path to extraction directory

    Example:
        compression.untar("archive.tar.gz", "extracted")
        compression.untar("data.tar")  # Extracts to current directory
    """
    if dest_dir is None:
        dest_dir = os.getcwd()

    dest_dir = os.path.abspath(dest_dir)

    with tarfile.open(tar_file, 'r:*') as tf:
        # Security: Validate all paths to prevent path traversal
        for member in tf.getmembers():
            member_path = os.path.abspath(os.path.join(dest_dir, member.name))
            if not member_path.startswith(dest_dir):
                raise ValueError(f"Path traversal attempt detected: {member.name}")
        tf.extractall(dest_dir)

    return dest_dir


def compress_string(text, encoding='utf-8'):
    """
    Compress a string using gzip.

    Args:
        text: String to compress
        encoding: Text encoding

    Returns:
        Compressed bytes

    Example:
        compressed = compress_string("Hello World!")
    """
    return _gzip.compress(text.encode(encoding))


def decompress_string(data, encoding='utf-8'):
    """
    Decompress gzipped bytes to string.

    Args:
        data: Compressed bytes
        encoding: Text encoding

    Returns:
        Decompressed string

    Example:
        text = decompress_string(compressed_data)
    """
    return _gzip.decompress(data).decode(encoding)


def list_zip(zip_file):
    """
    List contents of ZIP archive.

    Args:
        zip_file: Path to ZIP file

    Returns:
        List of file names in archive

    Example:
        files = list_zip("archive.zip")
        for file in files:
            print(file)
    """
    with zipfile.ZipFile(zip_file, 'r') as zf:
        return zf.namelist()


def list_tar(tar_file):
    """
    List contents of TAR archive.

    Args:
        tar_file: Path to TAR file

    Returns:
        List of file names in archive

    Example:
        files = list_tar("archive.tar.gz")
        for file in files:
            print(file)
    """
    with tarfile.open(tar_file, 'r:*') as tf:
        return tf.getnames()


def is_compressed(file_path):
    """
    Check if file appears to be compressed.

    Args:
        file_path: Path to file

    Returns:
        True if file extension indicates compression

    Example:
        if is_compressed("data.gz"):
            print("File is compressed")
    """
    compressed_extensions = (
        '.gz', '.bz2', '.xz', '.zip', '.tar.gz',
        '.tar.bz2', '.tar.xz', '.tgz', '.tbz2'
    )
    return file_path.lower().endswith(compressed_extensions)


def get_compression_type(file_path):
    """
    Detect compression type from file extension.

    Args:
        file_path: Path to file

    Returns:
        Compression type string or None

    Example:
        comp_type = get_compression_type("data.tar.gz")
        print(comp_type)  # "tar.gz"
    """
    file_lower = file_path.lower()

    if file_lower.endswith('.tar.gz') or file_lower.endswith('.tgz'):
        return 'tar.gz'
    elif file_lower.endswith('.tar.bz2') or file_lower.endswith('.tbz2'):
        return 'tar.bz2'
    elif file_lower.endswith('.tar.xz'):
        return 'tar.xz'
    elif file_lower.endswith('.tar'):
        return 'tar'
    elif file_lower.endswith('.gz'):
        return 'gz'
    elif file_lower.endswith('.bz2'):
        return 'bz2'
    elif file_lower.endswith('.xz'):
        return 'xz'
    elif file_lower.endswith('.zip'):
        return 'zip'

    return None


__all__ = [
    'zip',
    'unzip',
    'gzip',
    'gunzip',
    'tar',
    'untar',
    'compress_string',
    'decompress_string',
    'list_zip',
    'list_tar',
    'is_compressed',
    'get_compression_type',
]
