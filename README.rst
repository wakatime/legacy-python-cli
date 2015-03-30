WakaTime
========

Fully automatic time tracking for programmers.

This is the common interface for the WakaTime api. You shouldn't need to directly use this package unless you are creating a new plugin or your text editor's plugin asks you to install the wakatime cli interface.

Go to http://wakatime.com to install the plugin for your text editor.


Usage
-----

Install the plugin for your IDE/editor at https://wakatime.com/plugins

If you are building a plugin using the `WakaTime API <https://wakatime.com/developers/>`_
then follow the `Creating a Plugin <https://wakatime.com/help/misc/creating-plugin>`_
guide.


Configuring
-----------

Options can be passed via command line, or set in the ``$HOME/.wakatime.cfg``
config file. Command line arguments take precedence over config file settings.
The ``$HOME/.wakatime.cfg`` file is in `INI <http://en.wikipedia.org/wiki/INI_file>`_
format. An example config file looks like::
    [settings]
    debug = false
    api_key = your-api-key
    hidefilenames = false
    exclude =
        ^COMMIT_EDITMSG$
        ^TAG_EDITMSG$
        ^/var/
        ^/etc/
    include =
        .*
    offline = true
    proxy = https://user:pass@localhost:8080


Installation
------------

Each `plugin <https://wakatime.com/plugins>`_ should install wakatime for you, except for the `Emacs WakaTime plugin <https://github.com/wakatime/wakatime-mode>`_.
If your plugin does not install wakatime cli(this package), install it with::
    pip install wakatime
