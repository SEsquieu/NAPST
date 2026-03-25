# NAPST architecture notes

## Hard edges

NAPST is built around a strict split:

1. **Core engine**
   - target model
   - scenario packs
   - invocation
   - result normalization
   - inference
   - artifact storage
   - reporting

2. **CLI**
   - thin operator surface
   - no business logic
   - easy automation and CI integration

3. **UI**
   - optional local browser layer
   - reads saved artifacts
   - should never become the only way to use the system

## Core nouns

- **Target**: description of the system entrypoint and request/response shape
- **Scenario**: ordered set of probes intended to surface a class of behavior
- **Probe**: individual prompt payload and tags
- **Run**: execution of a scenario against a target
- **Finding**: inferred risk or boundary statement from a run
- **Artifact**: saved output from a run

## MVP goals

- make black-box probing repeatable
- move from raw responses to usable findings
- leave room for gray-box trace adapters later

## Deliberate limits

- inference is probabilistic, not proof
- black-box mode cannot directly observe real tool calls
- current transport is HTTP JSON only
- findings are heuristics and should trigger investigation, not replace it
