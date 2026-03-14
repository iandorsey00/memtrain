# Study Set Format

memtrain study sets are authored as CSV files.

## Minimal example

```csv
Animals
Cue,Response,Hint,Tag
{{}} make milk.,Cows,Mooo,Ungulates
You can ride on a {{}}.,horse,Neigh,Ungulates
```

The first single-value row is treated as the study set title.

The next row containing both `Cue` and `Response` is treated as the column header row.

## Core columns

- `Cue`: the authored prompt shown to the learner
- `Response`: the primary accepted answer
- `Hint`: an optional hint used in Level 2
- `Tag`: an optional filtering tag

## Supported optional columns

- `Response2`, `Response3`
- `Synonym`, `Synonym2`, `Synonym3`
- `Hint2`, `Hint3`
- `Tag` in multiple columns
- `MTag`
- `Id`, `Id2`, `Id3`

## Cue placeholders

memtrain supports placeholders inside cues:

- `{{}}`: a generic blank
- `{{1}}`, `{{2}}`, `{{3}}`: numbered blanks for multi-response cues

## How responses work

- `Response` is the default answer shown after grading
- `Synonym` values are also treated as correct answers
- `Response2` and `Response3` create additional answer slots for the same cue row

## Tags and mtags

- `Tag` is for filtering study sessions
- `MTag` is for grouping related answers so Level 1 can generate more plausible distractors

## Stable IDs

If you provide `Id`, `Id2`, or `Id3`, memtrain uses them as the stable learner-progress identifier for that answer item.

If you do not provide explicit IDs, memtrain falls back to a derived ID based on cue and response text.

Explicit IDs are recommended if you expect prompts or wording to evolve over time.

## CSV settings row

A top-of-file settings row can be used before the header row:

```csv
settings: !level1, level2, level3, nquestions=20
```

Supported settings:

- `level1`
- `level2`
- `level3`
- `!level1`, `!level2`, `!level3`
- `nquestions=<int>`

## Authoring guidance

- Keep cues specific and exam-like.
- Use hints to support partial recall, not to give away the full answer.
- Use synonyms for genuinely accepted alternate answers.
- Use tags to create focused sessions by topic.
- Use `MTag` to group confusable answers for better multiple choice.
- Prefer explicit IDs once a study set becomes important.
