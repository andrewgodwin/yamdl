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
boot, but versus static files, it still lets you write queries and have dynamic
views, while all being incredibly fast as queries return in microseconds.

It does not persist changes to the models back into files - this is purely for
authoring content in a text editor and using it via Django.


Why not use normal fixtures?
----------------------------

They're not only a little verbose, but they need to be loaded into a non-memory
database (slower) and you need lots of logic to work out if you should update
or delete existing entries.

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

Then, add the in-memory database to ``DATABASES``::

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

You can override the expected directory name by setting to the expected
directory name instead::

    class MyModel(models.Model):
        ...
        __yamdl__ = True
        __yamdl_directory__ = "talks"

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

You can also define a Markdown document (ending in ``.md``) below a document
separator, and it will be loaded into the column called ``content``::

    date: 2022-01-18 21:00:00+00:00
    image: blog/2022/241.jpg
    image_expand: true
    section: van-build
    slug: planning-a-van
    title: Planning A Van

    ---

    What's In A Van?
    ----------------

    So, I have decided to embark on my biggest project to date (and probably for a while, unless I finally get somewhere to build a cabin) - building myself a camper van, from scratch. Well, from an empty cargo van, anyway.

Files can be nested at any level under their model directory, so you can group
the files together in directories (for example, blog posts by year) if you
want.

The files are also added to the Django autoreloader, so if you are using the
development server, it will reload as you edit the files (so you can see
changes reflected live - they are only read on server start).

To customize how content files are loaded, you can set ``YAMDL_LOADER`` to a subclass of ``yamdl.loader.ModelLoader``, which will be imported and used instead.
