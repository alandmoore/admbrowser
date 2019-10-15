#!/usr/bin/python
"""
Thisq is the main script for ADMBrowser, a kiosk-oriented web browser
Written by Alan D Moore, http://www.alandmoore.com
Released under the GNU GPL v3
"""

# QT Binding imports
# Standard library imports
import sys
import os
import argparse
import re
import datetime

import yaml

from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtWebEngineWidgets as qtwe

from . import messages as msg
from .admwebview import AdmWebView
from .admwebpage import AdmWebPage
from .admnavbutton import AdmNavButton
from .inactivity_filter import InactivityFilter
from .config import Config
from . import resources

class MainWindow(qtw.QMainWindow):

    """This is the main application window class

    it defines the GUI window for the browser
    """

    def __init__(self, config, parent=None, debug=None):
        """Construct a MainWindow Object."""
        super().__init__(parent)

        self.debug = debug or (lambda x: None)
        self.config = config

        self.setWindowTitle("Browser")

        # self.popup will hold a reference to the popup window
        # if it gets opened
        self.popup = None

        # Stylesheet support
        if self.config.stylesheet:
            try:
                with open(self.config.stylesheet) as handle:
                    self.setStyleSheet(handle.read())
            except IOError as e:
                self.debug(
                    f'Problem loading stylesheet file "{self.config.stylesheet}": {e} '
                    '\nusing default style.'
                )
        self.setObjectName("global")

        # Set proxy server environment variable before creating web views
        if self.config.proxy_server:
            os.environ["http_proxy"] = self.config.proxy_server
            os.environ["https_proxy"] = self.config.proxy_server

        # If the whitelist is activated, add the bookmarks and start_url
        if self.config.whitelist:
            # we can just specify whitelist = True,
            # which should whitelist just the start_url and bookmark urls.
            whitelist = self.config.whitelist
            if not isinstance(whitelist, list):
                whitelist = []
            start_host = qtc.QUrl(self.config.start_url).host()
            whitelist.append(start_host)
            for bookmark in self.config.bookmarks.values():
                bookmark_host = qtc.QUrl(bookmark.get("url")).host()
                whitelist.append(bookmark_host)
                self.config.whitelist = set(whitelist)  # uniquify and optimize
            self.debug(f"Generated whitelist: {whitelist}")

        # create the web engine profile
        self.create_webprofile()

        # Now construct the UI
        self.build_ui()

    # ## END OF CONSTRUCTOR ## #

    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None,
                     checkable=False, signal="triggered"):
        """Return a QAction given a number of common QAction attributes

        Just a shortcut function Originally borrowed from
        'Rapid GUI Development with PyQT' by Mark Summerset
        """
        action = qtw.QAction(text, self)
        if icon is not None:
            action.setIcon(qtg.QIcon.fromTheme(
                icon, qtg.QIcon(f":/navigation/{icon}.png")
            ))
        if shortcut is not None and not shortcut.isEmpty():
            action.setShortcut(shortcut)
            tip += f" ({shortcut.toString()})"
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.__getattr__(signal).connect(slot)
        if checkable:
            action.setCheckable()
        return action

    def create_webprofile(self):
        """Create a webengineprofile to use in all views."""

        # create private/nonprivate webprofile per settings
        webprofile = (
            qtwe.QWebEngineProfile()
            if self.config.privacy_mode
            else qtwe.QWebEngineProfile.defaultProfile()
        )
        self.debug(f"Browser session is private: {webprofile.isOffTheRecord()}")

        # set the user agent string
        if self.config.user_agent:
            webprofile.setHttpUserAgent(self.config.user_agent)

        # use webprofile
        self.webprofile = webprofile

    def build_ui(self):
        """Set up the user interface for the main window.

        Unlike the constructor, this method is re-run
        whenever the browser is "reset" by the user.
        """

        self.debug("build_ui")
        inactivity_timeout = self.config.timeout
        quit_button_tooltip = (
            msg.QUIT_TOOLTIP
            if self.config.quit_button_mode == 'close'
            else msg.RESET_TOOLTIP
        )
        qb_mode_callbacks = {
            'close': self.close,
            'reset': self.reset_browser
        }
        to_mode_callbacks = {
            'close': self.close,
            'reset': self.reset_browser,
            'screensaver': self.screensaver
        }
        self.screensaver_active = False

        # ##Start GUI configuration## #
        self.browser_window = AdmWebView(
            self.config,
            webprofile=self.webprofile,
            debug=self.debug
        )
        self.browser_window.setObjectName("web_content")
        self.setCentralWidget(self.browser_window)
        self.browser_window.error.connect(self.show_error)

        # Icon theme setting
        qtg.QIcon.setThemeName(self.config.icon_theme)

        self.setCentralWidget(self.browser_window)
        self.debug(f"loading {self.config.start_url}")
        self.browser_window.setUrl(qtc.QUrl(self.config.start_url))

        # Window size settings
        window_size = self.config.window_size.lower()
        if window_size == 'full':
            self.showFullScreen()
        elif window_size == 'max':
            self.showMaximized()
        elif window_size:
            size = re.match(r"(\d+)x(\d+)", window_size)
            if size:
                width, height = size.groups()
                self.setFixedSize(int(width), int(height))
            else:
                self.debug(f'Ignoring invalid window size "{self.config.window_size}"')

        # Set up the top navigation bar if it's configured to exist
        if self.config.navigation:
            self.navigation_bar = qtw.QToolBar(
                "Navigation",
                objectName="navigation",
                movable=False,
                floatable=False
            )
            self.addToolBar(qtc.Qt.TopToolBarArea, self.navigation_bar)

            #  Standard navigation tools
            self.nav_items = {
                "back": self.browser_window.pageAction(AdmWebPage.Back),
                "forward": self.browser_window.pageAction(AdmWebPage.Forward),
                "refresh": self.browser_window.pageAction(AdmWebPage.Reload),
                "stop": self.browser_window.pageAction(AdmWebPage.Stop),
                "quit": self.createAction(
                    self.config.quit_button_text,
                    qb_mode_callbacks.get(
                        self.config.quit_button_mode,
                        self.reset_browser
                    ),
                    qtg.QKeySequence("Alt+F"),
                    None,
                    quit_button_tooltip
                ),
                "zoom_in": self.createAction(
                    "Zoom In",
                    self.zoom_in,
                    qtg.QKeySequence("Alt++"),
                    "zoom-in",
                    "Increase the size of the text and images on the page"
                ),
                "zoom_out": self.createAction(
                    "Zoom Out",
                    self.zoom_out,
                    qtg.QKeySequence("Alt+-"),
                    "zoom-out",
                    "Decrease the size of text and images on the page"
                )
            }
            # Set icons for browser actions from theme
            for action_name in ('back', 'forward', 'refresh', 'stop'):
                action = self.nav_items[action_name]
                icon = qtg.QIcon.fromTheme(
                    action_name,
                    qtg.QIcon(f":/navigation/{action_name}.png")
                )
                action.setIcon(icon)
            if self.config.allow_printing:
                self.nav_items["print"] = self.createAction(
                    "Print",
                    self.browser_window.print_webpage,
                    qtg.QKeySequence("Ctrl+p"),
                    "document-print",
                    "Print this page"
                )

            # Add all the actions to the navigation bar.
            for item in self.config.navigation_layout:
                if item == "separator":
                    self.navigation_bar.addSeparator()
                elif item == "spacer":
                    # an expanding spacer.
                    spacer = qtw.QWidget()
                    spacer.setSizePolicy(
                        qtw.QSizePolicy.Expanding,
                        qtw.QSizePolicy.Preferred
                    )
                    self.navigation_bar.addWidget(spacer)
                elif item == "bookmarks":
                    # Insert bookmarks buttons here.
                    self.bookmark_buttons = []
                    for bookmark in self.config.bookmarks.items():
                        self.debug(f"Bookmark:\n {bookmark}")
                        # bookmark name will use the "name" attribute,
                        # if present, or else just the key:
                        bookmark_name = bookmark[1].get("name") or bookmark[0]
                        button = AdmNavButton(
                            text=bookmark_name,
                            url=bookmark[1].get('url'),
                            shortcut=qtg.QKeySequence.mnemonic(bookmark_name),
                            toolTip=bookmark[1].get('description'),
                            objectName='navigation_button'
                        )
                        button.clicked.connect(self.browser_window.load)
                        self.navigation_bar.addWidget(button)
                else:
                    action = self.nav_items.get(item, None)
                    if action:
                        self.navigation_bar.addAction(action)
                        (self.navigation_bar.widgetForAction(action)
                         .setObjectName("navigation_button"))

            # This removes the ability to toggle off the navigation bar:
            self.nav_toggle = self.navigation_bar.toggleViewAction()
            self.nav_toggle.setVisible(False)
            # End "if show_navigation is True" block

        # set hidden quit action
        # For reasons I haven't adequately ascertained,
        # this shortcut fails now and then claiming
        # "Ambiguous shortcut overload".
        # No idea why, as it isn't consistent.
        self.really_quit = self.createAction(
            "",
            self.close,
            qtg.QKeySequence("Ctrl+Alt+Q"),
            None,
            ""
        )
        self.addAction(self.really_quit)

        # Call a reset function after timeout
        if inactivity_timeout != 0:
            self.event_filter = InactivityFilter(inactivity_timeout)
            qtc.QCoreApplication.instance().installEventFilter(self.event_filter)
            self.browser_window.page().installEventFilter(self.event_filter)
            self.event_filter.timeout.connect(
                to_mode_callbacks.get(
                    self.config.timeout_mode,
                    self.reset_browser)
            )
        else:
            self.event_filter = None

        # ##END OF UI SETUP## #

    def screensaver(self):
        """Enter "screensaver" mode

        This method puts the browser in screensaver mode, where a URL
        is displayed while the browser is idle.  Activity causes the browser to
        return to the home screen.
        """
        self.debug("screensaver started")
        self.screensaver_active = True
        if self.popup:
            self.popup.close()
        if self.config.navigation:
            self.navigation_bar.hide()
        self.browser_window.setZoomFactor(self.config.zoom_factor)
        self.browser_window.load(qtc.QUrl(self.config.screensaver_url))
        self.event_filter.timeout.disconnect()
        self.event_filter.activity.connect(self.reset_browser)

    def reset_browser(self):
        """Clear the history and reset the UI.

        Called whenever the inactivity filter times out,
        or when the user clicks the "finished" button in
        'reset' mode.
        """
        # Clear out the memory cache
        # QWebEngineSettings.clearMemoryCaches()
        self.browser_window.history().clear()
        # self.navigation_bar.clear() doesn't do its job,
        # so remove the toolbar first, then rebuild the UI.
        self.debug("RESET BROWSER")
        if self.event_filter:
            self.event_filter.blockSignals(True)
        if self.screensaver_active is True:
            self.screensaver_active = False
            self.event_filter.activity.disconnect()
        if self.event_filter:
            self.event_filter.blockSignals(False)
        if hasattr(self, "navigation_bar"):
            self.removeToolBar(self.navigation_bar)
        self.build_ui()

    def zoom_in(self):
        """Zoom in action callback.

        Note that we cap zooming in at a factor of 3x.
        """
        if self.browser_window.zoomFactor() < 3.0:
            self.browser_window.setZoomFactor(
                self.browser_window.zoomFactor() + 0.1
            )
            self.nav_items["zoom_out"].setEnabled(True)
        else:
            self.nav_items["zoom_in"].setEnabled(False)

    def zoom_out(self):
        """Zoom out action callback.

        Note that we cap zooming out at 0.1x.
        """
        if self.browser_window.zoomFactor() > 0.1:
            self.browser_window.setZoomFactor(
                self.browser_window.zoomFactor() - 0.1
            )
            self.nav_items["zoom_in"].setEnabled(True)
        else:
            self.nav_items["zoom_out"].setEnabled(False)


    def show_error(self, error):
        qtw.QMessageBox.critical(self, "Error", error)
        self.debug(f"Error shown: {error}")

# ## END Main Application Window Class def ## #


# ######## Main application code begins here ################## #

class ADMBrowserApp(qtw.QApplication):

    def __init__(self, args):
        super().__init__(args)

        #############################
        # Process the Configuration #
        #############################

        # locate the configuration file to use.
        confpaths = [
            '~/.admbrowser.yaml',
            '~/.config/admbrowser.yaml',
            '/etc/admbrowser.yaml',
            'etc/admbrowser/admbrowser.yaml'
        ]
        for path in confpaths:
            path = os.path.expanduser(path)
            if os.path.isfile(path):
                default_config_file = path
                break
        else:
            default_config_file = None

        # Get the argument configuration
        args_dict = self._configure_argparse()

        # Open the configuration file
        config_file = args_dict.get("config_file", default_config_file)
        if config_file:
            with open(config_file, 'r') as handle:
                file_dict = yaml.safe_load(handle)
        else:
            file_dict = {}

        # Create a configuration object
        self.config = Config(file_dict, args_dict, debug=self.debug)

        # Note: can't call "debug" until self.config exists
        self.debug(f"loading configuration from '{config_file}'")

        #########################
        # Create the MainWindow #
        #########################

        # Create main window
        self.mainwin = MainWindow(self.config, debug=self.debug)
        self.mainwin.show()

    def debug(self, message):
        """Log or print a message if the global DEBUG is true."""
        if not (self.config.debug or self.config.debug_log):
            pass
        else:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            debug_message = f"{timestamp}:: {message}"
            if self.config.debug:
                print(debug_message)
            if self.config.debug_log:
                try:
                    with open(self.config.debug_log, 'a') as handle:
                        handle.write(debug_message + "\n")
                except IOError as e:
                    print(f"unable to write log '{self.config.debug_log}':  {e}")

    def _configure_argparse(self):
        """Configure and process the command-line arguments.

        Returns a dictionary of the arguments.
        """

        # Create Parser
        parser = argparse.ArgumentParser()

        # add non-config switch for Configuration File
        parser.add_argument(
            "-c", "--config-file", action="store", default=argparse.SUPPRESS,
            dest="config_file",
            help="Specifiy an alternate config file"
        )

        # add config switches
        for key, meta in Config.option_definitions.items():
            if meta.switches:
                # not all actions are valid with the same keyword
                action = meta.action
                kwargs = {}
                if action == "store":
                    kwargs["type"] = meta.datatype
                    kwargs["choices"] = meta.values

                parser.add_argument(
                    *(meta.switches),
                    action=meta.action,
                    # no need for a default in argparse
                    # since we have a default option
                    default=argparse.SUPPRESS,
                    dest=key,
                    help=meta.help,
                    **kwargs
                )

        # rather than parse sys.argv here, we're parsing app.arguments
        # so that qt-specific args are removed.
        # we also need to remove argument 0.
        argv = [str(x) for x in list(self.arguments())][1:]

        return vars(parser.parse_args(argv))


def main():
    # Create the qapplication object,
    # so it can interpret the qt-specific CLI args
    app = ADMBrowserApp(sys.argv)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
