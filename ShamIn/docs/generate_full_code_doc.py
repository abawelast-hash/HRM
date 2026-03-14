"""
سكريبت توليد ملف الكود_كاملا.md
يمر على جميع الملفات في المسار الذي يتواجد فيه السكريبت
ويوثق شجرة المجلدات ومحتوى كل ملف
"""

import os
from pathlib import Path
from datetime import datetime

# المجلدات والملفات المستثناة
SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "node_modules",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    "logs", ".eggs", "*.egg-info",
}

SKIP_FILES = {
    ".DS_Store", "Thumbs.db", ".gitkeep",
}

# امتدادات الملفات الثنائية (لا يمكن قراءتها كنص)
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".exe", ".dll", ".so", ".dylib",
    ".pth", ".pkl", ".h5", ".hdf5", ".bin", ".dat",
    ".pyc", ".pyo", ".whl",
    ".ttf", ".otf", ".woff", ".woff2",
    ".db", ".sqlite", ".sqlite3",
}

# تحديد لغة الكود حسب الامتداد
LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".ps1": "powershell",
    ".bat": "batch",
    ".cmd": "batch",
    ".md": "markdown",
    ".txt": "",
    ".env": "bash",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",
    ".dockerfile": "dockerfile",
    ".r": "r",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".lua": "lua",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
}


def should_skip_dir(dirname: str) -> bool:
    """هل يجب تخطي هذا المجلد"""
    return dirname in SKIP_DIRS or dirname.startswith(".")


def should_skip_file(filename: str) -> bool:
    """هل يجب تخطي هذا الملف"""
    return filename in SKIP_FILES


def is_binary(filepath: Path) -> bool:
    """هل الملف ثنائي (غير نصي)"""
    return filepath.suffix.lower() in BINARY_EXTENSIONS


def get_lang(filepath: Path) -> str:
    """الحصول على لغة الكود حسب امتداد الملف"""
    name = filepath.name.lower()
    if name == "dockerfile":
        return "dockerfile"
    if name == ".gitignore":
        return ""
    return LANG_MAP.get(filepath.suffix.lower(), "")


def build_tree(root: Path, output_filename: str) -> str:
    """بناء شجرة المجلدات والملفات كنص"""
    lines = []

    for dirpath, dirnames, filenames in os.walk(root):
        # تصفية المجلدات المستثناة
        dirnames[:] = sorted(
            [d for d in dirnames if not should_skip_dir(d)]
        )
        filenames = sorted(
            [f for f in filenames if not should_skip_file(f) and f != output_filename]
        )

        rel = os.path.relpath(dirpath, root)
        level = 0 if rel == "." else rel.count(os.sep) + 1

        if rel == ".":
            lines.append(f"{root.name}/")
        else:
            indent = "│   " * (level - 1) + "├── "
            lines.append(f"{indent}{os.path.basename(dirpath)}/")

        for i, fname in enumerate(filenames):
            is_last = i == len(filenames) - 1 and not dirnames
            connector = "└── " if is_last else "├── "
            indent = "│   " * level + connector
            lines.append(f"{indent}{fname}")

    return "\n".join(lines)


def read_file_safe(filepath: Path) -> str:
    """قراءة ملف بأمان مع معالجة الأخطاء"""
    encodings = ["utf-8", "utf-8-sig", "cp1256", "latin-1"]
    for enc in encodings:
        try:
            return filepath.read_text(encoding=enc)
        except (UnicodeDecodeError, ValueError):
            continue
    return "⚠️ تعذرت قراءة الملف (ترميز غير مدعوم)"


def generate_doc(root: Path, output_filename: str) -> str:
    """توليد محتوى التوثيق الكامل"""
    parts = []

    # العنوان
    parts.append(f"# الكود كاملاً — مشروع {root.name}\n")
    parts.append(f"**تاريخ التوليد**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    parts.append(f"**المسار**: `{root}`\n")
    parts.append("---\n")

    # شجرة الملفات
    parts.append("## شجرة المشروع\n")
    parts.append("```")
    parts.append(build_tree(root, output_filename))
    parts.append("```\n")
    parts.append("---\n")

    # المرور على كل ملف
    parts.append("## محتوى الملفات\n")

    current_dir = None

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            [d for d in dirnames if not should_skip_dir(d)]
        )
        filenames = sorted(
            [f for f in filenames if not should_skip_file(f) and f != output_filename]
        )

        if not filenames:
            continue

        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            dir_display = f"{root.name}/ (الجذر)"
        else:
            dir_display = rel_dir.replace(os.sep, "/") + "/"

        # عنوان المجلد
        if dir_display != current_dir:
            current_dir = dir_display
            parts.append(f"### 📁 {dir_display}\n")

        for fname in filenames:
            filepath = Path(dirpath) / fname
            rel_path = os.path.relpath(filepath, root).replace(os.sep, "/")

            parts.append(f"#### 📄 `{rel_path}`\n")

            if is_binary(filepath):
                size = filepath.stat().st_size
                if size < 1024:
                    size_str = f"{size} bytes"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                parts.append(f"*ملف ثنائي — الحجم: {size_str}*\n")
            else:
                lang = get_lang(filepath)
                content = read_file_safe(filepath)
                parts.append(f"```{lang}")
                parts.append(content)
                parts.append("```\n")

        parts.append("---\n")

    return "\n".join(parts)


def main():
    # المسار = مكان تواجد السكريبت
    script_dir = Path(__file__).resolve().parent
    output_filename = "الكود_كاملا.md"
    output_path = script_dir / output_filename

    print(f"📂 المسار: {script_dir}")
    print(f"📝 ملف المخرجات: {output_path}")

    if output_path.exists():
        print("🔄 الملف موجود — سيتم تحديثه...")
    else:
        print("🆕 إنشاء ملف جديد...")

    content = generate_doc(script_dir, output_filename)
    output_path.write_text(content, encoding="utf-8")

    file_count = content.count("#### 📄")
    print(f"✅ تم بنجاح! تم توثيق {file_count} ملف")
    print(f"📄 الملف: {output_path}")


if __name__ == "__main__":
    main()
