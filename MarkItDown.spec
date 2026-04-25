# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

EXCLUDES = [
    'torch', 'torchvision', 'torchaudio', 'timm', 'xformers',
    'sklearn', 'scikit-learn', 'skimage',
    'tensorflow', 'keras', 'onnx',
    'cv2', 'opencv-python', 'librosa',
    'bitsandbytes', 'diffusers', 'transformers', 'accelerate',
    'datasets', 'tokenizers', 'safetensors',
    'numba', 'llvmlite',
    'sqlalchemy', 'psycopg2', 'pymysql', 'MySQLdb',
    'yt_dlp', 'websockets', 'curl_cffi',
    'boto3', 'botocore',
    'google', 'google.cloud', 'google.auth',
    'azure', 'kubernetes',
    'selenium', 'playwright',
    'pytest', 'nose', 'mock',
    'setuptools', 'pip', 'wheel',
    'tkinter.test',
    'unittest', 'pydoc', 'doctest',
    'xmlrpc',
    'multiprocessing', 'concurrent',
    'asyncio', 'logging.handlers',
    'distutils', 'lib2to3',
    'IPython', 'jupyter',
    'notebook', 'ipykernel',
    'flask', 'django', 'fastapi', 'uvicorn', 'starlette',
    'aiohttp', 'h11', 'h2',
    'pydantic', 'pydantic_core', 'jsonschema',
    'opentelemetry', 'prometheus_client',
    'tornado', 'zmq',
    'win32com', 'pythoncom', 'pywintypes',
    'youtube_transcript_api',
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
    'gradio', 'pgserver',
    'modelscope', 'videocaptioner',
    'phonenumbers',
    'triton',
    'scipy',
    'matplotlib',
    'onnxruntime.transformers',
    'onnxruntime.tools',
    'onnxruntime.datasets',
    'onnxruntime.capi.training',
    'pandas.plotting',
    'pandas.io.sql',
    'pandas.io.parquet',
    'pandas.io.feather',
    'pandas.io.stata',
    'pandas.io.sas',
    'pandas.io.spss',
    'pandas.io.json._normalize',
    'pandas.tseries',
    'pandas.io.clipboard',
    'pandas.io.formats.style',
    'pyarrow',
    'reportlab.graphics',
    'reportlab.pdfbase.cidfonts',
    'reportlab.platypus',
    'lxml.doctestcompare',
    'lxml.html',
    'lxml.objectify',
    'speech_recognition',
    'pymupdf', 'fitz', 'mupdf',
    'tiktoken',
    'soundfile', '_soundfile_data',
    'pydub',
    'pycparser',
    'nacl',
    'rich',
    'anyio',
    'httpcore', 'httpx',
    'openai',
    'sniffio',
    'huggingface_hub',
    'langchain', 'langchain_core', 'langchain_community',
    'jiter',
    'beartype',
    'annotated_types',
    'pygments',
    'cffi',
    'argcomplete',
    'docutils',
    'fontTools',
    'rapidocr_onnxruntime',
    'shapely',
    'pkg_resources',
]

magika_datas = collect_data_files('magika')
pdfminer_hiddenimports = collect_submodules('pdfminer')
pdfplumber_hiddenimports = collect_submodules('pdfplumber')
pypdfium2_hiddenimports = collect_submodules('pypdfium2')
pdfminer_datas = collect_data_files('pdfminer')
pdfplumber_datas = collect_data_files('pdfplumber')
pypdfium2_datas = collect_data_files('pypdfium2')
cryptography_datas = collect_data_files('cryptography')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=magika_datas + pdfminer_datas + pdfplumber_datas + pypdfium2_datas + cryptography_datas,
    hiddenimports=[
        'markitdown',
        'markitdown._markitdown',
        'markitdown.converters',
        'markitdown.converters._docx_converter',
        'markitdown.converters._xlsx_converter',
        'markitdown.converters._pptx_converter',
        'markitdown.converters._pdf_converter',
        'markitdown.converters._html_converter',
        'markitdown.converters._csv_converter',
        'markitdown.converters._image_converter',
        'markitdown.converters._zip_converter',
        'markitdown.converters._plain_text_converter',
        'markitdown.converters._markdownify',
        'markitdown.converters._ipynb_converter',
        'tkinterdnd2',
        'requests',
        'mammoth',
        'openpyxl',
        'pptx',
        'xlrd',
        'olefile',
        'bs4',
        'defusedxml',
        'markdownify',
        'charset_normalizer',
        'magika',
        'onnxruntime',
        'onnxruntime.capi',
        'onnxruntime.capi._pybind_state',
        'cryptography',
        'cryptography.hazmat',
        'cryptography.hazmat.bindings',
        'cryptography.hazmat.bindings._rust',
        'cryptography.fernet',
        'pypdfium2',
        'pypdfium2.raw',
        'pypdfium2._helpers',
        'pypdfium2._helpers.document',
        'pypdfium2._helpers.page',
        'pypdfium2._helpers.textpage',
        'pypdfium2._helpers.bitmap',
        'pypdfium2._library_scope',
    ] + pdfminer_hiddenimports + pdfplumber_hiddenimports + pypdfium2_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

removed_binaries = []
for binary in a.binaries:
    name = binary[0].lower()
    if any(x in name for x in [
        'torch', 'triton', 'xformers', 'bitsandbytes',
        'pyqt5', 'pyqt6', 'pyside2', 'pyside6',
        'playwright', 'cv2', 'librosa',
        'onnxruntime\\tools', 'onnxruntime\\transformers',
        'onnxruntime\\datasets',
        'scipy.libs',
        'pymupdf', 'mupdfcpp', '_mupdf',
        'speech_recognition', 'pocketsphinx',
        'flac-linux', 'flac-mac', 'flac-win32',
        'tiktoken',
        '_soundfile_data', 'libsndfile',
        'pydantic_core',
        'jiter',
        'fonttools',
    ]):
        removed_binaries.append(binary)

for b in removed_binaries:
    a.binaries.remove(b)

removed_datas = []
for data in a.datas:
    name = data[0].lower() if isinstance(data[0], str) else ''
    dest = data[1].lower() if len(data) > 1 and isinstance(data[1], str) else ''
    if any(x in name or x in dest for x in [
        'torch', 'triton', 'pyqt5', 'pyqt6',
        'playwright', 'cv2', 'scipy.libs',
        'onnxruntime\\tools', 'onnxruntime\\transformers',
        'onnxruntime\\datasets',
        'matplotlib', 'sympy', 'gradio',
        'pymupdf', 'mupdf',
        'speech_recognition', 'pocketsphinx',
        'flac-linux', 'flac-mac', 'flac-win32',
        'tiktoken',
        '_soundfile_data', 'libsndfile',
        'pydantic',
        'jiter',
        'fonttools',
        'rich',
        'pygments',
    ]):
        removed_datas.append(data)

for d in removed_datas:
    a.datas.remove(d)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MarkItDown',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
