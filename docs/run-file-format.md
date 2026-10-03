# Run file format (`chronicler-run/1`)

`manage.py replay <story>` writes one JSON file per run to
`backend/evaluation/runs/<story>/<UTC timestamp>.json` (git-ignored). The evaluation harness
(WP-040 onwards) reads it.

```jsonc
{
  "format": "chronicler-run/1",
  "story": "steward",                 // fixture slug
  "chronicle": 12,                    // id of the chronicle the run was built into
  "created_at": "2026-10-03T20:41:07+00:00",
  "reader": "UniformReader",          // class of the reader model, or null for a lattice-only run
  "matcher": {"repeatable_fill_cap": 3, "weight_floor": -6.0, "max_live_per_schema": 50},
  "players": {"3": "Anna", "4": "Ben"},
  "entities": {"17": {"slug": "aldric", "name": "Aldric", "kind": "character"}},
  "beats": [{"t": 1, "pred": "is_at", "text": "Mira holds court…", "quarantined": false}],
  "timeline": [                       // one entry per t, from 0 (before the first beat) to the last beat
    {
      "t": 13,
      "lattice": {                    // per audience: "all" is the unfiltered lattice, else a player name
        "all": [
          {
            "id": 40, "schema": "betrayal",
            "binding": {"T": 17, "V": 16, "S": 21},   // entity ids (see "entities"), null = open
            "status": "live",                          // as held at this t
            "weight": 1.0,                             // recomputed from the fills up to this t
            "created_at_t": 7, "status_changed_at_t": null,
            "fills": [["trust", 2], ["access", 7], ["harm", 13]],   // [step, beat t]
            "refines": 38, "merged_into": null, "refuted_by_t": null, "voiced_by": null
          }
        ]
      },
      "expectations": [               // readouts computed at this t
        {
          "hypothesis": 38, "step": "access", "for_player": null,
          "question": "Next: Aldric learns that Mira hides ___.",
          "candidates": [{"label": "A", "text": "The family seal", "binding_delta": {"S": 21}, "p": 0.5},
                         {"label": "B", "text": "nothing like this yet", "null": true, "p": 0.5}],
          "outside_mass": 0.0, "llm_call": 7
        }
      ]
    }
  ],
  "llm_calls": [7, 8, 9]              // ids of the LLMCall rows the run used
}
```

Hypothesis ids are only meaningful within one run; compare runs by schema, binding (via entity
slugs) and fills.
