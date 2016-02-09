WakaTime
========

.. image:: https://travis-ci.org/wakatime/wakatime.svg
    :target: https://travis-ci.org/wakatime/wakatime

.. image:: https://coveralls.io/repos/wakatime/wakatime/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/wakatime/wakatime?branch=master
    
.. image:: https://wakaslack.herokuapp.com/badge.svg
    :target: https://wakaslack.herokuapp.com

Command line interface to `WakaTime <https://wakatime.com/>`_ used by all WakaTime `text editor plugins <https://wakatime.com/editors>`_.

Note: You shouldn't need to directly use this package unless you are `building your own plugin <https://wakatime.com/help/misc/creating-plugin>`_ or your text editor's plugin asks you to install the wakatime cli interface manually.

Go to http://wakatime.com/editors to install the plugin for your text editor or IDE.


Usage
-----

Install the plugin for your IDE/editor at https://wakatime.com/editors

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
    timeout = 30


Installation
------------

Each `plugin <https://wakatime.com/editors>`_ should install wakatime for you, except for the `Emacs WakaTime plugin <https://github.com/wakatime/wakatime-mode>`_.
If your plugin does not install wakatime cli(this package), install it with::

    pip install wakatime


Troubleshooting
---------------

WakaTime CLI writes errors to a common log file in your User ``$HOME`` directory::

    ~/.wakatime.log

Set ``debug=true`` in ``~/.wakatime.cfg`` for more verbose logging, but don't forget to set it back to ``debug=false`` afterwards or your editor might be laggy while waiting for wakatime cli to finish executing.

Each plugin also has it's own log file for things outside of the common wakatime cli:

* **Atom** writes errors to the developer console (View -> Developer -> Toggle Developer Tools)
* **Brackets** errors go to the developer console (Debug -> Show Developer Tools)
* **Eclipse** logs can be found in the Eclipse ``Error Log`` (Window -> Show View -> Error Log)
* **Emacs** messages go to the *messages* buffer window
* **Jetbrains IDEs (IntelliJ IDEA, PyCharm, RubyMine, PhpStorm, AppCode, AndroidStudio, WebStorm)** log to ``idea.log`` (`locating IDE log files <https://intellij-support.jetbrains.com/entries/23352446-Locating-IDE-log-files>`_)
* **Komodo** logs are written to ``pystderr.log`` (Help -> Troubleshooting -> View Log File)
* **Netbeans** logs to it's own log file (View -> IDE Log)
* **Notepad++** errors go to ``AppData\Roaming\Notepad++\plugins\config\WakaTime.log`` (this file is only created when an error occurs)
* **Sublime** Text logs to the Sublime Console (View -> Show Console)
* **TextMate** logs to stderr so run TextMate from Terminal to see any errors (`enable logging <https://github.com/textmate/textmate/wiki/Enable-Logging>`_)
* **Vim** errors get displayed in the status line or inline (use ``:redraw!`` to clear inline errors)
* **Visual Studio** logs to the Output window, but uncaught exceptions go to ActivityLog.xml (`more info... <http://blogs.msdn.com/b/visualstudio/archive/2010/02/24/troubleshooting-with-the-activity-log.aspx>`_)
* **Xcode** type ``sudo tail -f /var/log/system.log`` in a Terminal to view Xcode errors

Check that heartbeats are received by the WakaTime api with the ``last_heartbeat`` and ``last_plugin`` attributes from the `current user <https://wakatime.com/api/v1/users/current>`_ api resource. Saving a file forces a heartbeat to be sent.


Contributing
------------

Before contributing a pull request, make sure tests pass::

    virtualenv venv
    . venv/bin/activate
    pip install tox
    tox

Many thanks to all `contributors <https://github.com/wakatime/wakatime/blob/master/AUTHORS>`_!
