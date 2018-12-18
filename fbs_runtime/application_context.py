from fbs_runtime import _state
from fbs_runtime._resource_locator import ResourceLocator, \
    DevelopmentResourceLocator
from fbs_runtime._signal import SignalWakeupHandler
from fbs_runtime.excepthook import Excepthook
from fbs_runtime.platform import is_windows, is_mac
from functools import lru_cache
from os.path import join, pardir, dirname

try:
    from PyQt5.QtGui import QIcon
except ImportError:
    from PySide2.QtGui import QIcon
try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PySide2.QtWidgets import QApplication

import sys

def cached_property(getter):
    """
    A cached Python @property. You use it in conjunction with ApplicationContext
    below to instantiate the components that comprise your application. For more
    information, please consult the Manual:
        https://build-system.fman.io/manual/#cached_property
    """
    return property(lru_cache()(getter))

class ApplicationContext:
    """
    The main point of contact between your application and fbs. For information
    on how to use it, please see the Manual:
        https://build-system.fman.io/manual/#your-python-code
    """
    def __init__(self):
        self.excepthook.install()
        # Many Qt classes require a QApplication to have been instantiated.
        # Do this here, before everything else, to achieve this:
        self.app
        # We don't build as a console app on Windows, so no point in installing
        # the SIGINT handler:
        if not is_windows():
            self._signal_wakeup_handler = SignalWakeupHandler(self.app)
            self._signal_wakeup_handler.install()
        if self.app_icon:
            self.app.setWindowIcon(self.app_icon)
    @cached_property
    def app(self):
        """
        The global Qt QApplication object for your app. Feel free to overwrite
        this property, eg. if you wish to use your own subclass of QApplication.
        An example of this is given in the Manual.
        """
        return QApplication(sys.argv)
    @cached_property
    def app_icon(self):
        """
        The app icon. Not available on Mac because app icons are handled by the
        OS there.
        """
        if not is_mac():
            return QIcon(self.get_resource('Icon.ico'))
    @cached_property
    def excepthook(self):
        """
        We use a custom excepthook because PyQt5/PySide2 hide some stack trace
        entries - see the documentation of fbs_runtime.excepthook.Excepthook.
        You can use a different implementation by overwriting this property.
        Just return an object with a .install() method.
        """
        return Excepthook()
    def get_resource(self, *rel_path):
        """
        Return the absolute path to the data file with the given name or
        (relative) path. When running from source, searches src/main/resources.
        Otherwise, searches your app's installation directory. If no file with
        the given name or path exists, a FileNotFoundError is raised.
        """
        return self._resource_locator.locate(*rel_path)
    @cached_property
    def _resource_locator(self):
        if is_frozen():
            executable_dir = dirname(sys.executable)
            if is_mac():
                resources_dir = join(executable_dir, pardir, 'Resources')
            else:
                resources_dir = executable_dir
            return ResourceLocator([resources_dir])
        else:
            return DevelopmentResourceLocator(self.__class__)
    def run(self):
        raise NotImplementedError()

def is_frozen():
    """
    Return True if running from the frozen (i.e. compiled form) of your app, or
    False when running from source.
    """
    return getattr(sys, 'frozen', False)

def get_application_context(DevelopmentAppCtxtCls, FrozenAppCtxtCls=None):
    if FrozenAppCtxtCls is None:
        FrozenAppCtxtCls = DevelopmentAppCtxtCls
    if _state.APPLICATION_CONTEXT is None:
        _state.APPLICATION_CONTEXT = \
            FrozenAppCtxtCls() if is_frozen() else DevelopmentAppCtxtCls()
    return _state.APPLICATION_CONTEXT