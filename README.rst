.. image:: https://travis-ci.org/wakatime/wakatime.svg
    :target: https://travis-ci.org/wakatime/wakatime
    :alt: Tests

.. image:: https://coveralls.io/repos/wakatime/wakatime/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/wakatime/wakatime?branch=master
    :alt: Coverage

.. image:: https://img.shields.io/pypi/v/wakatime.svg
    :target: https://pypi.python.org/pypi/wakatime
    :alt: Version

.. image:: https://img.shields.io/pypi/pyversions/wakatime.svg
    :target: https://pypi.python.org/pypi/wakatime
    :alt: Supported Python Versions


WakaTime
========

Command line interface to `WakaTime <https://wakatime.com/>`_ used by all WakaTime `text editor plugins <https://wakatime.com/editors>`_.

Go to http://wakatime.com/editors to install the plugin for your text editor or IDE.


Installation
------------

Note: You shouldn't need to directly use this package unless you are `building your own plugin <https://wakatime.com/help/misc/creating-plugin>`_ or your text editor's plugin asks you to install the WakaTime CLI manually.

Each `plugin <https://wakatime.com/editors>`_ installs the WakaTime CLI for you, except for the `Emacs WakaTime plugin <https://github.com/wakatime/wakatime-mode>`_.

Install the plugin for your IDE/editor:

https://wakatime.com/editors

Each plugin either comes pre-bundled with WakaTime CLI, or downloads the latest version from GitHub for you.


Usage
-----

If you are building a plugin using the `WakaTime API <https://wakatime.com/developers/>`_
then follow the `Creating a Plugin <https://wakatime.com/help/misc/creating-plugin>`_
guide.

For command line options, run ``wakatime --help``.

Some more usage information is available in the `FAQ <https://wakatime.com/faq>`_.


Configuring
-----------

Options can be passed via command line, or set in the ``$WAKATIME_HOME/.wakatime.cfg``
config file. Command line arguments take precedence over config file settings.
The ``$WAKATIME_HOME/.wakatime.cfg`` file is in `INI <http://en.wikipedia.org/wiki/INI_file>`_
format. An example config file with all available options::

    [settings]
    debug = false
    api_key = your-api-key
    hide_filenames = false
    exclude =
        ^COMMIT_EDITMSG$
        ^TAG_EDITMSG$
        ^/var/(?!www/).*
        ^/etc/
    include =
        .*
    only_include_with_project_file = false
    offline = true
    proxy = https://user:pass@localhost:8080
    no_ssl_verify = false
    timeout = 30
    hostname = machinename
    [projectmap]
    projects/foo = new project name
    ^/home/user/projects/bar(\d+)/ = project{0}
    [git]
    disable_submodules = false

For commonly used configuration options, see examples in the `FAQ <https://wakatime.com/faq>`_.


Troubleshooting
---------------

Read `How to debug the plugins <https://wakatime.com/faq#debug-plugins>`_.

Make sure to set ``debug=true`` in your ``~/.wakatime.cfg`` file.

Common log file location in your User ``$WAKATIME_HOME`` directory::

    ~/.wakatime.log

Each plugin also has it's own log file:

* **Atom** writes errors to the developer console (View -> Developer -> Toggle Developer Tools)
* **Brackets** errors go to the developer console (Debug -> Show Developer Tools)
* **Cloud9** logs to the browser console (View -> Developer -> JavaScript Console)
* **Coda** logs to ``/var/log/system.log`` so use ``sudo tail -f /var/log/system.log`` in Terminal to watch Coda 2 logs
* **Eclipse** logs can be found in the Eclipse ``Error Log`` (Window -> Show View -> Error Log)
* **Emacs** messages go to the *messages* buffer window
* **Jetbrains IDEs (IntelliJ IDEA, PyCharm, RubyMine, PhpStorm, AppCode, AndroidStudio, WebStorm)** log to ``idea.log`` (`locating IDE log files <https://intellij-support.jetbrains.com/hc/en-us/articles/207241085-Locating-IDE-log-files>`_)
* **Komodo** logs are written to ``pystderr.log`` (Help -> Troubleshooting -> View Log File)
* **Netbeans** logs to it's own log file (View -> IDE Log)
* **Notepad++** errors go to ``AppData\Roaming\Notepad++\plugins\config\WakaTime.log`` (this file is only created when an error occurs)
* **Sublime** Text logs to the Sublime Console (View -> Show Console)
* **TextMate** logs to stderr so run TextMate from Terminal to see any errors (`enable logging <https://github.com/textmate/textmate/wiki/Enable-Logging>`_)
* **Vim** errors get displayed in the status line or inline (use ``:redraw!`` to clear inline errors)
* **Visual Studio** logs to the Output window, but uncaught exceptions go to ActivityLog.xml (`more info... <http://blogs.msdn.com/b/visualstudio/archive/2010/02/24/troubleshooting-with-the-activity-log.aspx>`_)
* **VS Code** logs to the developer console (Help -> Toggle Developer Tools)
* **Xcode** type ``sudo tail -f /var/log/system.log`` in a Terminal to view Xcode errors

Useful API Endpoints:

* `List of Plugins and when they were last heard from <https://wakatime.com/api/v1/users/current/user_agents>`_
* `List of computers last sending coding activity <https://wakatime.com/api/v1/users/current/machine_names>`_

Useful Resources:

* `More Troubleshooting Info <https://wakatime.com/faq#debug-plugins>`_
* `Official API Docs <https://wakatime.com/api>`_


Contributing
------------

Before contributing a pull request, make sure tests pass::

    virtualenv venv
    . venv/bin/activate
    pip install tox
    tox

The above will run tests on all Python versions available on your machine.
To just run tests on a single Python version::

    virtualenv venv
    . venv/bin/activate
    pip install -r dev-requirements.txt
    nosetests

Many thanks to all `contributors <https://github.com/wakatime/wakatime/blob/master/AUTHORS>`_!
