import logging
from pathlib import Path

import yaml
from django.apps import apps
from django.db import transaction


logger = logging.getLogger(__name__)


class ModelLoader(object):
    """
    Reads model instances from disk as .yaml files and loads them into
    a database (designed for an in-memory one due to PK removal etc.)
    """

    EXT_MARKDOWN = [".md", ".markdown"]
    EXT_YAML = [".yml", ".yaml"]

    def __init__(self, connection, directories):
        self.connection = connection
        self.directories = directories

    def get_content_field(self, model_class):
        """
        Determine which field is used to store file content
        """
        return "content"

    def load(self):
        """
        Loads everything
        """
        self.loaded = 0
        # Discover models we manage and load their schema into memory
        self.load_schema()

        with transaction.atomic(using=self.connection.alias):
            # Scan content directories
            for directory in self.directories:
                # First level should be folders named after models
                for model_folder in Path(directory).iterdir():
                    if (
                        model_folder.is_dir()
                        and model_folder.name in self.managed_directories
                    ):
                        model = self.managed_directories[model_folder.name]
                        # Second level should be files, or more folders
                        self.load_folder_files(model._meta.label_lower, model_folder)
        logger.info("Loaded %d yamdl fixtures.", self.loaded)

    def load_folder_files(self, model_name, folder_path: Path):
        """
        Loads a folder full of either fixtures or other files
        """
        model_class = self.get_model_class(model_name)

        for filename in folder_path.iterdir():
            if filename.is_dir():
                self.load_folder_files(model_class, filename)
            elif filename.suffix in self.EXT_YAML and filename.is_file():
                self.load_yaml_file(model_class, filename)
            elif filename.suffix in self.EXT_MARKDOWN and filename.is_file():
                self.load_markdown_file(model_class, filename)

    def get_model_class(self, model_name):
        # Make sure it's for a valid model
        try:
            return self.managed_models[model_name]
        except KeyError:
            raise ValueError(
                "Cannot load yamdl fixture - the model name %s is not managed."
                % (model_name,)
            )

    def load_yaml_file(self, model_class, file_path: Path):
        """
        Loads a single file of fixtures.
        """
        # Read it into memory
        with file_path.open(mode="r", encoding="utf8") as fh:
            fixture_data = yaml.safe_load(fh)
        # Write it into our fixtures storage
        if isinstance(fixture_data, list):
            for fixture in fixture_data:
                self.load_fixture(model_class, fixture, file_path)
        elif isinstance(fixture_data, dict):
            self.load_fixture(model_class, fixture_data, file_path)
        else:
            raise ValueError(
                "Cannot load yamdl fixture %s - not a dict or list." % file_path
            )

    def load_markdown_file(self, model_class, file_path: Path):
        """
        Loads a markdown-hybrid file (yaml, then ---, then markdown).
        """
        with file_path.open(mode="r", encoding="utf8") as fh:
            # Read line by line until we hit the document separator
            yaml_data = ""
            for line in fh:
                if line.strip() == "---":
                    if not yaml_data:
                        # File started with "---"
                        continue
                    break
                else:
                    yaml_data += line
            else:
                if not yaml_data:
                    # Empty file.
                    return
                raise ValueError(
                    f"Markdown hybrid file {file_path} contains no document separator (---)"
                )
            fixture_data = yaml.safe_load(yaml_data)
            if not isinstance(fixture_data, dict):
                _type = type(fixture_data).__name__
                raise ValueError(f"Markdown hybrid header is not a YAML dict, but {_type}")
            # The rest goes into "content"
            fixture_data[self.get_content_field(model_class)] = fh.read()
            self.load_fixture(model_class, fixture_data, file_path)

    def load_fixture(self, model_class, data, file_path: Path):
        """
        Loads a single fixture from a dict object.
        """
        # Make an instance of the model, then save it
        if hasattr(model_class, "from_yaml"):
            model_class.from_yaml(**data)
        else:
            model_class.objects.create(**data)
        self.loaded += 1

    def load_schema(self):
        """
        Works out which models are marked as managed by us, and writes a schema
        for them into the database.
        """
        # Go through and collect the models
        self.managed_models = {}
        self.managed_directories = {}
        for app in apps.get_app_configs():
            for model in app.get_models():
                if getattr(model, "__yamdl__", False):
                    directory = getattr(model, "__yamdl_directory__", model._meta.label_lower)
                    self.managed_models[model._meta.label_lower] = model
                    self.managed_directories[directory] = model
        # Make the tables in the database
        with self.connection.schema_editor() as editor:
            for model in self.managed_models.values():
                editor.create_model(model)
        logger.info("Created yamdl schema for %s" % (", ".join(self.managed_models.keys()),))
