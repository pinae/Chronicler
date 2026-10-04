from django.db import models


class SchemaOrigin(models.TextChoices):
    LIBRARY = "library"
    VOICED = "voiced"


class StepPhase(models.TextChoices):
    SETUP = "setup"
    DEVELOPMENT = "development"
    PAYOFF = "payoff"


class Schema(models.Model):
    """A narrative pattern. The YAML files in schemas/library/ are the spec; rows are loaded from them."""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    # [["T", "character"], ["V", "character"], ["S", "secret"]]: pairs in the order of the schema file
    # (a JSON object would lose that order in PostgreSQL's JSONB).
    roles = models.JSONField()
    constraints = models.JSONField(default=list, blank=True)
    payoff_steps = models.JSONField(default=list, blank=True)
    prior = models.FloatField(default=0.0)  # log-odds base rate
    origin = models.CharField(max_length=20, choices=SchemaOrigin, default=SchemaOrigin.LIBRARY)

    def __str__(self) -> str:
        return self.name

    @property
    def role_names(self) -> list[str]:
        return [role for role, _ in self.roles]


class Step(models.Model):
    schema = models.ForeignKey(Schema, related_name="steps", on_delete=models.CASCADE)
    step_id = models.SlugField()
    order = models.PositiveIntegerField()
    phase = models.CharField(max_length=20, choices=StepPhase)
    patterns = models.JSONField()  # beat patterns in their YAML shape; any one may fill the step
    required = models.BooleanField(default=True)
    repeatable = models.BooleanField(default=False)
    weight = models.FloatField(default=1.0)  # log Bayes factor contributed when filled
    contradicts = models.JSONField(default=list, blank=True)
    trigger = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["schema", "step_id"], name="step_id_unique_per_schema")
        ]

    def __str__(self) -> str:
        return f"{self.schema.slug}.{self.step_id}"
