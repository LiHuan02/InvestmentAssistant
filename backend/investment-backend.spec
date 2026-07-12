"""
PyInstaller spec for Investment Assistant backend.
Produces a standalone executable that runs the FastAPI server.

Usage:
    cd backend
    uv run pyinstaller investment-backend.spec
"""

from pathlib import Path

block_cipher = None
backend_dir = Path(SPECPATH)
project_root = backend_dir.parent

a = Analysis(
    ['launcher.py'],
    pathex=[str(backend_dir), str(project_root)],
    binaries=[],
    datas=[
        (str(backend_dir / 'mcp_config.yaml'), '.'),
        (str(project_root / '.env.example'), '.'),
    ],
    hiddenimports=[
        # FastAPI / Uvicorn
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'websockets',
        'httptools',

        # LangChain ecosystem
        'langchain',
        'langchain_core',
        'langchain_openai',
        'langchain_tavily',
        'langgraph',
        'langchain_mcp_adapters',

        # Data libraries
        'akshare',
        'yfinance',
        'feedparser',
        'pandas',
        'numpy',

        # RAG
        'chromadb',
        'langchain_chroma',

        # Database
        'sqlite3',

        # Other
        'yaml',
        'pydantic_settings',
        'apscheduler',
        'apscheduler.schedulers.asyncio',
        'requests',
        'openai',
        'httpx',
        'curl_cffi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Build a single executable. Tauri externalBin embeds one file, so an onedir
# build would fail after the launcher is copied without its _internal folder.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='investment-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
