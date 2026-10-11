# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr helps someone shop secondhand clothes by describing what they want in plain language, like "vintage graphic tee under $30, size M". It searches a set of listings from depop, poshmark and thredUp for the best match within their size and price, then asks a model for one or two outfits that pair the find with pieces already in their wardrobe. They get back the item (title, price and platform), the outfit suggestions, and a short social-media caption, the "fit card", about the find. If nothing matches, they get no outfit or caption, just a message that says what to change: the size, the max price, or the keywords.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Finds the listings that match a keyword description, keeping only those that fit the size and price limits, best match first.
  - **Scoring:** A listing's score is the number of description keywords (lowercased, stopwords removed) that appear in its `title`, `description`, `category`, `style_tags`, `colors` or `brand`. Listings that score 0 are dropped, and the rest are sorted highest score first.
  - **Size:** Sizes match by whole token: the listing's size is split on `/` and anything in parentheses is dropped, so `M` matches `S/M` but `S` doesn't match `US 9`. Any `One Size` listing matches every size, and a size of `None` skips the size filter.
  - **Price:** `max_price` is inclusive (`price <= max_price`), and `None` skips the price filter.
- **Inputs:** `description` (str), `size` (str or None), `max_price` (float or None)
- **Returns:** A list of up to 10 listing dicts, best match first. Each has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None) and `platform`.
- **When it has nothing:** An empty list, `[]`.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the new item, using pieces from the user's wardrobe.
- **Inputs:** `new_item` (dict, a listing dict), `wardrobe` (dict with an `items` list)
- **Returns:** A non-empty string of outfit suggestions that name specific wardrobe pieces by their `name`.
- **When it has nothing:** If the wardrobe is empty, it returns a non-empty string of general styling advice for the item. It never returns `""`: if the model's response is empty, it returns a fixed sentence of general styling advice instead.

### `create_fit_card`

- **What it does:** Asks the model for a 2–4 sentence social-media caption about the find and its outfit, written like a real post, not a product listing.
- **Inputs:** `outfit` (str), `new_item` (dict, a listing dict)
- **Returns:** A caption string that mentions the item's `title`, `price` and `platform` once each.
- **When it has nothing:** If `outfit` is empty or only whitespace, it returns the error string `"Can't write a fit card without an outfit suggestion."` and does not call the model.
- **Unit 4 stretch:** now served over MCP from `mcp_server.py`. The inputs, return value and empty case are the same.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that tells the user what to change (drop or change the size, raise the max price, or use broader keywords), and return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise, put the first result in `session["selected_item"]` and go to `suggest_outfit`.

> **Unit 4 stretch:** an empty search that named a size now gets one retry
> over MCP with `size=None` before the run stops. See Stretch Features.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** With regex, in `agent.py::parse_query`, with no model call. It pulls out three things and removes each one from the query once it's found:
- **Price:** a number after `under`, `below`, `less than`, `max`, `up to` or `at most`, or a `$` amount such as `$40 or less`, becomes `max_price` (float).
- **Size:** the word `size` followed by a letter size (`XXS` to `XXL`), `US 9`, `W30` / `W30 L30` or `one size` becomes `size`, uppercased. A size without the word `size` in front, like "in a medium", isn't picked up.
- **Description:** whatever is left, with filler such as "looking for", "I want" and "a" taken out, becomes `description`.

A part the query doesn't mention comes back as `None`. For example, `"vintage graphic tee under $30, size M"` gives `{"description": "vintage graphic tee", "size": "M", "max_price": 30.0}`.

**What moves through the session:** Each tool's result goes into the session, and the next tool reads its inputs back out of the session, never from a local variable.
1. `query`, and `wardrobe` from the caller, are set by `new_session()`.
2. `parsed` holds `parse_query(query)`.
3. `search_results` holds `search_listings(parsed["description"], parsed["size"], parsed["max_price"])`.
4. If `search_results` is empty, `error` is set and the run stops, leaving `selected_item`, `outfit_suggestion` and `fit_card` as `None`. Otherwise `selected_item` is set to `search_results[0]`. (Unit 4 stretch: if the empty search had a size, it first retries once without it. `dropped_size` records the size it dropped, and `notice` tells the user.)
5. `outfit_suggestion` holds `suggest_outfit(selected_item, wardrobe)`.
6. `fit_card` holds `create_fit_card(outfit_suggestion, selected_item)`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Here are two ways to style the Y2K Baby Tee — Butterfly Print using only the items already in your wardrobe:

* **Streetwear Contrast:** Pair the baby tee with your **Baggy straight-leg jeans, dark wash** to balance out the fitted crop of the shirt. Add the **Chunky white sneakers** for footwear, layer the **Vintage black denim jacket** over top, and finish the look with the **Black crossbody bag**.
* **Casual Edgy:** Tuck the baby tee into your **Wide-leg khaki trousers**, and thread the **Brown leather belt** through the waistbands to add definition. Ground the outfit with your **Black combat boots** and layer the **Black cropped zip hoodie** over your shoulders or wear it zipped up for a textured contrast.

  Fit card: Found this adorable Y2K Baby Tee — Butterfly Print on depop for just $18.00 and I am so obsessed. I threw it on with baggy dark wash jeans and chunky sneakers for that classic early 2000s streetwear contrast, but it looks just as good dressed down with wide-leg trousers and combat boots.

0 model calls this session, 2 served from cache
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print([(l['title'], l['size'], l['price']) for l in search_listings('graphic tee', size='L', max_price=30)])"
[('Graphic Tee — 2003 Tour Bootleg Style', 'L', 24.0), ('Vintage Band Tee — Faded Grey', 'L', 19.0), ('Vintage Graphic Hoodie — Faded Black', 'L', 26.0)]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Here are two ways to style these vintage Levi's 501s using only the items currently in your wardrobe:

* **Casual Streetwear:** Pair the **Vintage Levi's 501 Jeans — Medium Wash** with the **White ribbed tank top** tucked in to define your waist. Layer the **Oversized grey crewneck sweatshirt** over top for an effortless, cozy contrast, and finish with the **Chunky white sneakers** and the **Black crossbody bag**.
* **Edgy Vintage Layering:** Wear the **Vintage Levi's 501 Jeans — Medium Wash** with the **Brown leather belt** threaded through the loops. Add the **Black cropped zip hoodie**, layer the **Vintage black denim jacket** right over it for a cool double-jacket effect, and ground the look with the **Black combat boots** and the **Black crossbody bag**.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Finally found a pair of Vintage Levi's 501 Jeans — Medium Wash that actually fit right. Grabbed these on depop for $38.00 and I'm obsessed with the knee fading. Just threw them on with crisp white sneakers for that effortlessly chill streetwear look.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I gave Claude my branch rule and asked it to fill in `run_agent()` in `agent.py`, parsing the query with regex.
- *What came back:* A loop that worked on both paths, but `parse_query("looking for a vintage graphic tee under $30")` returned the description `"a vintage graphic tee"`, with a stray "a".
- *What I changed:* I added `a`, `an` and `the` to the filler words the parser removes, so the description is now `"vintage graphic tee"`.

**Moment 2**

- *What I asked for:* I asked Claude to put every tool result in the session and have each next call read its inputs from the session, not from a value passed straight across.
- *What came back:* The search step copied `session["parsed"]` into a local `parsed` variable and passed that to `search_listings`, so the call line didn't show that its inputs came from the session.
- *What I changed:* I removed the local copy, so the call reads `session["parsed"]["description"]`, `["size"]` and `["max_price"]` directly. A run with `suggest_outfit` wrapped to record its input then confirmed it received the same object as `session["selected_item"]` (`lst_002`, Y2K Baby Tee — Butterfly Print).

**Moment 3 (unit 4)**

- *What I asked for:* I asked Claude to turn my five criteria into eval scenarios in `scenarios.py`.
- *What came back:* While writing criterion 4's scenario, it pointed out that the check asked for `$24`, but the query's first result, the one the loop picks, costs $18. So the check could never pass.
- *What I changed:* I didn't edit the original line. I added a revision under it in `criteria.md` that ties the price to `session["selected_item"]`, and I still scored the before run as MISSED (0/5) against the line as written.

**Moment 4 (unit 4)**

- *What I asked for:* After a before run where the agent itself missed nothing, I asked Claude what single improvement the diagnosis pointed to.
- *What came back:* Criterion 3's trace passed `session["selected_item"]` as the `in:` line, so it compared the selection against itself and couldn't fail. The proposed change was to have each tool record the item it received (`tools.py::last_received`) and trace that.
- *What I changed:* Before the real after run, I planted a bug with the model stubbed out, handing `create_fit_card` the second search result. Step 4's `in:` line then showed the wrong item. That confirmed the criterion can fail now. I didn't commit the planted bug. When I wrote up the MCP move, I also had Claude point the client at a missing server. That's how I found that `MCPError` escapes `run_agent`, which is now listed under What's Still Broken rather than claimed as handled.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected item reaches both model calls | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card stays within spec | ≥ 4 of 5 | FAIL* | FAIL* | FAIL* | FAIL* | FAIL* | MISSED (0/5)* |
| 5. empty wardrobe gets real advice | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

\* Criterion 4 as first written requires `$24`, the price of the second
search result. The loop takes the first (Y2K Baby Tee, $18, depop), so all
five tries fail that check: 0/5. Under the unit 4 revision in `criteria.md`
(the card must contain the selected item's price), all five pass: each card
has `$18.00`, says depop, has 2–3 sentences, and opens with a sentence no
earlier try used. Tries 1 and 2 share their opening words ("Found this
adorable Y2K Baby Tee — Butterfly Print for just $18.00…") and differ only
after that.

Full log, all five tries of every scenario: `results/run_2026-10-08_0842_before.md`.

**Real output from one try**, pasted as text, naming the file and function
that produced it:

All of it is from Try 1 of `python run_eval.py --label before` (caching off,
temperature 0.9). `run_eval.py::run_once` calls `agent.py::run_agent` and
records the session it returns and the trace. The trace text is printed by
`trace.py::get_trace` from the `trace.step()` calls in `agent.py::run_agent`.

#### Criterion 1 — matching query completes

Query `vintage graphic tee under $30`, example wardrobe. Trace from
`trace.py::get_trace`. All four steps ran:

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: found, taking the first result
[3] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Here are two ways to style the Y2K Baby Tee — Butterfly Print using only items from your wardrobe:  *   **Y2K …
[4] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Found the cutest little butterfly tee on Depop for just $18.00 and I’m obsessed with the early 2000s pink and …
```

Fit card returned, from `tools.py::create_fit_card`:

```
Found the cutest little butterfly tee on Depop for just $18.00 and I’m obsessed with the early 2000s pink and purple print. I’ve been wearing it non-stop, either leaning into a total Y2K streetwear vibe with baggy denim and chunky sneakers, or toughening it up with combat boots and a black jacket for that sweet-meets-grunge look.
```

#### Criterion 2 — impossible query stops early

Query `designer ballgown size XXS under $5`, example wardrobe. Trace from
`trace.py::get_trace`. It stops after step 2, and `suggest_outfit` never runs:

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping
```

`session["error"]`, written by `agent.py::_no_results_message`:

```
No listings matched 'designer ballgown' in size XXS and under $5. To find something, drop the size or try a neighbouring one; raise the max price; or use broader keywords (e.g. 'jacket' instead of 'designer bomber jacket').
```

#### Criterion 3 — selected item reaches both model calls

Query `levi's 501 jeans under $40`, example wardrobe. `session["selected_item"]`
was `Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)`. Trace from
`trace.py::get_trace`. The `in:` lines of steps 3 and 4 show the same item:

```
[1] parse_query
      in:  levi's 501 jeans under $40
      out: {'description': "levi's 501 jeans", 'size': None, 'max_price': 40.0}
[2] search_listings (via MCP)
      in:  {'description': "levi's 501 jeans", 'size': None, 'max_price': 40.0}
      out: 4 items: Vintage Levi's 501 Jeans — Medium Wash, Straight Leg Black Jeans — Faded, High-Waisted Denim Shorts — Cutoff … +1 more
      →    branch: found, taking the first result
[3] suggest_outfit
      in:  Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)
      out: These vintage Levi's 501s give you a classic, straight-leg silhouette that bridges the gap between your existi…
[4] create_fit_card
      in:  Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)
      out: Finally scored these Vintage Levi's 501 Jeans and I'm obsessed with the knee fading. Got them listed on depop …
```

#### Criterion 4 — fit card stays within spec

Query `vintage graphic tee under $30`, example wardrobe. Selected item: Y2K Baby
Tee — Butterfly Print ($18.0, depop). Fit card from `tools.py::create_fit_card`.
It has 3 sentences and contains `$18.00` and `depop`:

```
Found this adorable Y2K Baby Tee — Butterfly Print for just $18.00 on depop and I'm obsessed. I styled it with baggy dark wash jeans and chunky white sneakers for that ultimate early 2000s streetwear look. Such a steal!
```

#### Criterion 5 — empty wardrobe gets real advice

Query `denim jacket under $50`, wardrobe from `get_empty_wardrobe()`. Selected
item: Denim Jacket — Light Wash, Cropped ($42.0, poshmark). `session["error"]` is
None. The `outfit_suggestion` from `tools.py::suggest_outfit` is written by the
model, not the fixed "simple basics… focal point" fallback:

```
Here are two easy, practical ways to style this vintage Wrangler jacket using common wardrobe staples:

* **The Casual Contrast:** Layer the cropped jacket over a basic black or white ribbed tank top, paired with high-waisted wide-leg black trousers to balance the light wash. Finish the look with classic white leather low-top sneakers and a simple leather belt.
* **Double Denim (Different Tones):** Wear the jacket over a fitted gray crewneck t-shirt and dark wash straight-leg jeans—mixing light and dark denim keeps the outfit grounded. Add black canvas slip-on sneakers or ankle boots to complete the look.
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | ≥ 4 of 5 | **MET** (5/5) | All five tries show `stopped early: no`, four trace steps, and a fit card. 5 passes against a floor of 4 holds. |
| 2 | Impossible query stops before the second tool | 5 of 5 | **MET** (5/5) | All five traces end at step 2 with `branch: empty, stopping`, no `suggest_outfit` step, and the same message naming the size, price and keywords to change. The target asks for every try, and every try passed. |
| 3 | Selected item reaches both model calls | 5 of 5 | **MET** (5/5) | In all five tries the `in:` lines of steps 3 and 4 both read `Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)`, the same as `selected_item`. The target asks for every try, and every try passed. |
| 4 | Fit card stays within spec | ≥ 4 of 5 | **MISSED** (0/5) | Scored against the check as written in unit 3. No card contains `$24`. All five say `$18.00` because the selected item costs $18. 0 passes against a floor of 4 is a miss. Under the unit 4 revision (price of `selected_item`), all five pass: 2–3 sentences, `$18.00`, depop, five different first sentences. That's 5/5, but it doesn't change this verdict. |
| 5 | Empty wardrobe still gets real advice | ≥ 4 of 5 | **MET** (5/5) | All five tries finished with no error (`stopped early: no`). All five `outfit_suggestion`s are model-written two-outfit advice, and the fallback sentence ("simple basics… focal point") appears 0 times in the log. 5 passes against a floor of 4 holds. |

**Diagnoses**

**Criterion 4: missed on 5 of 5. The fault is in the criterion, not the agent.**
Step: 4, `create_fit_card`, scored by the price check. Mechanism: the check
names a fixed price from the wrong search result. The price check names `$24`, which is the price of the *second* search
result (Graphic Tee — 2003 Tour Bootleg Style). The loop's branch in
`agent.py::run_agent` always takes `results[0]`, the Y2K Baby Tee at $18.
The session passes that item intact to `create_fit_card`: the step 4 `in:`
line reads `Y2K Baby Tee — Butterfly Print ($18.0, depop)` in every try. The
model then wrote the correct price, `$18.00`, every time. The tool, the
branch, the session and the model's output all did what they should, so none
of the four places is at fault. I wrote the check against the wrong row of
the search results, so it could never pass. That makes it one cause, not
five separate failures: every try fails for the same reason. The fix is to
the measurement, recorded under criterion 4 in `criteria.md` as a revision
with the original left in place. The target stays at 4 of 5.

**The agent itself missed nothing.** Criteria 1, 2, 3 and 5 hit 5/5, and the
only miss was a broken check. So the honest question is whether my targets
were too low. Some were:

- **Criterion 3 is the one I'd tighten first. Its 5 of 5 cost nothing.** In
  `agent.py::run_agent`, the trace's `inputs=` is `session["selected_item"]`
  (lines 158 and 173), the same expression passed to `suggest_outfit` and
  `create_fit_card` (lines 151 and 166). So the `in:` line compares
  `selected_item` against itself. Suppose the tool were called with a stale or
  different item. The trace would still print `selected_item` and the try
  would pass. What actually verified the state was reading the code once; the
  five runs added nothing. A tighter version would record the item each tool
  actually received, inside `tools.py`, and compare that to `selected_item`.
- **Criterion 4's first-sentence check is too loose.** Tries 1 and 2 open
  with the same eleven words ("Found this adorable Y2K Baby Tee — Butterfly
  Print for just $18.00…"), and four of the five cards start with "Found".
  Exact-text comparison counts them as different anyway. Requiring the first
  five words to differ would have failed try 2. That's still 4/5, so the
  verdict under the revision wouldn't change, but the check would measure the
  variation it claims to.
- **Criteria 1 and 5 (≥ 4 of 5) leave room for a model call to fail, which
  never happened.** Five clean tries don't prove the failure rate is zero, so
  I'd keep these as they are rather than raise them on one run.

**Arguing the other side on criterion 4.** The case for MET: the agent did
exactly what the spec wanted, a card with the right price. A check that no
output could ever pass measures nothing, so 0/5 tells us nothing about the
agent. I still mark it MISSED. The verdict scores the criterion as it was
written before the results existed, and the guidelines allow fixing a broken
criterion only by revising it, not by rescoring it. The revision is in
`criteria.md`, and the after run gets scored against it.



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: found, taking the first result
[3] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Here are two ways to style the Y2K Baby Tee — Butterfly Print using only the items already in your wardrobe:  …
[4] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Found this adorable Y2K Baby Tee — Butterfly Print on depop for just $18.00 and I am so obsessed. I threw it o…
```

**Empty search**

```
$ python app.py ask 'ball gown size xxs under $5' --trace
[1] parse_query
      in:  ball gown size xxs under $5
      out: {'description': 'ball gown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'ball gown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping

  No listings matched 'ball gown' in size XXS and under $5. To find something, drop the size or try a neighbouring one; raise the max price; or use broader keywords (e.g. 'jacket' instead of 'designer bomber jacket').

0 model calls this session
```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->
`run_agent` no longer imports `search_listings` from `tools.py`. It calls
`mcp_client.call_tool("search_listings", {...})`, which starts
`mcp_server.py`, where the tool is registered with a description of its
inputs and its empty-list case. The results didn't change: on four queries
(graphic tee, ballgown, Levi's, denim jacket) the MCP call returned the same
list as the direct call (10, 0, 4 and 7 items, with `price` still a float).
Two things did change. Each search now takes about 0.3–0.65 s instead of
under 1 ms, because every call starts and stops the server. And there's a new
way for a run to fail: if the server can't start, `call_tool` raises
`MCPError` and `run_agent` doesn't catch it (see What's Still Broken).


---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** `suggest_outfit` and `create_fit_card` now record a copy of
the item they were handed, as the first line of each function
(`tools.py:237` and `tools.py:338`), and `tools.py::last_received` returns it.
`agent.py::run_agent` passes `last_received("suggest_outfit")` and
`last_received("create_fit_card")` to `trace.step(inputs=...)` (lines 158 and
173) where it used to pass `session["selected_item"]`. So the `in:` line of
steps 3 and 4 is now the item the tool received, and `selected_item` in the
run log is now the thing it gets compared against. One file per side, nothing
else touched: no prompt, no branch, no return shape.

**Which failure it was meant to fix:** Not a miss. The only miss in the before
run, criterion 4, was a broken check, and its fix is the measurement revision
already in `criteria.md`. No agent change could have made a card say `$24`
for an $18 item. What the diagnosis named as the thing to tighten first was
criterion 3. Its `in:` lines printed `selected_item` back to itself, so a
loop that handed a model call a stale or different item would still have
passed 5/5. The failure being fixed is that criterion 3 couldn't fail.

**Checking that it can fail now.** Before the real run I planted the bug the
criterion is about. With the model stubbed out (no API calls), I patched the
loop so `create_fit_card` received the second search result instead of
`selected_item`:

```
selected_item: Vintage Levi's 501 Jeans — Medium Wash
[3] suggest_outfit
      in:  Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)
      out: stub text
[4] create_fit_card
      in:  Straight Leg Black Jeans — Faded ($30.0, thredUp)
      out: stub text
```

Step 4's `in:` line no longer matches `selected_item`, so that try fails
criterion 3. With the old trace code, step 4 would have printed
`session["selected_item"]` (the Levi's) and passed, even though the tool
wrote a caption about the black jeans. That patch was a one-off check and
was never committed.

### Run Log — Before

`results/run_2026-10-08_0842_before.md`

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected item reaches both model calls | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card stays within spec | ≥ 4 of 5 | FAIL* | FAIL* | FAIL* | FAIL* | FAIL* | MISSED (0/5)* |
| 5. empty wardrobe gets real advice | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

### Run Log — After

`python run_eval.py --label after` → `results/run_2026-10-11_1442_after.md`.
Same five scenarios, five tries each, caching off, temperature 0.9.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected item reaches both model calls | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card stays within spec | ≥ 4 of 5 | PASS* | PASS* | PASS* | PASS* | PASS* | MET (5/5)* |
| 5. empty wardrobe gets real advice | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

\* Scored against the unit 4 revision (the card must contain the selected
item's price, $18), as the before diagnosis said the after run would be. All
five cards have `$18.00`, say depop, have 2–3 sentences, and open with a
sentence no earlier try used. Against the original `$24` line it's still 0/5,
for the same reason as before: the selected item costs $18.

How each row was scored:

1. All five: `stopped early: no`, four trace steps, a fit card.
2. All five: `branch: empty, stopping` at step 2, no `suggest_outfit` step,
   and the message naming size, price and keywords.
3. All five: steps 3 and 4 both read `Vintage Levi's 501 Jeans — Medium Wash
   ($38.0, depop)`, matching `selected_item`. These lines now come from
   `tools.py::last_received`, not from the session.
4. See the note above.
5. All five finish without an error. "simple basics" (the fallback) appears 0
   times in the log.

**Did it help, and how do I know:** The pass counts didn't move. Before and
after are both 5/5 on criteria 1, 2, 3 and 5, and 5/5 on criterion 4 as
revised. So the change didn't make the agent pass anything it was failing,
and it wasn't meant to. What changed is what criterion 3's 5/5 is worth.
Before, it was guaranteed by how the trace was written, and the five runs
added nothing past reading the code once. After, the `in:` line comes from
the tool, and the planted-bug check above shows a wrong item now produces a
failing try. Criterion 3's after-run 5/5 is evidence the loop passes the
right item. The before-run 5/5 wasn't.

The limits. `last_received` stores the item when the function is entered, so
it shows what the tool was *given*, not what went into the prompt. A bug
inside `_describe_item` would still slip through. It also holds only the
latest call, so if two runs overlapped in one process, one could overwrite
the other's record. The loop is sequential, so that can't happen today.

Unchanged, for comparison with the before diagnosis: 2 of the 5 cards open
with "Found" (4 of 5 before), and 2 with "Obsessed". This change doesn't
touch the caption prompt, so I read that as run-to-run variation, not an
effect.

---

## Stretch Features

Declared here, and committed, before either one was built.

**1. Retry with looser constraints (+1).** If `search_listings` returns `[]`
and the query named a size, `agent.py::run_agent` searches once more over
MCP with the same description and max price but `size=None`. The trace shows
this as its own step that names the size it dropped. If the retry finds
something, the loop takes the first result as usual and tells the user the
size was dropped. If the retry is also empty, the run stops with the same
kind of message as before, before `suggest_outfit`. A query with no size gets
no retry. There's only one retry, and price is never loosened.

**2. A second tool moved onto MCP (+1): `create_fit_card`.** It gets
registered in `mcp_server.py` next to `search_listings`, with a description
of its inputs and its empty-outfit case, and `run_agent` calls it through
`mcp_client.call_tool` instead of importing it. The trace step will read
`create_fit_card (via MCP)`.

How I'll check both: a third eval run (`python run_eval.py --label stretch`),
plus pasted traces for a retry that finds something and one that doesn't.


### What was built

**Retry.** In `agent.py::run_agent`, an empty first search with a size goes
to a new `retry_without_size` step. That step calls `search_listings` over MCP
again with the same description and max price and `size=None`, and records
the dropped size in `session["dropped_size"]`. If the retry finds something,
the first result is selected and `session["notice"]` tells the user the size
was dropped (`app.py` prints it as `Note:`). If the retry is also empty, the
run stops before `suggest_outfit`. The message no longer suggests dropping
the size, because that's already been tried. A query with no size skips the
retry.

A retry that finds something:

```
$ python app.py ask "levi's 501 jeans size XXS under $40" --trace
[1] parse_query
      in:  levi's 501 jeans size XXS under $40
      out: {'description': "levi's 501 jeans", 'size': 'XXS', 'max_price': 40.0}
[2] search_listings (via MCP)
      in:  {'description': "levi's 501 jeans", 'size': 'XXS', 'max_price': 40.0}
      out: [] (empty)
      →    branch: empty, retrying once without the size
[3] search_listings (via MCP, retry: dropped size XXS)
      in:  {'description': "levi's 501 jeans", 'size': None, 'max_price': 40.0}
      out: 4 items: Vintage Levi's 501 Jeans — Medium Wash, Straight Leg Black Jeans — Faded, High-Waisted Denim Shorts — Cutoff … +1 more
      →    branch: found without the size, taking the first result
[4] suggest_outfit
      in:  Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)
      out: Here are two ways to style these vintage Levi's 501s using only the items currently in your wardrobe:  * **Cas…
[5] create_fit_card (via MCP)
      in:  Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)
      out: Found the holy grail of denim with these Vintage Levi's 501 Jeans — Medium Wash for just $38.00 on depop. I've…

  Found:    Vintage Levi's 501 Jeans — Medium Wash — $38.0 on depop
  Note:     Nothing matched in size XXS, so FitFindr searched again without the size. Check the listing's size before you buy.
```

A retry that's also empty (criterion 2's query, the same in all five tries of
the run log below):

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, retrying once without the size
[3] search_listings (via MCP, retry: dropped size XXS)
      in:  {'description': 'designer ballgown', 'size': None, 'max_price': 5.0}
      out: [] (empty)
      →    branch: still empty, stopping

  No listings matched 'designer ballgown' in size XXS and under $5, or in any size under $5. To find something, raise the max price; or use broader keywords (e.g. 'jacket' instead of 'designer bomber jacket').
```

**`create_fit_card` on MCP.** It's registered in `mcp_server.py` as a second
`@mcp.tool()`, and `run_agent` calls `call_tool("create_fit_card", {"outfit":
..., "new_item": ...})`. The happy-path trace above shows step 5 as
`create_fit_card (via MCP)`. Moving it took three fixes outside the loop:

- **`mcp_client.py`:** the server was started with only a few environment
  variables, so `AI201_CACHE=0` never reached it. It now gets this process's
  environment.
- **`run_eval.py`:** it turned caching off with `config.CACHE_ENABLED = False`,
  which only affects its own process. It now also sets `AI201_CACHE=0`, so the
  server's fit cards aren't served from the cache. Without this, criterion 4's
  first-sentence check would have failed.
- **`mcp_client.py`:** a tool error, like a bad API key inside
  `create_fit_card`, came back wrapped in nested `ExceptionGroup`s. The real
  reason was lost and the error read "unhandled errors in a TaskGroup". The
  client now unwraps it. With `GEMINI_API_KEY=bad` the run stops at the fit
  card with `session["error"]` starting "Couldn't write the fit card… The
  model rejected your API key." It doesn't crash.

### Run Log — Stretch

`python run_eval.py --label stretch` → `results/run_2026-10-11_1457_stretch.md`.
Same five scenarios, five tries each, caching off, temperature 0.9.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected item reaches both model calls | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card stays within spec | ≥ 4 of 5 | PASS* | PASS* | PASS* | PASS* | PASS* | MET (5/5)* |
| 5. empty wardrobe gets real advice | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

\* Scored against the unit 4 revision (the selected item's price, $18).

How each row was scored:

1. All five: `stopped early: no` and a fit card.
2. All five: step 2 is empty, step 3 is the retry with `dropped size XXS`,
   then `branch: still empty, stopping`. There's no `suggest_outfit` step,
   and the message names the price and keywords to change. The run now stops
   at step 3 instead of step 2, but the criterion asks for a stop before
   `suggest_outfit`, and that still holds.
3. All five: steps 3 and 4 read `Vintage Levi's 501 Jeans — Medium Wash
   ($38.0, depop)`, matching `selected_item`.
4. All five cards have 2–3 sentences, `$18.00` and depop, and five different
   first sentences. Two open with "Scored" and two with "Obsessed".
5. All five finish without an error, and "simple basics" appears 0 times.

**What changed, and what it cost.**
- **Pass counts:** unchanged, 5/5 on every criterion.
- **Model calls:** the run printed "21 model calls this session". That count
  misses the 20 fit-card calls, which now happen in the server's process. The
  trace footer in `app.py` undercounts the same way.
- **Criterion 3:** it's weaker for step 4 than after the improvement. The
  server's `last_received` lives in another process, so step 4's `in:` line
  is the `new_item` the agent put into the MCP request, not what the tool
  received on the other side. A wrong item sent by the loop still shows up,
  which was the planted-bug case. A change to the item during the JSON
  round trip wouldn't.
- **Rate limiter:** it runs per process, so the server's calls don't count
  toward the 15-per-minute limit. In this run the service pushed back
  once, on a `suggest_outfit` call in criterion 3's scenario. The retry
  waited 45 s and the try passed. That's likely the server's calls
  pushing the real rate over the limit.

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

**Criterion 4, as first written, is still missed: 0/5 before and after.** It
requires `$24`, the price of the second search result, and the loop takes
the first one ($18). *What I'd do:* nothing more to the agent. Making it pick
the $24 tee would break the branch rule just to pass the check. The fix is
the revision in `criteria.md`, and the agent passes that 5/5. *Why I stopped
there:* the original line stays in place and stays scored as missed, because
that's the only honest way to fix a criterion that was wrong.

Every other criterion is met, so the rest of this list is things I know are
weak that no criterion catches yet.

- **An MCP server failure crashes the run.** I pointed `mcp_client.SERVER`
  at a file that doesn't exist and ran the graphic tee query. `run_agent`
  raised `MCPError: Couldn't call 'search_listings' over MCP: unhandled
  errors in a TaskGroup` after step 1. It didn't return a session with
  `error` set. Model failures are handled (`_stop_on_model_error`). Since
  the stretch work, an MCP failure on the fit card step is handled too.
  The two search calls (the first search and the retry) still aren't.
  *What I'd do:* catch `MCPError` around both search calls in
  `agent.py::run_agent`, put a message in `session["error"]` that says the
  search service couldn't be reached, and add a sixth criterion: with the
  server unreachable, the run returns a session with `error` set in 5 of 5
  tries. *Why I stopped:* the unit allowed one improvement, and I spent it on
  criterion 3. I only found this gap while writing up the MCP move above.
- **A size without the word "size" is silently ignored.** `parse_query('vintage
  graphic tee in a medium under $30')` gives `size: None` and the description
  `'vintage graphic tee medium'`. So the search doesn't filter by size, and
  2 of its top 3 results are size L. The user gets an item that won't fit and
  no warning. *What I'd do:* map `small`/`medium`/`large` (and `in a M`) to
  sizes in `_SIZE_RE`, and add a criterion that checks the size of
  `selected_item` against the size asked for. *Why I stopped:* I documented
  this limit in the Planning Loop section back in unit 3. None of my five
  criteria tests size, so the eval never surfaced it.
- **Criterion 4's first-sentence check is still too loose.** It compares
  whole sentences, so two cards that share their first eleven words still
  count as different. *What I'd do:* require the first five words to differ.
  *Why I stopped:* it wouldn't change either verdict (before would still be
  4/5 as revised), and revising the same criterion a second time after
  seeing results would look like tuning the check to the output.
- **Criterion 3 checks what each tool was given, not what it sent to the
  model.** `last_received` records the item when the function starts, so a
  bug in `_describe_item` that put the wrong title in the prompt would still
  pass. *What I'd do:* record the prompt text too and check that the
  item's title appears in it. *Why I stopped:* the planted-bug check showed
  that the change catches the failure the criterion names (a wrong item
  passed between steps), and that was the scope of the improvement.
- **The model-failure allowance in criteria 1 and 5 has never been used.**
  Across the 20 tries of those two criteria (before and after), no model
  call failed or came back empty. That doesn't show the failure rate is low,
  only that I haven't seen a failure yet.
  *What I'd do:* run more tries before raising either target to 5 of 5.
  *Why I stopped:* a full eval run makes about 40 model calls (four
  scenarios, five tries, two calls each), and two runs with zero failures
  isn't enough evidence to change a target.



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
