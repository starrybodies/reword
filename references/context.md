# Contexts

Context is the whole situation a piece is written for: the reader, what they need, the author's relationship to them, and where the piece appears. Reword carries it at three levels.

1. A **destination** names the channel and sets surface defaults. The table below lists the built-in ones.
2. A **task brief** states this occasion. Pass `--audience`, `--purpose` and `--context` for anything the destination does not say, such as a membership application read by a committee or a reply to a customer who is upset.
3. A **named context** saves a recurring occasion with its own evidence and preferences. See [named contexts](#named-contexts).

The built-in destinations are examples of channels. Work that matches none of them uses the nearest one, or `general`, together with a task brief.

A destination changes how an author's voice is expressed. Keep their word choice, rhythm, imagery, humor, warmth and other distinctive habits active while fitting the reader and purpose. These policies are instructions for an editor or model, not filters that lowercase or respell finished text.

Choose a destination explicitly when it is known. `auto` uses a single destination named in audience, purpose or context, or clear email headers in the source. Mixed destination signals, a vague "message", casual wording, and the reader's relationship to the author are insufficient: use `general`. An unknown explicit destination also falls back to `general`; it does not trigger another guess. `general` preserves the source register and assumes no intimacy.

| Destination | Default surface style |
| --- | --- |
| `text-message` | Preserve the author's case; natural lowercase is welcome when supported. Light punctuation, natural contractions and fitting familiar abbreviations. Reuse colloquial spellings only when present in supplied samples. |
| `chat` | Conversational at the reader's level of familiarity, light punctuation and fitting familiar abbreviations; retain the author's spelling. |
| `email` | Appropriate capitalization, standard punctuation and spelling, natural contractions; spell out casual abbreviations. |
| `linkedin` | Public professional prose with appropriate capitalization, punctuation and spelling; preserve the author's character. |
| `cover-letter` | Specific professional prose with appropriate capitalization, punctuation and spelling; preserve the author's character. |
| `essay` | Standard surfaces; retain the author's argument, rhythm, devices and contraction habits. |
| `web-copy` | Standard surfaces, natural contractions and fitting familiar abbreviations; clear movement toward the reader's task. |
| `agent` | The reader is a model that acts on the text. Surface habits and prose voice are left out. See [agent readers](agents.md). |
| `general` | Preserve author/source habits and register. |

No default requires slang, deliberate errors or an intimate register. Keep proper names, acronyms, quoted text, URLs, code and meaning-sensitive punctuation intact. Regional spelling affects editable prose, not protected material. A lowercase preference never authorizes indiscriminate lowercasing.

## Named contexts

A named context is written `DESTINATION/NAME`: a built-in destination, a slash, then up to 40 lowercase letters, digits or hyphens. `chat/family` and `chat/work` are two chats with different tones. `web-copy/acme` and `web-copy/northwind` are copy for two ventures. `general/membership-application` is an occasion with no closer channel.

A named context inherits its destination's surface defaults and examples. Its own material layers on top in this order: `general`, then the destination, then the named context. That order applies to style options, explicit preferences, avoid entries and learned traits. Evidence tagged with one named context never reaches a sibling, so `chat/family` habits stay out of `chat/work`.

Nothing has to be declared first. A named context exists once a sample, a preference or a learned profile carries its name.

```bash
python3 scripts/reword.py voice add STORE thread.md --destination chat/family --label 'Family group chat'
python3 scripts/reword.py voice feedback STORE --kind preference --destination chat/family --prefer 'Tease gently' --avoid 'Work vocabulary'
python3 scripts/reword.py voice refine STORE --destination chat/family
python3 scripts/reword.py prompt draft.md --destination chat/family --voice STORE
```

State who reads the context and what tone it takes as an explicit preference, so the description travels with every request. `voice status STORE` lists the saved names under `named_contexts`, and every `prompt` that uses a collection repeats the list in `meta.voice_collection`. Choose from that list before coining a name, because a misspelled name starts a new, empty context.

`auto` never infers a named context. The resolver accepts spaces and capitals in a requested name and normalizes them. Collection commands require the exact canonical form. A name under an unknown destination falls back to `general`.

## Profile schema

`contexts` is an optional object whose keys are destinations from the table or named contexts. Each value is a small object containing any of these options. Unknown keys and values are rejected.

| Option | Allowed values |
| --- | --- |
| `case` | `preserve`, `sentence`, `lowercase` |
| `punctuation` | `preserve`, `standard`, `light` |
| `spelling` | `preserve`, `standard`, `sampled-colloquial` |
| `regional_spelling` | `preserve`, `US`, `UK`, `CA` |
| `abbreviations` | `preserve`, `familiar`, `avoid` |
| `contractions` | `preserve`, `natural`, `avoid` |

`preserve` retains the author's relevant choices. `sentence` means appropriate capitalization, including proper names. `standard` uses conventional punctuation or spelling. `light` removes unnecessary punctuation while retaining boundaries needed for meaning. `sampled-colloquial` permits only supplied colloquial spellings; it does not create typos. `familiar` permits understandable abbreviations when fitting; it does not require them. The regional option overrides the source's regional spelling only when explicitly set to `US`, `UK` or `CA`.

Merge order is destination defaults, then `contexts.general`, then `contexts[chosen_destination]`, then `contexts[named_context]` when one is chosen, then explicit per-call overrides. Explicit user preferences take priority over inferred habits and defaults. A general preference therefore applies everywhere unless a destination-specific preference or per-call override replaces it.

```json
{
  "contexts": {
    "general": {"regional_spelling": "UK", "contractions": "natural"},
    "text-message": {"case": "lowercase", "punctuation": "light"},
    "linkedin": {"case": "sentence", "punctuation": "standard", "spelling": "standard"},
    "cover-letter": {"case": "sentence", "punctuation": "standard", "spelling": "standard"}
  },
  "traits": {
    "vocabulary": "Concrete words with occasional odd but apt images",
    "rhythm": "Longer thoughtful turns, followed by a short landing",
    "transitions": "Move through the idea rather than announcing sections"
  }
}
```

Optional `traits` records distilled semantic style observations. Allowed keys are `vocabulary`, `rhythm`, `openings`, `transitions`, `emotional_register` and `devices`; each value is a nonempty string of at most 120 characters. Use repeated evidence or explicit author preferences, not a personality diagnosis. A sample supplies style, never facts or experiences for another text. Store a profile or new feedback only when the writer authorizes it.

## Python API

`scripts/voice_context.py` uses only the standard library and never saves profiles, calls a model or changes prose.

```python
from voice_context import compact_voice, render_style_card, resolve_context

preferences = {**profile.get("contexts", {}), "regional_spelling": "CA"}
resolved = resolve_context("email", text=draft, audience=reader, preferences=preferences)
destination_card = render_style_card(resolved)  # At most 600 characters.
author_card = compact_voice(profile, destination=resolved)
```

`resolve_context(destination="auto", *, text="", audience="", purpose="", context="", preferences=None)` returns the canonical `destination`, complete `style`, `source` (`explicit`, `inferred` or `fallback`), `confidence` (`explicit`, `high` or `low`), a short `reason` and destination `guidance`. Confidence describes the resolution rule, not a calibrated probability. `preferences` accepts a profile's destination map, flat per-call style options, or both in one object. `validate_context_preferences(mapping)` validates the strict nested profile shape; flat options belong only to the resolver's per-call input. `validate_voice_traits(mapping)` validates traits.

`compact_voice(profile, destination="general")` returns an author card containing all explicit preferences and avoid entries, structured traits and any useful fact-free sample surface observations. It does not reproduce sample events or invent traits. Pass a resolved context as `destination` when per-call style overrides are present; a destination string instead uses that profile's contexts. Derived lowercase, abbreviated or colloquial habits are omitted where the selected style disallows them. Distinctive rhythm and vocabulary should still carry into formal writing.

When samples have no distilled traits, the card marks `needs_sample_context: true`. Keep those supplied samples separately as style-only input so the model can observe vocabulary, movement, openings and transitions; numeric or surface observations alone are not a voice. `compact_voice` does not silently learn or persist those observations. Existing explicit preferences are retained without truncation.

`style_findings(text, resolved, *, visible=None)` returns at most eight `{kind, quote, reason}` suggestions for surface choices that may conflict with the resolved policy: contractions when `contractions` is `avoid`, clearly informal lowercase abbreviations when abbreviations are avoided or spelling is standard, colloquial shortenings when spelling is standard, and common lowercase sentence openings or pronoun `i` when case is `sentence`. Repeated findings for the same kind and text are deduplicated. It changes no text, validates no claims, and does not provide full spelling or grammar validation.

Pass the existing protected-prose mask as `visible` for precise exclusions; it must retain the source's character offsets and length. Without it, conservative local masking excludes quoted text, code, URLs and link targets. The checks skip possessive `'s`, uppercase acronyms, camelCase and uncommon sentence-opening words rather than guessing how a proper name should be capitalized. Ordinary contractions remain allowed unless explicitly avoided; default text-message and chat policies do not penalize natural lowercase, light punctuation or fitting informal abbreviations. Findings are review suggestions, never automatic corrections.
