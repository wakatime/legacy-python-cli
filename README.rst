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


Troubleshooting
---------------

WakaTime CLI writes errors to a common log file in your User $HOME directory:

``$HOME/.wakatime.log``

Set ``debug=true`` in ``~/.wakatime.cfg`` for more verbose logging, but don't forget to set it back to ``debug=false`` afterwards or your editor might be laggy while waiting for wakatime cli to finish executing.

Each plugin also has it's own log file for things outside of the common wakatime cli:

* **Atom** writes errors to the developer console (View -> Developer -> Toggle Developer Tools)
* **Brackets** errors go to the developer console (Debug -> Show Developer Tools)
* **Eclipse** logs can be found in the Eclipse ``Error Log`` (Window -> Show View -> Error Log)
* **Emacs** messages go to the *messages* buffer window
* **Jetbrains IDEs (IntelliJ IDEA, PyCharm, RubyMine, PhpStorm, AppCode, AndroidStudio, WebStorm)** log to ``idea.log`` (`locating IDE log files <https://intellij-support.jetbrains.com/entries/23352446-Locating-IDE-log-files>`_)
* **Komodo** logs are written to ``pystderr.log`` (Help -> Troubleshooting -> View Log File)
* **Netbeans** logs to it's own log file (View -> IDE Log)
* **Notepad++** errors go to ``notepadpp-wakatime.log`` in your User home directory (this file is only created when an error occurs)
* **Sublime** Text logs to the Sublime Console (View -> Show Console)
* **TextMate** logs to stderr so run TextMate from Terminal to see any errors (`enable logging <https://github.com/textmate/textmate/wiki/Enable-Logging>`_)
* **Vim** errors get displayed in the status line or inline (use ``:redraw!`` to clear inline errors)
* **Visual Studio** errors go to ActivityLog.xml (`more info... <http://blogs.msdn.com/b/visualstudio/archive/2010/02/24/troubleshooting-with-the-activity-log.aspx>`_)
* **Xcode** errors go to ``dmesg`` (type ``dmesg`` in a Terminal to view them)

Check that heartbeats are received by the WakaTime api with the ``last_heartbeat`` and ``last_plugin`` attributes from the `current user <https://wakatime.com/api/v1/users/current>`_ api resource. Saving a file forces a heartbeat to be sent.
