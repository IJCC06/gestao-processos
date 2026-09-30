# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

PROJECT_DIR = Path(SPECPATH)

datas = [
    (str(PROJECT_DIR / "processos" / "templates"), "processos/templates"),
    (str(PROJECT_DIR / "processos" / "static"), "processos/static"),
    (str(PROJECT_DIR / "migrations"), "migrations"),
    (str(PROJECT_DIR / "alembic.ini"), "."),
]

hiddenimports = [
    "flask_migrate",
    "flask_sqlalchemy",
    "flask_login",
    "flask_wtf",
    "sqlalchemy",
    "alembic",
    "dotenv",
    "requests",
    "logging.config",
    "processos.routes.auth",
    "processos.routes.clientes",
    "processos.routes.processos",
    "processos.routes.prazos",
    "processos.routes.notificacoes",
    "processos.routes.dashboard",
    "processos.routes.admin",
    "processos.routes.auditoria",
    "processos.routes.sistema",
    "processos.routes.setup",
]

a = Analysis(
    ["scripts/desktop_launcher.py"],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "unittest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GestaoProcessos",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="GestaoProcessos",
)
