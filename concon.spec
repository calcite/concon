# -*- mode: python -*-
a = Analysis(['concon.py'],
             pathex=['UCA_lib/usb_driver_lib/windows', 'UCA_lib/usb_driver_lib/linux', 'UCA_lib/usb_driver_lib', 'C:\\WORK\\HF\\SW\\concon'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

config_tree = Tree('config', prefix = 'config')
#Fixes one PyInstaller bug: http://stackoverflow.com/questions/19055089/pyinstaller-onefile-warning-pyconfig-h-when-importing-scipy-or-scipy-signal
a.datas = list({tuple(map(str.upper, t)) for t in a.datas})

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
		  config_tree,
          name='concon.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
