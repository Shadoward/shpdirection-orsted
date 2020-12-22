# from https://chriskiehl.com/article/packaging-gooey-with-pyinstaller

import gooey
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_data_files # this is very helpful

gooey_root = os.path.dirname(gooey.__file__)
gooey_languages = Tree(os.path.join(gooey_root, 'languages'), prefix = 'gooey/languages')
gooey_images = Tree(os.path.join(gooey_root, 'images'), prefix = 'gooey/images')

hidden_imports = [
    'fiona',
    'shapely',
    'shapely.geometry',
    'pyproj',
    'rtree',
    'geopandas.datasets',
    'fiona._shim',
    'fiona.schema',
]

a = Analysis(['C:\\Users\\patrice.ponchant\\Documents\\GitHub\\shpdirection-orsted\\src\\shpdirectionorsted\\shpdirectionorsted.py'],
             pathex=['C:\\Users\\patrice.ponchant\\Documents\\GitHub\\hpdirection-orsted\\src\\shpdirectionorsted'],
             binaries=collect_dynamic_libs("rtree"),
             datas=collect_data_files('geopandas', subdir='datasets'),
             hiddenimports=hidden_imports,
             hookspath=None,
             runtime_hooks=None,
             )
pyz = PYZ(a.pure)

options = [('u', None, 'OPTION'), ('u', None, 'OPTION'), ('u', None, 'OPTION')]

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          options,
          gooey_languages, # Add them in to collected files
          gooey_images, # Same here.
          name='shpdirectionorsted',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          windowed=True,
          icon=os.path.join(gooey_root, 'images', 'program_icon.ico'))











from PyInstaller.utils.hooks import collect_dynamic_libs
block_cipher = None


a = Analysis(['C:\\Users\\patrice.ponchant\\Documents\\GitHub\\shpdirection-orsted\\src\\shpdirectionorsted\\shpdirectionorsted.py'],
             pathex=['C:\\Users\\patrice.ponchant\\Documents\\GitHub\\shpdirection-orsted\\installer'],
             binaries=collect_dynamic_libs("rtree"),
             datas=[],
             hiddenimports=['fiona._shim','fiona.schema'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)