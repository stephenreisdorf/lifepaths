# Life Path Config Authoring Reference

A life path config defines a branching sequence of narrative stages that a player moves through during character creation. Each stage contains events (dice rolls, choices, or automatic effects) that modify the character's attributes and grant features.

## File Discovery

Place config files in `backend/content/stages/`. The loader accepts `.yaml`, `.yml`, and `.json` extensions. Files are processed in alphabetical order by filename. If two files declare the same `id`, the server raises an error and refuses to start.

---

## Root Config Fields

```yaml
id: my_lifepath           # Unique identifier across all loaded configs
name: My Life Path        # Display name
version: "1.0"            # Free-form version string (use quotes to avoid YAML parsing as float)
starting_stage_id: intro  # ID of the first stage the player enters
base_attributes:          # Starting attribute values before any stage effects
  strength: 2
  wealth_level: 1
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Must be unique across all loaded files |
| `name` | string | yes | Human-readable title |
| `version` | string | yes | No format enforced; quote it to be safe |
| `starting_stage_id` | string | yes | Must match a key in `stages` |
| `base_attributes` | map\<string, int\> | no | Defaults to empty map |

---

## Stages

The `stages` field is a map whose keys are stage IDs. Each value is a `StageDefinition`.

```yaml
stages:
  childhood:      # This key must equal the stage's id field
    id: childhood
    name: Childhood
    ...
```

### StageDefinition Fields

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | string | — | Must match the map key |
| `name` | string | — | Display name |
| `description` | string | — | Narrative description shown to the player |
| `order_hint` | int | `null` | Optional UI ordering hint; not enforced by the engine |
| `age_cost` | int | `0` | Years added to the character's age when this stage completes |
| `default_next_stage_id` | string | `null` | Stage entered after this one completes. `null` marks a terminal stage |
| `is_repeatable` | bool | `false` | If `true`, the player may repeat the stage after completing it |
| `max_repeats` | int | `null` | Maximum additional completions beyond the first. `null` = unlimited |
| `repeat_prompt` | string | `null` | Text shown to the player when offered the option to repeat |
| `prerequisite_stage_ids` | list\<string\> | `[]` | All listed stages must be completed before this stage is accessible |
| `prerequisite_features` | list\<string\> | `[]` | Feature IDs the character must possess to enter this stage |
| `prerequisite_attribute_minimums` | map\<string, int\> | `{}` | Attribute values the character must meet or exceed |
| `events` | list\<EventDefinition\> | `[]` | Ordered list of events the player resolves during this stage |

**Terminal vs. non-terminal stages:** A stage with `default_next_stage_id: null` ends character creation (unless an outcome's `next_stage_override` redirects elsewhere).

**Repeatable stages:** When a stage has `is_repeatable: true`, after the player resolves all events the server asks whether to repeat. Each additional completion costs another `age_cost` and runs the events again. The `max_repeats` cap counts completions *after* the first (so `max_repeats: 3` allows up to 4 total completions). Use `POST /api/sessions/{id}/advance` with `repeat_stage: true/false` to respond.

---

## Events

Events are the interactive elements within a stage. They are resolved in list order.

### EventDefinition Fields

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | string | — | Unique within the stage |
| `name` | string | — | Display name |
| `description` | string | — | Narrative description |
| `event_type` | enum | — | `table_roll`, `choice`, or `automatic` |
| `is_optional` | bool | `false` | If `true`, the player may skip this event |
| `outcomes` | list\<OutcomeDefinition\> | `[]` | Possible results |
| `dice_expression` | string | `null` | **`table_roll` only** — dice formula (see Dice Expression Syntax) |
| `choice_prompt` | string | `null` | **`choice` only** — question shown to the player |
| `min_choices` | int | `1` | **`choice` only** — minimum outcomes the player must select |
| `max_choices` | int | `1` | **`choice` only** — maximum outcomes the player may select |

### Event Types

#### `table_roll`

The player (or the system) rolls dice and the result selects an outcome by range.

- Requires `dice_expression`.
- Every outcome must have `roll_min` and `roll_max`.
- Outcomes must collectively cover the entire possible range of the dice expression without gaps or overlaps.

```yaml
event_type: table_roll
dice_expression: 2d6
outcomes:
  - id: low
    label: Low Roll
    roll_min: 2
    roll_max: 7
    ...
  - id: high
    label: High Roll
    roll_min: 8
    roll_max: 12
    ...
```

#### `choice`

The player picks one or more outcomes from a list.

- Requires `choice_prompt`.
- Every outcome must have a unique `choice_key`.
- `min_choices` and `max_choices` control how many options the player must/may pick.

```yaml
event_type: choice
choice_prompt: Which path will you follow?
min_choices: 1
max_choices: 1
outcomes:
  - id: warrior_path
    label: Warrior
    choice_key: warrior
    ...
  - id: scholar_path
    label: Scholar
    choice_key: scholar
    ...
```

#### `automatic`

No player input. The single outcome is applied unconditionally.

- Typically has exactly one outcome (the engine applies the first/only one).
- Useful for guaranteed events that always happen at a stage.

```yaml
event_type: automatic
outcomes:
  - id: you_age
    label: Time Passes
    description: Another year goes by.
    attribute_modifiers:
      - attribute: age
        delta: 1
```

### Optional Events

Setting `is_optional: true` adds a skip option. The player may call `POST /api/sessions/{id}/events/{event_id}/skip` to bypass the event with no effect applied.

---

## Dice Expression Syntax

Dice expressions follow the pattern:

```
[N]d<sides>[+/-<bonus>]
```

| Part | Description | Example |
|---|---|---|
| `N` | Number of dice (optional, defaults to 1) | `2` in `2d6` |
| `sides` | Number of sides per die (required) | `6` in `2d6` |
| `+/-bonus` | Flat modifier (optional, defaults to 0) | `+3` in `1d20+3` |

### Valid Examples

| Expression | Min | Max |
|---|---|---|
| `d6` | 1 | 6 |
| `2d6` | 2 | 12 |
| `1d20+3` | 4 | 23 |
| `3d8-2` | 1 | 22 |
| `d100` | 1 | 100 |

### Range Computation

```
minimum = count × 1 + bonus   (all dice show 1)
maximum = count × sides + bonus  (all dice show max)
```

For `table_roll` events, the `roll_min`/`roll_max` values across all outcomes must exactly cover `[minimum, maximum]` with no gaps or overlaps, otherwise rolls outside any outcome's range will result in a runtime error.

---

## Outcomes

An `OutcomeDefinition` describes what happens when a particular result is selected.

### OutcomeDefinition Fields

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | string | — | Unique within the event |
| `label` | string | — | Short display name |
| `description` | string | — | Narrative description of this outcome |
| `roll_min` | int | `null` | **`table_roll` only** — inclusive lower bound |
| `roll_max` | int | `null` | **`table_roll` only** — inclusive upper bound |
| `choice_key` | string | `null` | **`choice` only** — identifier the player submits to select this outcome |
| `attribute_modifiers` | list\<AttributeModifier\> | `[]` | Attribute changes applied when this outcome resolves |
| `features_granted` | list\<Feature\> | `[]` | Features added to the character when this outcome resolves |
| `next_stage_override` | string | `null` | If set, overrides the stage's `default_next_stage_id` and routes to this stage instead |
| `triggers_events` | list\<string\> | `[]` | Event IDs within the **same stage** that are injected into the event queue after this outcome resolves |

### Routing

By default a stage advances to its `default_next_stage_id` after all events are resolved. An outcome can override this by setting `next_stage_override` to a different stage ID — useful for branching narratives.

### Event Chaining

`triggers_events` injects additional events into the current stage's processing queue. All referenced IDs must be events defined within the same stage. This lets a single outcome conditionally activate follow-up events without requiring a separate stage.

---

## Attribute Modifiers

`AttributeModifier` is a simple signed delta applied to a named attribute.

| Field | Type | Notes |
|---|---|---|
| `attribute` | string | Any string — attributes are created on first use |
| `delta` | int | Positive or negative integer added to the current value |

Attributes not listed in `base_attributes` implicitly start at `0`.

```yaml
attribute_modifiers:
  - attribute: strength
    delta: 2
  - attribute: wealth_level
    delta: -1
```

---

## Features

`Feature` represents a persistent trait, skill, contact, injury, or other narrative marker attached to the character.

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | string | — | Unique identifier for this feature |
| `name` | string | — | Display name |
| `description` | string | — | Narrative description |
| `category` | string | `null` | Free string: `"skill"`, `"trait"`, `"contact"`, `"injury"`, etc. |
| `source_stage_id` | string | `null` | Stage where this feature was acquired (for display/tracking) |
| `source_event_id` | string | `null` | Event where this feature was acquired (for display/tracking) |

```yaml
features_granted:
  - id: street_smart
    name: Street Smart
    description: Hard times taught you to read people and situations quickly.
    category: trait
    source_stage_id: childhood
    source_event_id: childhood_upbringing
```

The `category` field is not validated by the engine — use any string that makes sense for your system. `source_stage_id` and `source_event_id` are cosmetic; they are recorded in the event log for provenance but have no mechanical effect.

---

## Validation Rules

### At Load Time (`validate_cross_references`)

These checks run when the server starts. Any failure prevents startup.

- `starting_stage_id` must be a key in `stages`.
- Every stage's `default_next_stage_id` (if non-null) must be a key in `stages`.
- Every ID in a stage's `prerequisite_stage_ids` must be a key in `stages`.
- Every outcome's `next_stage_override` (if non-null) must be a key in `stages`.
- Every ID in an outcome's `triggers_events` must be the `id` of an event in the **same stage**.
- Duplicate config `id` values across files raise an error (checked in the loader, not the model).

### At Runtime

These checks run during a session.

- Roll results submitted to `table_roll` events must fall within `[minimum, maximum]` for the dice expression.
- The number of choices submitted to a `choice` event must satisfy `min_choices ≤ n ≤ max_choices`.
- A stage cannot be entered unless all `prerequisite_stage_ids` have been completed in the current session.
- A stage cannot be entered unless the character possesses all `prerequisite_features`.
- A stage cannot be entered unless all `prerequisite_attribute_minimums` are satisfied.
- A repeatable stage cannot be repeated beyond `max_repeats` additional completions.
- Only events with `is_optional: true` may be skipped.

---

## Complete Annotated Example

The following is `backend/content/stages/example_lifepath.yaml` with inline comments.

```yaml
# Root config fields
id: example_lifepath        # Unique ID; must not collide with other loaded configs
name: Example Life Path     # Display name
version: "1.0"              # Quoted to prevent YAML from parsing as float
starting_stage_id: childhood  # First stage; must exist in stages map

# Starting attribute values for every character using this life path
base_attributes:
  strength: 2
  agility: 2
  intellect: 2
  wealth_level: 1

stages:
  # ── Stage 1: Childhood ────────────────────────────────────────────────────
  childhood:
    id: childhood           # Must match the map key above
    name: Childhood
    description: Your formative years shape who you will become.
    order_hint: 1           # UI hint: render this stage first
    age_cost: 10            # Character ages 10 years when this stage completes

    # After resolving all events, advance to the youth stage
    default_next_stage_id: youth

    events:
      # Event 1: table_roll — random upbringing
      - id: childhood_upbringing
        name: Upbringing
        description: Roll to determine the circumstances of your childhood.
        event_type: table_roll
        dice_expression: 1d6    # Range: 1–6; outcomes below must cover [1,6]

        outcomes:
          - id: upbringing_poor
            label: Poor
            description: You grew up in poverty, learning to make do with little.
            roll_min: 1           # Applies when roll is 1 or 2
            roll_max: 2
            attribute_modifiers:
              - attribute: wealth_level
                delta: -1         # Subtract 1 from wealth_level
              - attribute: agility
                delta: 1
            features_granted:
              - id: street_smart
                name: Street Smart
                description: Hard times taught you to read people and situations quickly.
                category: trait             # Free string; not validated by engine
                source_stage_id: childhood  # Provenance fields; cosmetic only
                source_event_id: childhood_upbringing

          - id: upbringing_middle
            label: Middle Class
            description: A comfortable upbringing with modest opportunities.
            roll_min: 3           # Applies when roll is 3 or 4
            roll_max: 4
            attribute_modifiers: []   # No attribute changes
            features_granted: []

          - id: upbringing_wealthy
            label: Wealthy
            description: You grew up with privilege and access to education.
            roll_min: 5           # Applies when roll is 5 or 6
            roll_max: 6           # Together, outcomes 1–6 cover the full 1d6 range
            attribute_modifiers:
              - attribute: wealth_level
                delta: 1
              - attribute: intellect
                delta: 1
            features_granted:
              - id: educated
                name: Educated
                description: Formal schooling has broadened your mind.
                category: trait
                source_stage_id: childhood
                source_event_id: childhood_upbringing

      # Event 2: choice — player picks a talent
      - id: childhood_talent
        name: Natural Talent
        description: Choose an area where you showed early aptitude.
        event_type: choice
        choice_prompt: Which talent emerged during your childhood?
        min_choices: 1    # Player must pick exactly one
        max_choices: 1

        outcomes:
          - id: talent_physical
            label: Physical
            description: You excelled at sports and physical activities.
            choice_key: physical    # Player submits this string to select the outcome
            attribute_modifiers:
              - attribute: strength
                delta: 1
            features_granted: []

          - id: talent_mental
            label: Mental
            description: You had a knack for learning and problem-solving.
            choice_key: mental
            attribute_modifiers:
              - attribute: intellect
                delta: 1
            features_granted: []

  # ── Stage 2: Youth ────────────────────────────────────────────────────────
  youth:
    id: youth
    name: Youth
    description: Your adolescent years and early independence.
    order_hint: 2
    age_cost: 6
    default_next_stage_id: career

    # childhood must be completed before this stage is accessible
    prerequisite_stage_ids:
      - childhood

    events:
      - id: youth_event
        name: Defining Moment
        description: Something happened in your youth that left a mark.
        event_type: table_roll
        dice_expression: 1d6

        outcomes:
          - id: youth_adventure
            label: Adventure
            description: A chance encounter led you into brief adventure.
            roll_min: 1
            roll_max: 3
            attribute_modifiers:
              - attribute: agility
                delta: 1
            features_granted: []

          - id: youth_scholarship
            label: Scholarship
            description: Your academic abilities earned you a rare opportunity.
            roll_min: 4
            roll_max: 6
            attribute_modifiers:
              - attribute: intellect
                delta: 1
            features_granted:
              - id: scholar
                name: Scholar
                description: Rigorous study has sharpened your analytical mind.
                category: skill
                source_stage_id: youth
                source_event_id: youth_event

  # ── Stage 3: Career ───────────────────────────────────────────────────────
  career:
    id: career
    name: Career
    description: You enter the workforce and find your calling.
    order_hint: 3
    age_cost: 4             # Each career term costs 4 years

    is_repeatable: true     # Player may repeat this stage
    max_repeats: 3          # Up to 3 additional completions (4 total)
    repeat_prompt: Do you wish to continue in this career for another term?

    default_next_stage_id: null   # null = terminal stage; character creation ends here

    prerequisite_stage_ids:
      - youth

    events:
      - id: career_assignment
        name: Assignment
        description: Roll to see what work comes your way this term.
        event_type: table_roll
        dice_expression: 1d6

        outcomes:
          - id: career_rough
            label: Rough Term
            description: This term was hard. You earned little but learned much.
            roll_min: 1
            roll_max: 2
            attribute_modifiers:
              - attribute: strength
                delta: 1
            features_granted: []

          - id: career_steady
            label: Steady Work
            description: Solid, unremarkable employment.
            roll_min: 3
            roll_max: 4
            attribute_modifiers:
              - attribute: wealth_level
                delta: 1
            features_granted: []

          - id: career_windfall
            label: Windfall
            description: A lucrative contract or lucky break.
            roll_min: 5
            roll_max: 6
            attribute_modifiers:
              - attribute: wealth_level
                delta: 2
            features_granted:
              - id: well_connected
                name: Well Connected
                description: Success brought you into contact with influential people.
                category: contact   # "contact" is a designer-defined category string
                source_stage_id: career
                source_event_id: career_assignment
```
