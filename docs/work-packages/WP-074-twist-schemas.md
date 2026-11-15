# WP-074: Twist schemas

**Milestone:** M3 (follow-up) · **Serves:** RQ1, RQ3

## Goal
A plot point is a single beat that makes the audience reinterpret what came before. The library
reads the kinds of twist that the existing predicate vocabulary can express, so that the engine
can see them coming in prose and play and a story writer can aim for them. Identity and kinship
reveals need new predicates and follow in WP-075.

| Twist | Classic examples | Schema |
|---|---|---|
| A too simple belief is replaced by a better one | Elizabeth after Darcy's letter | `revised_belief` |
| The world or the time order was not what it seemed | *The Others*, *Planet of the Apes*, *Arrival* | `revised_belief` |
| A character was lying and loses trust | Wickham | `exposed_lie` |
| The narrator kept back what they did | *The Murder of Roger Ackroyd* | `unreliable_narrator` |
| A deed was credited to the wrong person | Pip's benefactor, Quirrell not Snape | `false_attribution` |
| A suspected enemy was secretly loyal | Snape | `hidden_loyalty` |
| A prophecy comes true through a loophole | Macduff, Croesus | `prophecy_loophole` |
| A hidden plan or con | *The Sting* | `con` |

## Acceptance criteria
- `revised_belief`: a belief about what someone is, where they are or what they want seeds a
  reading; it completes when the believer learns what that person really is, where they are or
  what they want (as a proposition, or by learning a fact beat that came after the belief).
- `exposed_lie`: a claim seeds a reading; it completes when someone the liar told it to (or
  anyone) stops believing that claim, or learns that the liar hid something.
- `unreliable_narrator`: what a narrator tells the audience seeds a reading; it completes when the
  audience comes to know a deed of the narrator that happened before the narrator told them.
  A deed the audience knew from the start does not complete it.
- `false_attribution`: believing that someone did a deed seeds a reading; it completes when the
  believer learns that someone else did it. The two must be different people.
- `hidden_loyalty`: distrusting someone seeds a reading; it completes when the distrustful
  character learns that this person helped, protected, saved or allied with someone.
- `prophecy_loophole`: a foretelling about what someone is seeds a reading; it completes when that
  person learns what someone else is (the loophole), which must come after the foretelling.
- `con`: the mark's trust in a schemer seeds a reading; the mark hands something over, and the
  reading completes when someone learns that the schemer was allied with an accomplice.
- Twist readings start weak (prior −4, a small weight for the beat that seeds them) and gain weight
  when the twist pays off, so that the main plot keeps most of the belief in the example stories.
- The schema library usage doc lists the new schemas; the test settings keep pinning the schemas
  the matcher's tests were written against; the usage docs and browser tests describe what the
  example stories show with the twists loaded.

## Dependencies
WP-011, WP-012, WP-014, WP-060, WP-073.

## Out of scope
Negation (a beat establishing ¬P for a claim P, concept §4.1): the lie is read from explicit beats
of distrust or concealment. Identity and kinship reveals (WP-075). Example stories for the new
schemas and tuning their weights against a corpus.

## Status
done

## Summary
Seven YAML schemas with tests in `schemas/tests/test_twist_readings.py`; the helpers for running
library schemas moved to `schemas/tests/readings.py`. Because they start from common beats, the
twist schemas have a prior of −4 and seed at −3.5, well below the plot schemas. In The Broken Jug
the players now also weigh the judge (or Frau Marthe) lying, so before the confession their tension
is above 60 % instead of 80 % (pacing doc, river test and browser test updated); the confession
still releases it and surprises everyone. Anna's lattice is no longer empty before beat 16 (tour
updated), and the evidence matrix lists the twists as 0 % columns. Pointing at a step mark in the
river now shows its band's tooltip instead of nothing (the twists moved a mark under the pointer of
*Read a band*).
