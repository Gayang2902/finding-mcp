"""Language detection and per-language metadata.

Phase 1 scope: Java, PHP, JavaScript, TypeScript (incl. TSX).
"""

from __future__ import annotations

from pathlib import Path

# extension -> canonical language name
EXTENSION_MAP: dict[str, str] = {
    ".java": "java",
    ".php": "php",
    ".phtml": "php",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}

# ctags --language-force argument names per language
CTAGS_LANGUAGE: dict[str, str] = {
    "java": "Java",
    "php": "PHP",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "tsx": "TypeScript",
}

# ripgrep --type names per language
RIPGREP_TYPE: dict[str, str] = {
    "java": "java",
    "php": "php",
    "javascript": "js",
    "typescript": "ts",
    "tsx": "ts",
}

ALL_LANGUAGES = tuple(set(EXTENSION_MAP.values()))


def detect_language(file_path: str | Path) -> str | None:
    """Detect language by file extension. Returns None if unsupported."""
    suffix = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(suffix)


def is_supported_file(file_path: str | Path) -> bool:
    return detect_language(file_path) is not None
