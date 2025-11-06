"""File type detection utility using multiple strategies."""

from pathlib import Path
from typing import Optional

# File extension to type mapping (v2.0 - expanded for MarkItDown support)
EXTENSION_MAP = {
    # Documents
    '.pdf': 'pdf',
    '.docx': 'docx',
    '.doc': 'doc',  # Legacy Word format
    '.xlsx': 'xlsx',
    '.xls': 'xls',  # Legacy Excel format
    '.pptx': 'pptx',
    '.ppt': 'ppt',  # Legacy PowerPoint format
    # Web
    '.html': 'html',
    '.htm': 'html',
    # Images
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.gif': 'image',
    '.bmp': 'image',
    '.tiff': 'image',
    '.tif': 'image',
    '.webp': 'image',
    # Audio
    '.wav': 'audio',
    '.mp3': 'audio',
    '.m4a': 'audio',
    '.flac': 'audio',
    '.ogg': 'audio',
    # E-books
    '.epub': 'epub',
    # Data formats
    '.json': 'json',
    '.xml': 'xml',
    '.csv': 'csv',
    # Archives
    '.zip': 'zip',
    # Email
    '.msg': 'msg',
}

# MIME type to file type mapping (v2.0 - expanded)
MIME_MAP = {
    # Documents
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
    'application/vnd.ms-powerpoint': 'ppt',
    # Web
    'text/html': 'html',
    # Images
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/gif': 'image',
    'image/bmp': 'image',
    'image/tiff': 'image',
    'image/webp': 'image',
    # Audio
    'audio/wav': 'audio',
    'audio/mpeg': 'audio',
    'audio/mp4': 'audio',
    'audio/flac': 'audio',
    'audio/ogg': 'audio',
    # E-books
    'application/epub+zip': 'epub',
    # Data formats
    'application/json': 'json',
    'application/xml': 'xml',
    'text/xml': 'xml',
    'text/csv': 'csv',
    # Archives
    'application/zip': 'zip',
    # Email
    'application/vnd.ms-outlook': 'msg',
}

# Magic bytes signatures for file types (v2.0 - expanded)
MAGIC_SIGNATURES = {
    'pdf': [b'%PDF-'],
    'html': [b'<!DOCTYPE', b'<html', b'<HTML'],
    'docx': [b'PK\x03\x04'],  # ZIP signature (DOCX is ZIP-based)
    'xlsx': [b'PK\x03\x04'],  # ZIP signature (XLSX is ZIP-based)
    'pptx': [b'PK\x03\x04'],  # ZIP signature (PPTX is ZIP-based)
    'epub': [b'PK\x03\x04'],  # ZIP signature (EPUB is ZIP-based)
    'zip': [b'PK\x03\x04'],  # ZIP signature
    'png': [b'\x89PNG\r\n\x1a\n'],
    'jpg': [b'\xff\xd8\xff'],
    'gif': [b'GIF87a', b'GIF89a'],
    'bmp': [b'BM'],
    'tiff': [b'II*\x00', b'MM\x00*'],
    'wav': [b'RIFF'],
    'mp3': [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2', b'ID3'],
    'json': [b'{', b'['],  # JSON typically starts with { or [
    'xml': [b'<?xml', b'<'],  # XML starts with <?xml or <
}


class FileTypeDetector:
    """
    Detects file types using a multi-layered approach:
    1. File extension (fast, first check)
    2. Magic bytes (reliable, binary signature)
    3. MIME type detection (requires python-magic)
    4. Content analysis (fallback for ambiguous cases)
    """

    def __init__(self):
        """Initialize the file type detector."""
        self._magic_available = False
        try:
            import magic
            self._magic = magic
            self._magic_available = True
        except ImportError:
            pass

    def detect(self, file_path: Path, allow_fallback: bool = True) -> str:
        """
        Detect the file type of the given file.

        Args:
            file_path: Path to the file to detect
            allow_fallback: If True, use multiple detection strategies

        Returns:
            File type string ('pdf', 'html', 'docx', 'xlsx', etc.)

        Raises:
            ValueError: If file type cannot be determined
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Strategy 1: Extension-based detection (fast)
        ext = file_path.suffix.lower()
        if ext in EXTENSION_MAP:
            file_type = EXTENSION_MAP[ext]

            # Verify with magic bytes if available
            if allow_fallback and self._verify_with_magic_bytes(file_path, file_type):
                return file_type

            # If verification fails but we have fallback, continue
            if not allow_fallback:
                return file_type

        # Strategy 2: MIME type detection (reliable)
        if self._magic_available:
            mime_type = self._detect_mime_type(file_path)
            if mime_type in MIME_MAP:
                return MIME_MAP[mime_type]

        # Strategy 3: Magic bytes detection (no python-magic required)
        detected_type = self._detect_by_magic_bytes(file_path)
        if detected_type:
            # For ZIP-based formats (DOCX, XLSX), need further analysis
            if detected_type in ['docx', 'xlsx']:
                return self._detect_office_format(file_path)
            return detected_type

        # Strategy 4: Content analysis (last resort)
        if allow_fallback:
            detected_type = self._detect_by_content(file_path)
            if detected_type:
                return detected_type

        # Could not determine file type
        raise ValueError(
            f"Could not determine file type for: {file_path}. "
            f"Supported types: {', '.join(set(EXTENSION_MAP.values()))}"
        )

    def _verify_with_magic_bytes(self, file_path: Path, expected_type: str) -> bool:
        """
        Verify file type using magic bytes.

        Args:
            file_path: Path to the file
            expected_type: Expected file type

        Returns:
            True if magic bytes match expected type
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(512)  # Read first 512 bytes

            if expected_type in MAGIC_SIGNATURES:
                signatures = MAGIC_SIGNATURES[expected_type]
                return any(header.startswith(sig) for sig in signatures)

            return True  # No signature to verify, assume correct
        except Exception:
            return True  # If we can't verify, assume extension is correct

    def _detect_mime_type(self, file_path: Path) -> Optional[str]:
        """
        Detect MIME type using python-magic.

        Args:
            file_path: Path to the file

        Returns:
            MIME type string or None
        """
        try:
            return self._magic.from_file(str(file_path), mime=True)
        except Exception:
            return None

    def _detect_by_magic_bytes(self, file_path: Path) -> Optional[str]:
        """
        Detect file type by magic bytes signature.

        Args:
            file_path: Path to the file

        Returns:
            File type string or None
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(512)

            for file_type, signatures in MAGIC_SIGNATURES.items():
                if any(header.startswith(sig) for sig in signatures):
                    return file_type

            return None
        except Exception:
            return None

    def _detect_office_format(self, file_path: Path) -> str:
        """
        Distinguish between Office formats (DOCX, XLSX, PPTX, EPUB - all are ZIP files).

        Args:
            file_path: Path to the ZIP-based Office file

        Returns:
            'docx', 'xlsx', 'pptx', 'epub', or 'zip'

        Raises:
            ValueError: If cannot determine Office format
        """
        try:
            import zipfile

            with zipfile.ZipFile(file_path, 'r') as zip_file:
                file_list = zip_file.namelist()

                # DOCX contains word/ directory
                if any('word/' in f for f in file_list):
                    return 'docx'

                # XLSX contains xl/ directory
                if any('xl/' in f for f in file_list):
                    return 'xlsx'

                # PPTX contains ppt/ directory
                if any('ppt/' in f for f in file_list):
                    return 'pptx'

                # EPUB contains mimetype file with specific content
                if 'mimetype' in file_list:
                    try:
                        mimetype = zip_file.read('mimetype').decode('utf-8').strip()
                        if mimetype == 'application/epub+zip':
                            return 'epub'
                    except Exception:
                        pass

                # Check for content types
                if '[Content_Types].xml' in file_list:
                    content_types = zip_file.read('[Content_Types].xml').decode('utf-8')
                    if 'wordprocessingml' in content_types:
                        return 'docx'
                    if 'spreadsheetml' in content_types:
                        return 'xlsx'
                    if 'presentationml' in content_types:
                        return 'pptx'

        except Exception:
            pass

        # Default to regular ZIP if unclear
        return 'zip'

    def _detect_by_content(self, file_path: Path) -> Optional[str]:
        """
        Detect file type by analyzing content (last resort).

        Args:
            file_path: Path to the file

        Returns:
            File type string or None
        """
        try:
            # Try reading as text to detect HTML
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # Read first 1KB

            # Check for HTML markers
            html_markers = ['<!doctype', '<html', '<head', '<body', '<div']
            content_lower = content.lower()
            if any(marker in content_lower for marker in html_markers):
                return 'html'

            return None
        except Exception:
            return None

    def is_supported(self, file_path: Path) -> bool:
        """
        Check if the file type is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if file type is supported
        """
        try:
            self.detect(file_path)
            return True
        except (ValueError, FileNotFoundError):
            return False

    def get_supported_types(self) -> list[str]:
        """
        Get list of supported file types.

        Returns:
            List of supported file type strings
        """
        return sorted(set(EXTENSION_MAP.values()))
