from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from schemas.definitions import SchemaDefinitionError
from schemas.library import LIBRARY_DIR, load_library


class Command(BaseCommand):
    help = "Load the schema library (schemas/library/*.yaml) into the database."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--directory", default=str(LIBRARY_DIR), help="directory with schema YAML files")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            schemas = load_library(Path(options["directory"]))
        except SchemaDefinitionError as error:
            raise CommandError(str(error)) from error
        noun = "schema" if len(schemas) == 1 else "schemas"
        slugs = ", ".join(schema.slug for schema in schemas)
        self.stdout.write(f"Loaded {len(schemas)} {noun}: {slugs}")
