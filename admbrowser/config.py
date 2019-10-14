"""Defaults and metadata for the application's configuration options"""

from dataclasses import dataclass
from typing import Any
from os import environ

from . import messages as msg


@dataclass
class OptionDefinition:
    default: Any = None
    datatype: type = str
    switches: tuple = None
    values: tuple = None
    action: str = 'store'
    help: str = ''
    is_file: bool = False
    env: str = None

    def __str__(self):
        return str(self.value) if self.value else ''

class Config:

    option_definitions = {
        "allow_external_content": OptionDefinition(
            default=False,
            datatype=bool,
            switches=('-e', '--allow_external'),
            help="Allow the browser to open content in external applications",
            action='store_true'
        ),
        "allow_plugins": OptionDefinition(
            default=False,
            datatype=bool,
            switches=('-g', '--allow_plugins'),
            help="Allow the browser to use plugins",
            action="store_true"
        ),
        "allow_popups": OptionDefinition(
            default=False,
            datatype=bool,
            switches=("-p", "--popups"),
            help="Allow browser to open new windows",
            action="store_true"
        ),
        "allow_printing": OptionDefinition(default=False, datatype=bool),
        "bookmarks": OptionDefinition(default={}, datatype=dict),
        "content_handlers": OptionDefinition(default={}, datatype=dict),
        "default_password": OptionDefinition(
            default=None,
            switches=("-w", "--password"),
            help="Default password for URLs requiring authentication"
        ),
        "default_user": OptionDefinition(
            default=None,
            switches=("-u", "--user"),
            help="Default username for URLs requiring authentication"
        ),
        "force_js_confirm": OptionDefinition(
            default="ask",
            values=("ask", "accept", "deny")
        ),
        "icon_theme": OptionDefinition(
            switches=("-i", "--icon_theme"),
            help="Qt/KDE icon theme to use"
        ),
        "navigation": OptionDefinition(
            default=True,
            datatype=bool,
            switches=("-n", "--no_navigation"),
            help="Start browser without navigation controls",
            action="store_false"
        ),
        "navigation_layout": OptionDefinition(
            default=[
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
            datatype=list
        ),
        "network_down_html": OptionDefinition(
            default=msg.DEFAULT_NETWORK_DOWN,
            is_file=True
        ),
        "page_unavailable_html": OptionDefinition(
            default=msg.DEFAULT_404,
            is_file=True
        ),
        "print_settings": OptionDefinition(default=None, datatype=dict),
        "privacy_mode": OptionDefinition(
            default=True,
            datatype=bool,
            switches=('--privacy',),
            action="store_true"
        ),
        "proxy_server": OptionDefinition(
            env="http_proxy",
            switches=("--proxy_server",),
            help="Proxy server string, in the format host:port"
        ),
        "quit_button_mode": OptionDefinition(
            default="reset",
            values=("reset", "close")
        ),
        "quit_button_text": OptionDefinition(default="I'm &Finished"),
        "screensaver_url": OptionDefinition(default="about:blank"),
        "ssl_mode": OptionDefinition(
            default="strict",
            values=("strict", "ignore")
        ),
        "start_url": OptionDefinition(
            default="about:blank",
            switches=("-l", "--url"),
            help="Start browser at this URL",
        ),
        "stylesheet": OptionDefinition(),
        "suppress_alerts": OptionDefinition(default=False, datatype=bool),
        "timeout": OptionDefinition(
            default=0,
            datatype=int,
            switches=("-t", "--timeout"),
            help="Reset browser after this many seconds of user inactivity"
        ),
        "timeout_mode": OptionDefinition(
            default="reset",
            values=["reset", "close", "screensaver"]
        ),
        "user_agent": OptionDefinition(),
        "whitelist": OptionDefinition(datatype=None),
        "window_size": OptionDefinition(
            default="max",
            switches=("--size",),
            help=("Window size in pixels (WxH), 'max' for maximized,"
                     " or 'full' for full-screen")
        ),
        "zoom_factor": OptionDefinition(
            default=1.0,
            datatype=float,
            switches=("-z", "--zoom"),
            help="Default zoom factor for web pages"
        )
    }

    def __init__(self, file_config, args_config, debug=None):
        """Create a configuration

        Will combine the file config, command-line arguments, and Defaults
        to create a single configuration object.

        Both config arguments must be dictionaries.
        debug is the debug log function
        """
        self.debug = debug or (lambda x: None)
        self._build_config(file_config, args_config)


    def _build_config(self, file_config, args_config):
        for key, definition in self.option_definitions.items():
            sources = {"CLI arguments": args_config, "Configuration file": file_config}
            if definition.env:
                sources['Environment variables'] = environ

            for sourcename, source in sources.items():
                if key not in source:
                    continue
                value = source[key]
                if definition.datatype and not isinstance(value, definition.datatype):
                    self.debug(
                        f'Wrong datatype for {key} in {sourcename}: '
                        f'{value} is {type(value)}, {definition.datatype} required'
                    )
                    continue
                if definition.values and value not in definition.values:
                    self.debug(
                        f'Invalid setting for {key} in {sourcename}: '
                        f'"{value}" must be one of {definition.values}'
                    )
                    continue
                if definition.is_file:
                    try:
                        with open(value, 'r') as handle:
                            value = handle.read()
                    except IOError as e:
                        self.debug(
                            f'Could not open file {value} for option {key} set in {sourcename}.  '
                            f'Error was: {e}'
                        )
                    continue
                # if all went well and we found a valid value, break
                break
            else:  # we get here when attempts to find a valid value fail
                value = definition.default


            # having established the value, set it as a class attribute.
            setattr(self, key, value)

    def __str__(self):

        option_list = '\n\t'.join([
            f'{key}:\t{getattr(self, key)}'
            for key in self.option_definitions
        ])
        return f'ADMBrowser Configuration:\n\t{option_list}'
