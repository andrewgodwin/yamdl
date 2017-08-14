yamdl
=====

.. image:: https://img.shields.io/pypi/v/yamdl.svg
    :target: https://pypi.python.org/pypi/yamdl

.. image:: https://img.shields.io/pypi/l/yamdl.svg
    :target: https://pypi.python.org/pypi/yamdl

Lets you store instances of Django models as flat files (simplified fixtures).
For when you want to store content in a Git repo, but still want to be able to
use the normal Django ORM methods and shortcut functions.

It works by loading the data into an in-memory SQLite database on startup, and
then serving queries from there. This means it adds a little time to your app's
boot, and slightly more RAM usage, but with the advantage of a much easier time
dealing with static files (rather than custom code to load them directly).

It does not persist changes to the models back into files - this is purely for
authoring content in a text editor and using it via Django.

Due to Python limitations yamdl currently only works on **Python 3.4** and up.


Why not use normal fixtures?
----------------------------

They're not only a little verbose, but they need to be loaded into a non-memory
database (slower) and you need lots of logic to work out if you should update
or delete existing entries. They're still a better solution for anything that
has a lot of data or which needs JOINs, though.


Installation
------------

First, install the package::

    pip install yamdl

Then, add it to ``INSTALLED_APPS``::

    INSTALLED_APPS = [
        ...
        'yamdl',
        ...
    ]

Then, add the in-memory database to ``DATABASES`` (note that you must have at
least **Python 3.4** to have a SQlite module that understands shared memory URIs)::

    DATABASES = {
        ...
        'yamdl': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'file:yamdl-db?mode=memory&cache=shared',
        }
    }

Then, add a ``YAMDL_DIRECTORIES`` setting which defines where your directories
of YAML files can be found (it's a list)::

    YAMDL_DIRECTORIES = [
        os.path.join(PROJECT_DIR, "content"),
    ]

Finally, add the database router::

    DATABASE_ROUTERS = [
        "yamdl.router.YamdlRouter",
    ]


Usage
-----

First, add the ``__yamdl__`` attribute to the models you want to use static
content. A model can only be static or dynamic, not both::

    class MyModel(models.Model):
        ...
        __yamdl__ = True

Then, start making static files under one of the directories you listed in the
``YAMDL_DIRECTORIES`` setting above. Within one of these, make a directory with
the format ``appname.modelname``, and then YAML files ending in ``.yaml``::

    andrew-site/
        content/
            speaking.Talk/
                2017.yaml
                2016.yaml

Within those YAML files, you can define either a list of model instances, like
this::

    - title: 'Alabama'
      section: us-states

    - title: 'Alaska'
      section: us-states
      done: 2016-11-18
      place_name: Fairbanks

    - title: 'Arizona'
      section: us-states
      done: 2016-05-20
      place_name: Flagstaff

Or a single model instance at the top level, like this::

    conference: DjangoCon AU
    title: Horrors of Distributed Systems
    when: 2017-08-04
    description: Stepping through some of the myriad ways in which systems can fail that programmers don't expect, and how this hostile environment affects the design of distributed systems.
    city: Melbourne
    country: AU
    slides_url: https://speakerdeck.com/andrewgodwin/horrors-of-distributed-systems
    video_url: https://www.youtube.com/watch?v=jx1Hkxe64Xs

When you start up Django, as either ``runserver`` or in production, it will read the
YAML files and load them into an in-memory database and then let you query them
using all the standard ORM stuff.


Todo
----

Here's a short list of things I'd like to get done before a 1.0:

* Maybe replace the ``__yamdl__`` attribute with something nicer.
* Support for Python versions before 3.4, either by using a global SQLite ``:memory:`` instance with thread locking or by supporting disk databases with a wipe phase.
* Include YAML files in the Django auto-reloader so editing them loads changes in development.
* Potentially load changes to flat files in production using mtime checking.
