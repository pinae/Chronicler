from django.contrib import admin

from chronicle.models import Beat, Chronicle, Entity, EntityAttribute, Player, ScopeGrant, Utterance
from narrative_engine.read_only_admin import ReadOnlyAdmin, ReadOnlyInline


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0


@admin.register(Chronicle)
class ChronicleAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "created_at"]
    list_filter = ["kind"]
    search_fields = ["title"]
    inlines = [PlayerInline]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ["name", "chronicle", "implicit"]
    list_filter = ["implicit"]


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ["canonical_name", "slug", "kind", "chronicle", "introduced_at_t"]
    list_filter = ["kind"]
    search_fields = ["canonical_name", "slug"]


@admin.register(Utterance)
class UtteranceAdmin(ReadOnlyAdmin):
    list_display = ["__str__", "chronicle", "speaker_player", "speaker_entity"]


class ScopeGrantInline(ReadOnlyInline):
    model = ScopeGrant
    fk_name = "beat"
    fields = ["character", "player", "t", "via_beat"]


@admin.register(Beat)
class BeatAdmin(ReadOnlyAdmin):
    list_display = ["t", "pred", "text", "chronicle", "source_kind", "confidence", "is_quarantined"]
    list_filter = ["pred", "source_kind"]
    search_fields = ["text"]
    inlines = [ScopeGrantInline]


@admin.register(ScopeGrant)
class ScopeGrantAdmin(ReadOnlyAdmin):
    list_display = ["__str__", "beat", "t", "via_beat"]


@admin.register(EntityAttribute)
class EntityAttributeAdmin(ReadOnlyAdmin):
    list_display = ["entity", "key", "value", "source_beat"]
