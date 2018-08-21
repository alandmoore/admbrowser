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

from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import (
    QUrl,
    QTimer,
    QObject,
    QEvent,
    Qt,
    QCoreApplication,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QWidget,
    QApplication,
    QSizePolicy,
    QToolBar,
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineProfile,
)

from . import messages as msg
from .admwebview import AdmWebView
from .admwebpage import AdmWebPage

# Define our default configuration settings
CONFIG_OPTIONS = {
    "allow_external_content": {"default": False, "type": bool},
    "allow_plugins": {"default": False, "type": bool},
    "allow_popups": {"default": False, "type": bool},
    "allow_printing": {"default": False, "type": bool},
    "bookmarks": {"default": {}, "type": dict},
    "content_handlers": {"default": {}, "type": dict},
    "default_password": {"default": None, "type": str},
    "default_user": {"default": None, "type": str},
    "force_js_confirm": {
        "default": "ask",
        "type": str,
        "values": ("ask", "accept", "deny")
    },
    "icon_theme": {"default": None, "type": str},
    "navigation": {"default": True, "type": bool},
    "navigation_layout": {
        "default": [
            'back',
            'forward',
            'refresh',
            'stop',
            'zoom_in',
            'zoom_out',
            'separator',
            'bookmarks',
            'separator',
            'spacer',
            'quit'
        ],
        "type": list
    },
    "network_down_html": {
        "default": msg.DEFAULT_NETWORK_DOWN,
        "type": str,
        "is_file": True
    },
    "page_unavailable_html": {
        "default": msg.DEFAULT_404,
        "type": str,
        "is_file": True
    },
    "print_settings": {"default": None, "type": dict},
    "privacy_mode": {"default": True, "type": bool},
    "proxy_server": {
        "default": None,
        "type": str,
        "env": "http_proxy"
    },
    "quit_button_mode": {
        "default": "reset",
        "type": str,
        "values": ["reset", "close"]
    },
    "quit_button_text": {"default": "I'm &Finished", "type": str},
    "screensaver_url": {"default": "about:blank", "type": str},
    "ssl_mode": {
        "default": "strict",
        "type": str,
        "values": ["strict", "ignore"]
    },
    "start_url": {"default": "about:blank", "type": str},
    "stylesheet": {"default": None, "type": str},
    "suppress_alerts": {"default": False, "type": bool},
    "timeout": {"default": 0, "type": int},
    "timeout_mode": {
        "default": "reset",
        "type": str,
        "values": ["reset", "close", "screensaver"]
    },
    "user_agent": {"default": None, "type": str},
    "user_css": {"default": None, "type": str},
    "whitelist": {"default": None},  # don't check type here
    "window_size": {"default": "max", "type": str},
    "zoom_factor": {"default": 1.0, "type": float}
}


class MainWindow(QMainWindow):

    """This is the main application window class

    it defines the GUI window for the browser
    """

    def __init__(self, options, parent=None, debug=None):
        """Construct a MainWindow Object."""
        super().__init__(parent)

        self.debug = debug or (lambda x: None)

        # Load config file
        self.setWindowTitle("Browser")
        self.debug("loading configuration from '{}'".format(options.config_file))
        configfile = {}
        if options.config_file:
            configfile = yaml.safe_load(open(options.config_file, 'r'))
        self.parse_config(configfile, options)
        # self.popup will hold a reference to the popup window
        # if it gets opened
        self.popup = None

        # Stylesheet support
        if self.config.get("stylesheet"):
            try:
                with open(self.config.get("stylesheet")) as ss:
                    self.setStyleSheet(ss.read())
            except Exception as e:
                self.debug(
                    (
                        'Problem loading stylesheet file "{}": {} '
                        '\nusing default style.'
                    ).format(self.config.get("stylesheet"), e)
                )
        self.setObjectName("global")

        # Set proxy server environment variable before creating web views
        if self.config.get("proxy_server"):
            os.environ["http_proxy"] = self.config.get("proxy_server")
            os.environ["https_proxy"] = self.config.get("proxy_server")

        # If the whitelist is activated, add the bookmarks and start_url
        if self.config.get("whitelist"):
            # we can just specify whitelist = True,
            # which should whitelist just the start_url and bookmark urls.
            if type(self.config.get("whitelist")) is not list:
                self.whitelist = []
            self.whitelist.append(str(QUrl(
                self.config.get("start_url")
            ).host()))
            bookmarks = self.config.get("bookmarks")
            if bookmarks:
                self.whitelist += [
                    str(QUrl(b.get("url")).host())
                    for k, b in bookmarks.items()
                ]
                self.whitelist = set(self.whitelist)  # uniquify and optimize
            self.debug("Generated whitelist: " + str(self.whitelist))

        # create the web engine profile
        self.create_webprofile()

        # Now construct the UI
        self.build_ui()

    # ## END OF CONSTRUCTOR ## #

    def parse_config(self, file_config, options):
        """Compile the running config

        Order of precedence:
          1. Switches
          2. Config file
          3. Defaults
        """
        self.config = {}
        options = vars(options)
        for key, metadata in CONFIG_OPTIONS.items():
            options_val = options.get(key)
            file_val = file_config.get(key)
            env_val = os.environ.get(metadata.get("env", ''))

            default_val = metadata.get("default")
            vals = metadata.get("values")
            self.debug("key: {}, default: {}, file: {}, options: {}".format(
                key, default_val, file_val, options_val
            ))
            if vals:
                options_val = options_val if options_val in vals else None
                file_val = file_val if file_val in vals else None
                env_val = env_val if env_val in vals else None
            if metadata.get("is_file"):
                filename = options_val or env_val
                if not filename:
                    self.config[key] = default_val
                else:
                    try:
                        with open(filename, 'r') as fh:
                            self.config[key] = fh.read()
                    except IOError:
                        self.debug("Could not open file {} for reading.".format(
                            filename
                        ))
                        self.config[key] = default_val
            else:
                set_values = [
                    val for val in (options_val, env_val, file_val)
                    if val is not None
                ]
                if len(set_values) > 0:
                    self.config[key] = set_values[0]
                else:
                    self.config[key] = default_val
            if metadata.get("type") and self.config[key]:
                self.debug("{} cast to {}".format(key, metadata.get("type")))
                self.config[key] = metadata.get("type")(self.config[key])
        self.debug(repr(self.config))

    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None,
                     checkable=False, signal="triggered"):
        """Return a QAction given a number of common QAction attributes

        Just a shortcut function Originally borrowed from
        'Rapid GUI Development with PyQT' by Mark Summerset
        """
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon.fromTheme(
                icon, QIcon(":/{}.png".format(icon))
            ))
        if shortcut is not None and not shortcut.isEmpty():
            action.setShortcut(shortcut)
            tip += " ({})".format(shortcut.toString())
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
        if self.config.get("privacy_mode"):
            webprofile = QWebEngineProfile()
        else:
            webprofile = QWebEngineProfile.defaultProfile()
        self.debug("Browser session is private: {}"
                   .format(webprofile.isOffTheRecord()))
        if self.config.get("user_agent"):
            webprofile.setHttpUserAgent(self.config["user_agent"])
            self.debug('Set user agent to "{}"'
                       .format(webprofile.httpUserAgent()))
        self.webprofile = webprofile

    def build_ui(self):
        """Set up the user interface for the main window.

        Unlike the constructor, this method is re-run
        whenever the browser is "reset" by the user.
        """

        self.debug("build_ui")
        inactivity_timeout = self.config.get("timeout")
        quit_button_tooltip = (
            msg.QUIT_TOOLTIP
            if self.config.get('quit_button_mode') == 'close'
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

        # Icon theme setting
        QIcon.setThemeName(self.config.get("icon_theme"))

        self.setCentralWidget(self.browser_window)
        self.debug("loading {}".format(self.config.get("start_url")))
        self.browser_window.setUrl(QUrl(self.config.get("start_url")))

        # Window size settings
        window_size = self.config.get("window_size", '').lower()
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
                self.debug('Ignoring invalid window size "{}"'.format(
                    window_size
                ))

        # Set up the top navigation bar if it's configured to exist
        if self.config.get("navigation"):
            self.navigation_bar = QToolBar("Navigation")
            self.navigation_bar.setObjectName("navigation")
            self.addToolBar(Qt.TopToolBarArea, self.navigation_bar)
            self.navigation_bar.setMovable(False)
            self.navigation_bar.setFloatable(False)

            #  Standard navigation tools
            self.nav_items = {
                "back": self.browser_window.pageAction(AdmWebPage.Back),
                "forward": self.browser_window.pageAction(AdmWebPage.Forward),
                "refresh": self.browser_window.pageAction(AdmWebPage.Reload),
                "stop": self.browser_window.pageAction(AdmWebPage.Stop),
                "quit": self.createAction(
                    self.config.get("quit_button_text"),
                    qb_mode_callbacks.get(
                        self.config.get("quit_button_mode"),
                        self.reset_browser
                    ),
                    QKeySequence("Alt+F"),
                    None,
                    quit_button_tooltip
                ),
                "zoom_in": self.createAction(
                    "Zoom In",
                    self.zoom_in,
                    QKeySequence("Alt++"),
                    "zoom-in",
                    "Increase the size of the text and images on the page"
                ),
                "zoom_out": self.createAction(
                    "Zoom Out",
                    self.zoom_out,
                    QKeySequence("Alt+-"),
                    "zoom-out",
                    "Decrease the size of text and images on the page"
                )
            }
            if self.config.get("allow_printing"):
                self.nav_items["print"] = self.createAction(
                    "Print",
                    self.browser_window.print_webpage,
                    QKeySequence("Ctrl+p"),
                    "document-print",
                    "Print this page"
                )

            # Add all the actions to the navigation bar.
            for item in self.config.get("navigation_layout"):
                if item == "separator":
                    self.navigation_bar.addSeparator()
                elif item == "spacer":
                    # an expanding spacer.
                    spacer = QWidget()
                    spacer.setSizePolicy(
                        QSizePolicy.Expanding,
                        QSizePolicy.Preferred
                    )
                    self.navigation_bar.addWidget(spacer)
                elif item == "bookmarks":
                    # Insert bookmarks buttons here.
                    self.bookmark_buttons = []
                    for bookmark in self.config.get("bookmarks", {}).items():
                        self.debug("Bookmark:\n" + bookmark.__str__())
                        # bookmark name will use the "name" attribute,
                        # if present, or else just the key:
                        bookmark_name = bookmark[1].get("name") or bookmark[0]
                        # Create a button for the bookmark as a QAction,
                        # which we'll add to the toolbar
                        button = self.createAction(
                            bookmark_name,
                            (
                                lambda url=bookmark[1].get("url"):
                                self.browser_window.load(QUrl(url))
                            ),
                            QKeySequence.mnemonic(bookmark_name),
                            None,
                            bookmark[1].get("description")
                        )
                        self.navigation_bar.addAction(button)
                        (self.navigation_bar.widgetForAction(button)
                         .setObjectName("navigation_button"))
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
            QKeySequence("Ctrl+Alt+Q"),
            None,
            ""
        )
        self.addAction(self.really_quit)

        # Call a reset function after timeout
        if inactivity_timeout != 0:
            self.event_filter = InactivityFilter(inactivity_timeout)
            QCoreApplication.instance().installEventFilter(self.event_filter)
            self.browser_window.page().installEventFilter(self.event_filter)
            self.event_filter.timeout.connect(
                to_mode_callbacks.get(
                    self.config.get("timeout_mode"),
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
        if self.config.get("navigation"):
            self.navigation_bar.hide()
        self.browser_window.setZoomFactor(self.config.get("zoom_factor"))
        self.browser_window.load(QUrl(self.config.get("screensaver_url")))
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


# ## END Main Application Window Class def ## #


class InactivityFilter(QTimer):
    """This defines an inactivity filter.

    It's basically a timer that resets when user "activity"
    (Mouse/Keyboard events) are detected in the main application.
    """
    activity = pyqtSignal()

    def __init__(self, timeout=0, parent=None):
        """Constructor for the class.

        args:
          timeout -- number of seconds before timer times out (integer)
        """
        super(InactivityFilter, self).__init__(parent)
        # timeout needs to be converted from seconds to milliseconds
        self.timeout_time = timeout * 1000
        self.setInterval(self.timeout_time)
        self.start()

    def eventFilter(self, object, event):
        """Overridden from QTimer.eventFilter"""
        if event.type() in (
            QEvent.MouseMove, QEvent.MouseButtonPress,
            QEvent.HoverMove, QEvent.KeyPress,
            QEvent.KeyRelease
        ):
            self.activity.emit()
            self.start(self.timeout_time)
            # commented this debug code,
            # because it spits out way to much information.
            # uncomment if you're having trouble with the timeout detecting
            # user inactivity correctly to determine what it's detecting
            # and ignoring:

            # debug ("Activity: %s type %d" % (event, event.type()))
            # else:
            # debug("Ignored event: %s type %d" % (event, event.type()))
        return QObject.eventFilter(self, object, event)




# ######## Main application code begins here ################## #

class ADMBrowserApp(QApplication):

    def __init__(self, args):
        super().__init__(args)
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

        self.args = self._configure_argparse(default_config_file)

        self.mainwin = MainWindow(self.args, debug=self.debug)
        self.mainwin.show()

    def debug(self, message):
        """Log or print a message if the global DEBUG is true."""
        if not (self.args.debug or self.args.debug_log):
            pass
        else:
            message = message.__str__()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            debug_message = "{}:: {}".format(timestamp, message)
            if self.args.debug:
                print(debug_message)
            if self.args.debug_log:
                try:
                    with open(self.args.debug_log, 'a') as file_handle:
                        file_handle.write(debug_message + "\n")
                except Exception as e:
                    print(
                        "unable to write to log file {}:  {}"
                        .format(self.args.debug_log, e)
                    )

    def _configure_argparse(self, default_config_file):
        # Parse the command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument(  # Start URL
            "-l", "--url", action="store", dest="start_url",
            help="Start browser at URL"
        )
        parser.add_argument(  # No Navigation
            "-n", "--no-navigation", action="store_false",
            default=argparse.SUPPRESS, dest="navigation",
            help="Start browser without Navigation controls"
        )
        parser.add_argument(  # Config file
            "-c", "--config-file", action="store", default=default_config_file,
            dest="config_file", help="Specifiy an alternate config file"
        )
        parser.add_argument(  # Debug
            "-d", "--debug", action="store_true", default=False, dest="debug",
            help="Enable debugging output to stdout"
        )
        parser.add_argument(  # Debug Log
            "--debug_log", action="store", default=None, dest="debug_log",
            help="Enable debug output to the specified filename"
        )
        parser.add_argument(  # Timeout
            "-t", "--timeout", action="store", type=int, default=argparse.SUPPRESS,
            dest="timeout",
            help="Define the timeout in seconds after which to reset the browser"
            "due to user inactivity"
        )
        parser.add_argument(  # icon theme
            "-i", "--icon-theme", action="store", default=None, dest="icon_theme",
            help="override default icon theme with other Qt/KDE icon theme"
        )
        parser.add_argument(  # Default zoom factor
            "-z", "--zoom", action="store", type=float, default=argparse.SUPPRESS,
            dest="zoomfactor", help="Set the zoom factor for web pages"
        )
        parser.add_argument(  # Allow popups
            "-p", "--popups", action="store_true", default=argparse.SUPPRESS,
            dest="allow_popups", help="Allow the browser to open new windows"
        )
        parser.add_argument(  # Default HTTP user
            "-u", "--user", action="store", dest="default_user",
            help="Set the default username used for URLs"
            " that require authentication"
        )
        parser.add_argument(  # Default HTTP password
            "-w", "--password", action="store", dest="default_password",
            help="Set the default password used for URLs"
            " that require authentication"
        )
        parser.add_argument(  # Allow launching of external programs
            "-e", "--allow_external", action="store_true",
            default=argparse.SUPPRESS, dest='allow_external_content',
            help="Allow the browser to open content in external programs."
        )
        parser.add_argument(  # Allow browser plugins
            "-g", "--allow_plugins", action="store_true",
            default=argparse.SUPPRESS, dest='allow_plugins',
            help="Allow the browser to use plugins like"
            " Flash or Java (if installed)"
        )
        parser.add_argument(  # Window size
            "--size", action="store", dest="window_size", default=None,
            help="Specify the default window size in pixels (widthxheight),"
            " 'max' to maximize, or 'full' for full-screen."
        )
        parser.add_argument(  # HTTP Proxy server
            "--proxy_server", action="store", dest="proxy_server", default=None,
            help="Specify a proxy server string, in the form host:port"
        )

        # rather than parse sys.argv here, we're parsing app.arguments
        # so that qt-specific args are removed.
        # we also need to remove argument 0.
        argv = [str(x) for x in list(self.arguments())][1:]
        return parser.parse_args(argv)


def main():
    # Create the qapplication object,
    # so it can interpret the qt-specific CLI args
    app = ADMBrowserApp(sys.argv)
    app.exec_()


if __name__ == "__main__":
    main()
