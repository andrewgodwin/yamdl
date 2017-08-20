from django.apps import apps
from django.conf import settings


class YamdlRouter(object):
    """
    Database router that intercepts models marked as being managed by us.
    """

    DEFAULT_DB_ALIAS = "yamdl"

    def __init__(self):
        self.yamdl_app = apps.get_app_config("yamdl")

    def _is_yamdl(self, obj):
        return getattr(obj, "__yamdl__", False)

    def db_for_read(self, model, **hints):
        if self._is_yamdl(model):
            return getattr(settings, "YAMDL_DATABASE_ALIAS", self.DEFAULT_DB_ALIAS)

    def db_for_write(self, model, **hints):
        if self._is_yamdl(model):
            if self.yamdl_app.loaded:
                raise RuntimeError("You cannot write to Yamdl-backed models")
            else:
                return getattr(settings, "YAMDL_DATABASE_ALIAS", self.DEFAULT_DB_ALIAS)
