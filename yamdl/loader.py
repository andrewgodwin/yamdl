from django.apps import apps

import os.path
import yaml


class ModelLoader(object):
    """
    Reads model instances from disk as .yaml files and loads them into
    a database (designed for an in-memory one due to PK removal etc.)
    """

    def __init__(self, connection, directories):
        self.connection = connection
        self.directories = directories

    def load(self):
        """
        Loads everything
        """
        self.loaded = 0
        # Discover models we manage and load their schema into memory
        self.load_schema()
        # Scan content directories
        for directory in self.directories:
            # First level should be folders named after models
            for model_folder in os.listdir(directory):
                folder_path = os.path.join(directory, model_folder)
                if "." in model_folder and not model_folder.startswith(".") and os.path.isdir(folder_path):
                    # Second level should be files
                    for filename in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, filename)
                        if filename.endswith(".yaml") and os.path.isfile(file_path):
                            self.load_file(model_folder.lower(), file_path)
        # Print result
        print("Loaded %s yamdl fixtures." % self.loaded)

    def load_file(self, model_name, file_path):
        """
        Loads a single file of fixtures.
        """
        # Make sure it's for a valid model
        try:
            model_class = self.managed_models[model_name]
        except KeyError:
            raise ValueError("Cannot load yamdl fixture %s - the model name %s is not managed." % (
                file_path,
                model_name,
            ))
        # Read it into memory
        with open(file_path, "r", encoding="utf8") as fh:
            fixture_data = yaml.safe_load(fh)
        # Write it into our fixtures storage
        if isinstance(fixture_data, list):
            for fixture in fixture_data:
                self.load_fixture(model_class, fixture)
        elif isinstance(fixture_data, dict):
            self.load_fixture(model_class, fixture_data)
        else:
            raise ValueError("Cannot load yamdl fixture %s - not a dict or list." % file_path)

    def load_fixture(self, model_class, data):
        """
        Loads a single fixture from a dict object.
        """
        # Make an instance of the model, then save it
        instance = model_class(**data)
        instance.save(using=self.connection.alias)
        self.loaded += 1

    def load_schema(self):
        """
        Works out which models are marked as managed by us, and writes a schema
        for them into the database.
        """
        # Go through and collect the models
        self.managed_models = {}
        for app in apps.get_app_configs():
            for model in app.get_models():
                if getattr(model, "__yamdl__", False):
                    self.managed_models[model._meta.label_lower] = model
        # Make the tables in the database
        with self.connection.schema_editor() as editor:
            for model in self.managed_models.values():
                editor.create_model(model)
        print("Created yamdl schema for %s" % (
            ", ".join(self.managed_models.keys()),
        ))
