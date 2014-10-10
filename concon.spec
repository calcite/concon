# -*- mode: python -*-
a = Analysis(['concon.py'],
             pathex=['C:\\WORK\\HF\\SW\\concon'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='concon.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
