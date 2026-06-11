from __future__ import annotations

import ast
import fnmatch
import json
import uuid
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from .config import Settings
from .storage import create_audit_event, utc_now


CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".css",
    ".html",
    ".md",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".ps1",
    ".sh",
    ".sql",
}
DEFAULT_EXCLUDES = (
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".cache",
    "data",
    "logs",
)


@dataclass(frozen=True)
class CodeGraphStatus:
    status: str
    detail: str
    root: str
    repo_count: int
    scan_count: int
    latest_scan_id: str
    memory_boundary: str


@dataclass(frozen=True)
class CodeGraphRepo:
    id: str
    name: str
    root_path: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CodeGraphFile:
    id: str
    repo_id: str
    path: str
    relative_path: str
    language: str
    size_bytes: int
    sha256: str
    symbol_count: int
    import_count: int


@dataclass(frozen=True)
class CodeGraphSymbol:
    id: str
    repo_id: str
    file_id: str
    name: str
    qualname: str
    kind: str
    language: str
    path: str
    line_start: int
    line_end: int
    parent: str


@dataclass(frozen=True)
class CodeGraphImport:
    id: str
    repo_id: str
    file_id: str
    source_path: str
    module: str
    name: str
    line: int


@dataclass(frozen=True)
class CodeGraphScan:
    id: str
    repo_id: str
    status: str
    file_count: int
    symbol_count: int
    import_count: int
    skipped_count: int
    detail: str
    created_at: str


def as_payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, dict):
        return value
    return dict(value)


def codegraph_status(settings: Settings) -> CodeGraphStatus:
    repos = list_codegraph_repos(settings)
    scans = _read_jsonl(_scans_path(settings), limit=200)
    latest = scans[-1] if scans else {}
    return CodeGraphStatus(
        status="ready",
        detail="Code structure index is local, separate from long-term memory.",
        root=str(settings.codegraph_root),
        repo_count=len(repos),
        scan_count=len(scans),
        latest_scan_id=str(latest.get("id", "")),
        memory_boundary="codegraph indexes source structure only; it does not write long-term memory",
    )


def register_codegraph_repo(settings: Settings, path: str, name: str = "") -> CodeGraphRepo:
    root = Path(path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"repo path does not exist or is not a directory: {path}")
    existing = next((repo for repo in list_codegraph_repos(settings, limit=1000) if Path(str(repo["root_path"])).resolve() == root), None)
    if existing:
        return CodeGraphRepo(**existing)
    now = utc_now()
    repo = CodeGraphRepo(
        id=str(uuid.uuid4()),
        name=name.strip() or root.name,
        root_path=str(root),
        status="registered",
        created_at=now,
        updated_at=now,
    )
    _append_jsonl(_repos_path(settings), asdict(repo))
    create_audit_event(
        settings.data_dir,
        "codegraph.repo_registered",
        resource_type="codegraph_repo",
        resource_ref=repo.id,
        payload={"name": repo.name, "root_path": repo.root_path, "memory_boundary": "separate"},
    )
    return repo


def list_codegraph_repos(settings: Settings, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(_repos_path(settings), limit=limit)


def scan_codegraph_repo(settings: Settings, repo_id: str) -> dict[str, Any]:
    repo = _find_repo(settings, repo_id)
    if repo is None:
        return {"status": "not_found", "detail": f"codegraph repo not found: {repo_id}", "scan": None}
    root = Path(str(repo["root_path"])).resolve()
    if not root.exists() or not root.is_dir():
        return {"status": "missing_source", "detail": f"repo root is missing: {root}", "scan": None}

    files: list[CodeGraphFile] = []
    symbols: list[CodeGraphSymbol] = []
    imports: list[CodeGraphImport] = []
    skipped_count = 0
    for path in _iter_code_files(root):
        if path.stat().st_size > settings.codegraph_max_file_bytes:
            skipped_count += 1
            continue
        parsed = _scan_file(root, repo_id=str(repo["id"]), path=path)
        files.append(parsed["file"])
        symbols.extend(parsed["symbols"])
        imports.extend(parsed["imports"])

    scan = CodeGraphScan(
        id=str(uuid.uuid4()),
        repo_id=str(repo["id"]),
        status="completed",
        file_count=len(files),
        symbol_count=len(symbols),
        import_count=len(imports),
        skipped_count=skipped_count,
        detail=f"indexed {len(files)} files, {len(symbols)} symbols, {len(imports)} imports",
        created_at=utc_now(),
    )
    _write_jsonl(_files_path(settings, scan.id), [asdict(item) for item in files])
    _write_jsonl(_symbols_path(settings, scan.id), [asdict(item) for item in symbols])
    _write_jsonl(_imports_path(settings, scan.id), [asdict(item) for item in imports])
    _append_jsonl(_scans_path(settings), asdict(scan))
    create_audit_event(
        settings.data_dir,
        "codegraph.repo_scanned",
        resource_type="codegraph_repo",
        resource_ref=str(repo["id"]),
        payload={"scan_id": scan.id, "file_count": scan.file_count, "symbol_count": scan.symbol_count, "import_count": scan.import_count},
    )
    return {"status": scan.status, "detail": scan.detail, "scan": asdict(scan)}


def codegraph_overview(settings: Settings, repo_id: str = "") -> dict[str, Any]:
    scan = _latest_scan(settings, repo_id=repo_id)
    repos = list_codegraph_repos(settings, limit=1000)
    if scan is None:
        return {"status": "empty", "detail": "No CodeGraph scans recorded yet.", "repos": repos, "scan": None, "files": [], "symbols": [], "imports": []}
    files = _read_jsonl(_files_path(settings, str(scan["id"])), limit=10000)
    symbols = _read_jsonl(_symbols_path(settings, str(scan["id"])), limit=10000)
    imports = _read_jsonl(_imports_path(settings, str(scan["id"])), limit=10000)
    languages: dict[str, int] = {}
    for file in files:
        language = str(file.get("language", "other"))
        languages[language] = languages.get(language, 0) + 1
    return {
        "status": "ready",
        "detail": "CodeGraph overview is built from local source structure index.",
        "repos": repos,
        "scan": scan,
        "counts": {"files": len(files), "symbols": len(symbols), "imports": len(imports), "languages": languages},
        "top_files": sorted(files, key=lambda item: int(item.get("symbol_count", 0)), reverse=True)[:20],
        "top_symbols": symbols[:50],
    }


def query_codegraph(settings: Settings, query: str, repo_id: str = "", limit: int = 20) -> dict[str, Any]:
    scan = _latest_scan(settings, repo_id=repo_id)
    if scan is None:
        return {"status": "empty", "detail": "No CodeGraph scans recorded yet.", "query": query, "results": []}
    needle = query.strip().lower()
    if not needle:
        return {"status": "invalid_request", "detail": "query is required", "query": query, "results": []}
    files = _read_jsonl(_files_path(settings, str(scan["id"])), limit=10000)
    symbols = _read_jsonl(_symbols_path(settings, str(scan["id"])), limit=10000)
    results: list[dict[str, Any]] = []
    for symbol in symbols:
        haystack = " ".join(str(symbol.get(key, "")) for key in ("name", "qualname", "kind", "path")).lower()
        if needle in haystack:
            results.append({"type": "symbol", "score": 2, **symbol})
    for file in files:
        haystack = " ".join(str(file.get(key, "")) for key in ("relative_path", "language")).lower()
        if needle in haystack:
            results.append({"type": "file", "score": 1, **file})
    return {"status": "completed", "detail": f"{len(results[:limit])} CodeGraph results", "query": query, "scan_id": scan["id"], "results": results[:limit]}


def codegraph_impact(settings: Settings, path: str, repo_id: str = "") -> dict[str, Any]:
    scan = _latest_scan(settings, repo_id=repo_id)
    if scan is None:
        return {"status": "empty", "detail": "No CodeGraph scans recorded yet.", "path": path, "imports": [], "symbols": []}
    files = _read_jsonl(_files_path(settings, str(scan["id"])), limit=10000)
    symbols = _read_jsonl(_symbols_path(settings, str(scan["id"])), limit=10000)
    imports = _read_jsonl(_imports_path(settings, str(scan["id"])), limit=10000)
    target = path.replace("\\", "/").lower()
    matching_files = [file for file in files if target in str(file.get("relative_path", "")).replace("\\", "/").lower()]
    matching_paths = {str(file.get("relative_path", "")) for file in matching_files}
    file_symbols = [symbol for symbol in symbols if str(symbol.get("path", "")) in matching_paths]
    imported_by = [
        item
        for item in imports
        if any(_module_matches_path(str(item.get("module", "")), match) for match in matching_paths)
    ]
    return {
        "status": "completed" if matching_files else "not_found",
        "detail": f"{len(matching_files)} files, {len(file_symbols)} symbols, {len(imported_by)} import references",
        "path": path,
        "files": matching_files,
        "symbols": file_symbols,
        "imported_by": imported_by,
    }


def _scan_file(root: Path, repo_id: str, path: Path) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    content = path.read_bytes()
    file_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{repo_id}:{relative}"))
    language = _language(path)
    parsed_symbols: list[CodeGraphSymbol] = []
    parsed_imports: list[CodeGraphImport] = []
    if path.suffix == ".py":
        parsed_symbols, parsed_imports = _scan_python(repo_id, file_id, relative, content.decode("utf-8", errors="ignore"))
    file = CodeGraphFile(
        id=file_id,
        repo_id=repo_id,
        path=str(path.resolve()),
        relative_path=relative,
        language=language,
        size_bytes=len(content),
        sha256=sha256(content).hexdigest(),
        symbol_count=len(parsed_symbols),
        import_count=len(parsed_imports),
    )
    return {"file": file, "symbols": parsed_symbols, "imports": parsed_imports}


def _scan_python(repo_id: str, file_id: str, path: str, source: str) -> tuple[list[CodeGraphSymbol], list[CodeGraphImport]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return (), ()
    symbols: list[CodeGraphSymbol] = []
    imports: list[CodeGraphImport] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> Any:
            self._symbol(node, "class")
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
            self._symbol(node, "function" if not self.stack else "method")
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
            self._symbol(node, "async_function" if not self.stack else "async_method")
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_Import(self, node: ast.Import) -> Any:
            for alias in node.names:
                imports.append(_import(repo_id, file_id, path, alias.name, alias.asname or alias.name, node.lineno))

        def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
            module = "." * int(node.level or 0) + (node.module or "")
            for alias in node.names:
                imports.append(_import(repo_id, file_id, path, module, alias.name, node.lineno))

        def _symbol(self, node: ast.AST, kind: str) -> None:
            name = getattr(node, "name", "")
            parent = ".".join(self.stack)
            qualname = ".".join([*self.stack, name]) if self.stack else name
            symbols.append(
                CodeGraphSymbol(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{repo_id}:{path}:{qualname}:{getattr(node, 'lineno', 0)}")),
                    repo_id=repo_id,
                    file_id=file_id,
                    name=name,
                    qualname=qualname,
                    kind=kind,
                    language="python",
                    path=path,
                    line_start=int(getattr(node, "lineno", 0) or 0),
                    line_end=int(getattr(node, "end_lineno", getattr(node, "lineno", 0)) or 0),
                    parent=parent,
                )
            )

    Visitor().visit(tree)
    return symbols, imports


def _import(repo_id: str, file_id: str, path: str, module: str, name: str, line: int) -> CodeGraphImport:
    return CodeGraphImport(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{repo_id}:{path}:{module}:{name}:{line}")),
        repo_id=repo_id,
        file_id=file_id,
        source_path=path,
        module=module,
        name=name,
        line=line,
    )


def _iter_code_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(root).parts)
        if parts.intersection(DEFAULT_EXCLUDES):
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        yield path


def _language(path: Path) -> str:
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".vue": "vue",
        ".css": "css",
        ".html": "html",
        ".md": "markdown",
        ".json": "json",
        ".toml": "toml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".ps1": "powershell",
        ".sh": "shell",
        ".sql": "sql",
    }
    return mapping.get(path.suffix.lower(), "other")


def _module_matches_path(module: str, file: str) -> bool:
    normalized_module = module.strip(".").replace(".", "/").lower()
    normalized_file = file.replace("\\", "/").removesuffix(".py").lower()
    return bool(normalized_module and (normalized_module in normalized_file or normalized_file.endswith(normalized_module)))


def _find_repo(settings: Settings, repo_id: str) -> dict[str, Any] | None:
    repos = list_codegraph_repos(settings, limit=1000)
    if not repo_id and repos:
        return repos[-1]
    return next((repo for repo in repos if repo.get("id") == repo_id or repo.get("name") == repo_id), None)


def _latest_scan(settings: Settings, repo_id: str = "") -> dict[str, Any] | None:
    scans = _read_jsonl(_scans_path(settings), limit=1000)
    if repo_id:
        scans = [scan for scan in scans if scan.get("repo_id") == repo_id]
    return scans[-1] if scans else None


def _repos_path(settings: Settings) -> Path:
    return settings.codegraph_root / "repos.jsonl"


def _scans_path(settings: Settings) -> Path:
    return settings.codegraph_root / "scans.jsonl"


def _files_path(settings: Settings, scan_id: str) -> Path:
    return settings.codegraph_root / "scans" / scan_id / "files.jsonl"


def _symbols_path(settings: Settings, scan_id: str) -> Path:
    return settings.codegraph_root / "scans" / scan_id / "symbols.jsonl"


def _imports_path(settings: Settings, scan_id: str) -> Path:
    return settings.codegraph_root / "scans" / scan_id / "imports.jsonl"


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _read_jsonl(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows[-limit:]
