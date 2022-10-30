import os

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from django.utils.autoreload import autoreload_started

from .loader import ModelLoader


class YamdlConfig(AppConfig):

    name = "yamdl"
    loaded = False

    def ready(self):
        """
        Startup and signal handling code
        """
        if not self.loaded:
            # Verify we have a db alias to write to.
            self.db_alias = getattr(settings, "YAMDL_DATABASE_ALIAS", "yamdl")
            if self.db_alias not in connections:
                raise ImproperlyConfigured(
                    "No database is set up for Yamdl (expecting alias %s).\n"
                    "You should either set YAMDL_DATABASE_ALIAS or add a DATABASES entry."
                    % self.db_alias
                )
            self.connection = connections[self.db_alias]
            # Make sure it's shared in-memory SQLite
            if self.connection.vendor != "sqlite":
                raise ImproperlyConfigured(
                    "The Yamdl database must be shared in-memory SQLite"
                )
            if not self.connection.is_in_memory_db():
                raise ImproperlyConfigured(
                    "The Yamdl database must be shared in-memory SQLite"
                )
            if "mode=memory" not in self.connection.settings_dict.get("NAME", ""):
                raise ImproperlyConfigured(
                    "The Yamdl database must be shared in-memory SQLite"
                )
            # Check the directory settings
            if not hasattr(settings, "YAMDL_DIRECTORIES"):
                raise ImproperlyConfigured(
                    "You have not set YAMDL_DIRECTORIES to a list of directories to scan"
                )
            for directory in settings.YAMDL_DIRECTORIES:
                if not os.path.isdir(directory):
                    raise ImproperlyConfigured(
                        "Yamdl directory %s does not exist" % directory
                    )
            # Read the fixtures into memory
            self.loader = ModelLoader(self.connection, settings.YAMDL_DIRECTORIES)
            self.loader.load()
            self.loaded = True
            # Add autoreload watches for our files
            autoreload_started.connect(self.autoreload_ready)

    def autoreload_ready(self, sender, **kwargs):
        for directory in settings.YAMDL_DIRECTORIES:
            sender.watch_dir(directory, "**/*.yaml")
            sender.watch_dir(directory, "**/*.md")
