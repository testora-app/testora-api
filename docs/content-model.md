# Content Model: Subjects, Themes, Topics & Questions

This document describes the academic content hierarchy in `testora-api` and how
each layer ties into questions. All models live under `app/app_admin/models.py`
(Subject, Theme, Topic) and `app/test/models.py` (Question, SubQuestion,
QuestionImage), and all inherit `BaseModel` (`app/_shared/models.py`), which adds
`is_deleted`, `created_at`, and `updated_at` to every table.

## Hierarchy at a glance

```
Subject  (e.g. "Integrated Science", curriculum: bece/igsce)
  └── Theme        (a grouping of topics within a subject)
        └── Topic        (the taggable unit, carries a difficulty `level`)
              └── Question        (belongs to exactly one Topic)
                    ├── SubQuestion   (0..n, child parts of a question)
                    └── QuestionImage (0..n, image/answer-image URLs)
```

The content tree is **Subject → Theme → Topic**. A **Question hangs off a Topic**,
and a Question owns its **SubQuestions** and **QuestionImages**.

> Note: `Topic` carries both `theme_id` *and* a denormalized `subject_id`, so a
> Topic points directly at its Subject in addition to reaching it via its Theme.

---

## Subject

Table: `subject` — `app/app_admin/models.py:33`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | Integer | PK | |
| `name` | String(100) | NOT NULL | e.g. "Integrated Science" |
| `short_name` | String(20) | NOT NULL, **unique** | |
| `curriculum` | String(20) | NOT NULL | e.g. `bece`, `igsce` |
| `max_duration` | Integer | nullable, default `3000` | test duration cap, in seconds |
| `is_premium` | Boolean | default `False` | gates premium content |

**Relationships**
- `staff` — many-to-many with `Staff` via the `staff_subjects` association table
  (`back_populates="subjects"`). Lets staff be scoped to the subjects they own.
- Referenced by `Theme.subject_id` and `Topic.subject_id`.
- Referenced by `Test.subject_id` (a test is taken for one subject).

A Subject does **not** hold a direct relationship to Questions — questions are
reached through its Topics.

---

## Theme

Table: `theme` — `app/app_admin/models.py:59`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | Integer | PK | |
| `name` | String(100) | NOT NULL | |
| `short_name` | String(20) | NOT NULL, **unique** | |
| `subject_id` | Integer | FK → `subject.id`, NOT NULL | parent subject |

**Relationships**
- `topics` — one-to-many to `Topic` (`backref="theme"`).
- Belongs to one `Subject` via `subject_id`.

A Theme is purely an organizational grouping between Subject and Topic. Its
`to_json()` nests its topics, so the API can return a Subject's full theme→topic
tree in one shape.

---

## Topic

Table: `topic` — `app/app_admin/models.py:80`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | Integer | PK | |
| `name` | String(100) | NOT NULL | |
| `short_name` | String(20) | NOT NULL, **unique** | |
| `level` | Integer | NOT NULL | difficulty/grade level of the topic |
| `theme_id` | Integer | FK → `theme.id`, NOT NULL | parent theme |
| `subject_id` | Integer | FK → `subject.id`, NOT NULL | denormalized parent subject |

**Relationships**
- `theme` — parent Theme (`backref` from `Theme.topics`).
- `questions` — one-to-many to `Question` (`back_populates="topic"`).
- Belongs to one `Subject` directly via `subject_id`.

The **Topic is the join point to questions**: every Question must reference a
Topic. The Topic's `level` is surfaced onto each question at serialization time
(see below), so difficulty is a property of the Topic, not stored per-question.

---

## Question

Table: `question` — `app/test/models.py:6`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | Integer | PK | |
| `text` | Text | NOT NULL | |
| `correct_answer` | Text | nullable | |
| `possible_answers` | Text | nullable | stored as a **stringified Python list**, parsed back with `ast.literal_eval` |
| `topic_id` | Integer | FK → `topic.id`, NOT NULL | the tie to the content tree |
| `points` | Integer | nullable, default `None` | |
| `school_id` | Integer | FK → `school.id`, nullable | `null` = global/shared; set = school-owned question |
| `is_flagged` | Boolean | default `False` | |
| `flag_reason` | Text | nullable | stored as a JSON string of reasons |
| `year` | Integer | nullable | exam year |
| `is_instructional` | Boolean | default `False` | |

**Relationships**
- `topic` — parent Topic (`back_populates="questions"`).
- `sub_questions` — one-to-many to `SubQuestion`.
- `images` — one-to-many to `QuestionImage`.

### How a Question ties back to the hierarchy
- A Question links **only** to a `Topic` (via `topic_id`). Theme and Subject are
  reached transitively: `Question → Topic → Theme → Subject`, with
  `Topic.subject_id` also giving a direct Subject hop.
- `Question.to_json()` (`app/test/models.py:24`) injects `"level": self.topic.level`
  — i.e. difficulty is pulled live from the parent Topic.
- `school_id` makes questions either **global** (null) or **school-specific**,
  independent of the content tree.

---

## SubQuestion

Table: `sub_question` — `app/test/models.py:55`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | Integer | PK | |
| `parent_question_id` | Integer | FK → `question.id`, NOT NULL | |
| `text` | Text | NOT NULL | |
| `correct_answer` | Text | NOT NULL | |
| `possible_answers` | Text | NOT NULL | stringified list |
| `points` | Integer | NOT NULL | |
| `is_flagged` | Boolean | default `False` | |
| `flag_reason` | Text | nullable | |
| `year` | Integer | nullable | |

**Relationships**
- `parent_question` — parent Question (`backref` from `Question.sub_questions`).

Subquestions inherit their topic/subject context from the parent Question —
they have **no `topic_id`** of their own (the input schema accepts `topic_id`
but the model does not persist it) and **no images** relationship.

---

## QuestionImage

Table: `question_image` — `app/test/models.py:87` (migration `24bf26e7a271`)

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | Integer | PK | |
| `question_id` | Integer | FK → `question.id`, NOT NULL | attaches to parent Question only |
| `image_url` | String | NOT NULL | a URL — the API stores no binaries |
| `label` | String | nullable | e.g. `"main"`, `"the various options"` |
| `is_for_answer` | Boolean | default `False` | question image vs. answer image |

Images attach to the parent Question only (not to SubQuestions). On read,
`Question.to_json()` splits them into `question_images` / `answer_images` dicts
keyed by `label`.

---

## End-to-end relationship map

```
staff_subjects (assoc) ── Staff
        │
     Subject ─────────────┐ (subject_id, denormalized)
        │                 │
      Theme               │
        │                 │
      Topic ◄─────────────┘
        │  (topic_id)        level surfaced onto question JSON
     Question ── school_id ──► School (nullable: global vs school-owned)
       ├── SubQuestion (parent_question_id)
       └── QuestionImage (question_id; question vs answer images)

     Test ── subject_id ──► Subject     (a test is for one subject)
```

## Practical notes / gotchas
- **Difficulty lives on the Topic** (`level`), not the Question; it is copied into
  each question's serialized JSON at read time.
- **`possible_answers` is a stringified list** on both Question and SubQuestion,
  parsed via `ast.literal_eval` on every serialization — fragile and worth
  migrating to a JSON column.
- **`Topic.subject_id` is denormalized** alongside `theme_id`; keep them
  consistent (a Topic's `subject_id` should match its Theme's `subject_id`).
- **Question scope is orthogonal to the content tree**: a question is global when
  `school_id` is null, school-owned otherwise.
