"""Defaults and metadata for the application's configuration options"""

from . import messages as msg


CONFIG_OPTIONS = {
    "allow_external_content": {
        "default": False,
        "type": bool,
        "switches": ('-e', '--allow_external'),
        "help": "Allow the browser to open content in external applications",
        "action": "store_true"
    },
    "allow_plugins": {
        "default": False,
        "type": bool,
        "switches": ('-g', '--allow_plugins'),
        "help": "Allow the browser to use plugins",
        "action": "store_true"
    },
    "allow_popups": {
        "default": False,
        "type": bool,
        "switches": ("-p", "--popups"),
        "help": "Allow browser to open new windows",
        "action": "store_true"
    },
    "allow_printing": {"default": False, "type": bool},
    "bookmarks": {"default": {}, "type": dict},
    "content_handlers": {"default": {}, "type": dict},
    "default_password": {
        "default": None,
        "type": str,
        "switches": ("-w", "--password"),
        "help": "Default password for URLs requiring authentication"
    },
    "default_user": {
        "default": None,
        "type": str,
        "switches": ("-u", "--user"),
        "help": "Default username for URLs requiring authentication"
    },
    "force_js_confirm": {
        "default": "ask",
        "type": str,
        "values": ("ask", "accept", "deny")
    },
    "icon_theme": {
        "default": None,
        "type": str,
        "switches": ("-i", "--icon_theme"),
        "help": "Qt/KDE icon theme to use"
    },
    "navigation": {
        "default": True,
        "type": bool,
        "switches": ("-n", "--no_navigation"),
        "help": "Start browser without navigation controls",
        "action": "store_false"
    },
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
        "env": "http_proxy",
        "switches": ("--proxy_server",),
        "help": "Proxy server string, in the format host:port"
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
    "start_url": {
        "default": "about:blank",
        "type": str,
        "switches": ("-l", "--url"),
        "help": "Start browser at this URL",
    },
    "stylesheet": {"default": None, "type": str},
    "suppress_alerts": {"default": False, "type": bool},
    "timeout": {
        "default": 0,
        "type": int,
        "switches": ("-t", "--timeout"),
        "help": "Reset browser after this many seconds of user inactivity"
    },
    "timeout_mode": {
        "default": "reset",
        "type": str,
        "values": ["reset", "close", "screensaver"]
    },
    "user_agent": {"default": None, "type": str},
    "user_css": {"default": None, "type": str},
    "whitelist": {"default": None},  # don't check type here
    "window_size": {
        "default": "max",
        "type": str,
        "switches": ("--size",),
        "help": ("Window size in pixels (WxH), 'max' for maximized,"
                 " or 'full' for full-screen")
    },
    "zoom_factor": {
        "default": 1.0,
        "type": float,
        "switches": ("-z", "--zoom"),
        "help": "Default zoom factor for web pages"
    }
}
