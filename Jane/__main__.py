import sys, os, wx, importlib
from configparser import ConfigParser, ExtendedInterpolation, NoSectionError
from argparse import ArgumentParser
from pathlib import Path
from MainWindow  import MainWindow

class Application(wx.App):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		__builtins__.__dict__['app'] = self
		executablePath = Path(sys.argv[0])
		self.name = app.name = executablePath.stem
		self.version = '0.0'
		self.dir = executablePath.parent.resolve()
		sys.path.append(os.path.dirname(sys.argv[0]))
		self.loadCmdlineArgs()
		self.loadConfigs()
		self.loadTranslations()
		self.win = MainWindow(parent=None, title=app.name)
		__builtins__.__dict__['win'] = self.win
		self.win.initUI()
		self.loadPlugins()
		self.openStdin()
		#self.openStdout(sys.stdout, 'stdout')
		#self.openStdout(sys.stderr, 'stderr')
		win.openDocuments(self.cmdargs.files)
		if not win.documents: win.newDocument()
		win.Show(True)
		self.SetTopWindow(win)
		self.MainLoop()
	
	def loadCmdlineArgs(self):
		parser = ArgumentParser()
		parser.add_argument('files', nargs='*')
		self.cmdargs = parser.parse_args()

	def loadConfigs(self):
		self.configDir = configDir = Path(wx.StandardPaths.Get().GetUserConfigDir(), app.name)
		self.config = ConfigParser(default_section='global', allow_no_value=True, empty_lines_in_values=False, strict=True, interpolation=ExtendedInterpolation())
		self.config.optionxform = str
		self.config.read((
		str(Path(configDir, app.name+'.ini')),
			str(Path(app.dir, app.name+'.ini'))
		))
	
	def loadConfig(self, mod):
		self.config.read((
		str(Path(self.configDir, mod+'.ini')),
			str(Path(app.dir, mod+'.ini')),
			str(Path(app.dir, 'plugins', mod+'.ini'))
		))
	
	def loadTranslations(self):
		self.lang = lang = wx.Locale.GetLanguageCanonicalName(wx.Locale.GetSystemLanguage())
		locale = wx.Locale(language=wx.Locale.GetSystemLanguage())
		self.translationsrep = translations = ConfigParser(default_section='default', empty_lines_in_values=False, strict=True, interpolation=ExtendedInterpolation())
		translations.optionxform = str
		translations.read((
			str(Path(app.dir, app.name+'.lng')),
			str(Path(app.dir, app.name +'_' + lang[0:2] + '.lng')),
			str(Path(app.dir, app.name +'_' + lang + '.lng'))
		))
		if translations.has_section(lang): self.translations = translations[lang]
		elif translations.has_section(lang[0:2]): self.translations = translations[lang[0:2]]
		else: self.translations = translations.defaults()
		__builtins__.__dict__['translate'] = self.translate #wx.GetTranslation 
	
	def loadTranslation(self, mod):
		self.translationsrep.read((
			str(Path(app.dir, 'plugins', mod+'.lng')),
			str(Path(app.dir, 'plugins', mod +'_' + self.lang[0:2] + '.lng')),
			str(Path(app.dir, 'plugins', mod +'_' + self.lang + '.lng')),
			str(Path(app.dir, 'plugins', mod, mod+'.lng')),
			str(Path(app.dir, 'plugins', mod, mod +'_' + self.lang[0:2] + '.lng')),
			str(Path(app.dir, 'plugins', mod, mod +'_' + self.lang + '.lng'))
		))
	
	def loadPlugins(self):
		plugins = ()
		try: plugins = self.config.options('plugins')
		except NoSectionError: pass
		path = app.config.get('plugins', 'path', fallback='')
		if path:
			approot = os.path.dirname(sys.argv[0])
			for p in path.split(os.path.pathsep):
				if not p.startswith(os.path.sep) and p[1:3]!=':\\': p = Path(approot, p).resolve()
				sys.path.append(str(p))
		for plugin in plugins:
			if plugin=='path': continue
			try: importlib.import_module(plugin)
			except Exception as e: print(e)
	
	def openStdin(self):
		if not sys.stdin or sys.stdin.isatty(): return
		data = None
		try: 
			with open(sys.stdin.fileno(), 'rb') as stdin:
				data = stdin.read()
		except OSError: raise #pass
		if data:
			win.newDocument(name=translate('stdin'), file=None, data=data) .setData(data)
	
	def openStdout (self, stdout, name):
		if not stdout or sys.stdout.isatty(): return
		doc = win.newDocument(name=translate(name)) 
		doc.close = writeOnClose(doc, stdout.fileno())
	
	def translate (self, key, defaultValue=None):
		return self.translations.get(key, defaultValue or key) .replace(r'\n', '\n')
	
	def SetClipboardText (self, text):
		cb = wx.Clipboard.Get()
		if not cb or not cb.Open(): return False
		try:
			tdo = wx.TextDataObject(text)
			result = cb.SetData(tdo)
			cb.Flush()
			return result
		finally:
			cb.Close()
	
	def SetClipboardFiles (self, files):
		cb = wx.Clipboard.Get()
		if not cb or not cb.Open(): return False
		try:
			fdo = wx.FileDataObject()
			for f in files: fdo.AddFile(str(f))
			result = cb.SetData(fdo)
			cb.Flush()
			return result
		finally:
			cb.Close()
	
	def GetClipboardText (self):
		cb = wx.Clipboard.Get()
		if not cb or not cb.Open(): return None
		try:
			tdo = wx.TextDataObject()
			return tdo.GetText() if cb.GetData(tdo) else None
		finally:
			cb.Close()
	
	def GetClipboardFiles (self):
		cb = wx.Clipboard.Get()
		if not cb or not cb.Open(): return None
		try:
			fdo = wx.FileDataObject()
			return [Path(f) for f in fdo.GetFilenames()] if cb.GetData(fdo) else None
		finally:
			cb.Close()
	
def writeOnClose (doc, fileno):
	def close():
		try:
			with open(fileno, 'wb') as fd:
				fd.write(doc.getData())
			return True
		except OSError as e: print(e); return False
	return close

app = Application()