# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->
`search_listings` and the query parsing never call the model, so the same query finds the same listing every time. What can vary are the two model calls after it: `suggest_outfit` and `create_fit_card`. Either can come back empty or fail on a slow or rate-limited request. I allow one try in five for that, but not more, because a loop that drops a run every other time isn't working.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->
This path never reaches the model. Parsing, `search_listings` and the empty-list check are all plain Python with no randomness, so the same impossible query gives `[]` and takes the same branch every time. A miss here can't be bad luck; it's a bug in the branch, so anything below 5 of 5 counts as a fail.

---

## 3. Something about state

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

Given a matching query, run 5 times with the trace on. A try passes if the `in:` line of the `suggest_outfit` step and the `in:` line of the `create_fit_card` step each show the same text as the selected item, `title ($price, platform)`, e.g. `Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)`. Target: 5 of 5.

For that line to exist, `agent.py::run_agent` must call `trace.step()` for each tool with `inputs=` set to the item dict passed to that tool. I check this once by reading the code before the runs.

**Why this target:**
Passing the item from search to `suggest_outfit` to `create_fit_card` is plain Python with no model involved, so nothing about it is random and any mismatch is a bug. That's why it's 5 of 5. I compare the trace text and not the fit card's wording, so a caption that leaves out the price can't make this criterion fail. The trace shows each listing as title, price and platform, and that text is different for all 40 listings, so a match means the same item. A state bug, such as passing a stale or different item to the second model call, would otherwise look like a bad caption.

---

## 4. Something about the fit card

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

Run the same matching query 5 times with caching off. A try passes if its fit card:
- has 2–4 sentences, counted by `.`, `!` and `?`;
- contains the item's price as `$24` or `$24.00`;
- contains the item's platform name;
- has a first sentence different from every earlier try's first sentence.

Target: at least 4 of 5 tries pass.

**Why this target:**
The words are allowed to change; what can't change is what my spec for `create_fit_card` promises: 2–4 sentences that mention the price and platform. At `TEMPERATURE` 0.9 the model sometimes writes "24 bucks", drops the platform, or runs long, so I allow one miss in five, the same allowance as criterion 1 for one model call. The first-sentence check makes sure the variation is real: if tries keep opening the same way, the cache is on or the prompt is too rigid, and those tries fail.

---

## 5. Your choice

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

**An empty wardrobe still gets real advice.** Given a matching query and `get_empty_wardrobe()`, the run finishes with `session["error"]` as None, and `outfit_suggestion` is model-written styling advice, not the fixed fallback sentence, in at least 4 of 5 tries.

**Why this target:**
An empty wardrobe is the input most likely to break `suggest_outfit`, for example by building the prompt from an empty list. My spec adds a fixed fallback sentence so this case never returns `""`, but that fallback would also hide a broken empty-wardrobe prompt, so a try that falls back counts as a fail. The target is 4 of 5, not 5 of 5, because like criterion 1 it depends on a model call that can occasionally come back empty.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
