"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re
from mcp_client import call_tool
import config
import trace
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable

# ── session state ─────────────────────────────────────────────────────────────


def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,  # what the user typed
        "parsed": {},  # description / size / max_price you pulled out of it
        "search_results": [],  # everything search_listings returned
        "selected_item": None,  # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,  # the user's wardrobe
        "outfit_suggestion": None,  # what suggest_outfit returned
        "fit_card": None,  # what create_fit_card returned
        "error": None,  # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    trace.start_trace()
    session["parsed"] = parse_query(query)
    trace.step("parse_query", inputs=query, returned=str(session["parsed"]))

    # Each pass runs one step and names the next one from what it got back.
    next_step = "search_listings"
    count = 0
    while next_step != "done":
        count += 1
        trace.check_iterations(count)

        if next_step == "search_listings":
            session["search_results"] = call_tool(
                "search_listings",
                {
                    "description": session["parsed"]["description"],
                    "size": session["parsed"]["size"],
                    "max_price": session["parsed"]["max_price"],
                },
            )
            # The branch: nothing found means stop here, before any model call.
            if not session["search_results"]:
                session["error"] = _no_results_message(session["parsed"])
                next_step = "done"
                note = "branch: empty, stopping"
            else:
                session["selected_item"] = session["search_results"][0]
                next_step = "suggest_outfit"
                note = "branch: found, taking the first result"
            trace.step(
                "search_listings (via MCP)",
                inputs=str(session["parsed"]),
                returned=session["search_results"],
                note=note,
            )

        elif next_step == "suggest_outfit":
            try:
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"], session["wardrobe"]
                )
            except ModelUnavailable as exc:
                next_step = _stop_on_model_error(session, "suggest_outfit", exc)
                continue
            trace.step(
                "suggest_outfit",
                inputs=session["selected_item"],
                returned=session["outfit_suggestion"],
            )
            next_step = "create_fit_card"

        elif next_step == "create_fit_card":
            try:
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"], session["selected_item"]
                )
            except ModelUnavailable as exc:
                next_step = _stop_on_model_error(session, "create_fit_card", exc)
                continue
            trace.step(
                "create_fit_card",
                inputs=session["selected_item"],
                returned=session["fit_card"],
            )
            next_step = "done"

    return session


# ── query parsing ─────────────────────────────────────────────────────────────

# "under $30", "below 30", "less than $30", "max $30", "$30 or less"
_PRICE_RE = re.compile(
    r"(?:under|below|less than|max(?:imum)?|up to|at most)\s*\$?\s*(\d+(?:\.\d+)?)"
    r"|\$\s*(\d+(?:\.\d+)?)\s*(?:or less|or under|max)?",
    re.IGNORECASE,
)

# "size M", "size XXS", "size US 9", "size W30", "size W30 L30", "size one size"
_SIZE_RE = re.compile(
    r"\bsize\s+(one size|us\s*\d+(?:\.\d+)?|w\d+(?:\s*l\d+)?|x{0,3}[sml]|x{1,3}l)\b",
    re.IGNORECASE,
)

# Words that describe the request rather than the item.
_FILLER_RE = re.compile(
    r"\b(?:i'?m|i am|looking for|look for|i want|want|i need|need|find me|find|"
    r"show me|something|anything|please|in|a|an|the)\b",
    re.IGNORECASE,
)


def parse_query(query: str) -> dict:
    """
    Pull a description, a size and a max_price out of a plain-language query,
    with regex. Anything not mentioned comes back as None.

        parse_query("vintage graphic tee under $30, size M")
        → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}
    """
    rest = query

    max_price = None
    price_match = _PRICE_RE.search(rest)
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))
        rest = rest[: price_match.start()] + " " + rest[price_match.end() :]

    size = None
    size_match = _SIZE_RE.search(rest)
    if size_match:
        size = re.sub(r"\s+", " ", size_match.group(1)).upper()
        if size == "ONE SIZE":
            size = "One Size"
        rest = rest[: size_match.start()] + " " + rest[size_match.end() :]

    rest = _FILLER_RE.sub(" ", rest)
    description = " ".join(re.sub(r"[^\w\s'-]", " ", rest).split())

    return {"description": description, "size": size, "max_price": max_price}


def _stop_on_model_error(session: dict, step: str, exc: ModelUnavailable) -> str:
    """Record which model step failed, say what to do, and end the loop."""
    item = session["selected_item"]
    stage = "the outfit" if step == "suggest_outfit" else "the fit card"
    session["error"] = (
        f"Couldn't reach the model while writing {stage}, so FitFindr stopped "
        f"there. {exc} Your search did find {item['title']} "
        f"(${item['price']:g} on {item['platform']}); run the same query again "
        f"once the model is reachable."
    )
    trace.step(step, inputs=item, note="model unavailable, stopping")
    return "done"


def _no_results_message(parsed: dict) -> str:
    """Say what was searched for and which parts the user could loosen."""
    searched = f"'{parsed['description']}'" if parsed["description"] else "your query"
    limits = []
    if parsed["size"]:
        limits.append(f"size {parsed['size']}")
    if parsed["max_price"] is not None:
        limits.append(f"under ${parsed['max_price']:g}")
    where = f" in {' and '.join(limits)}" if limits else ""

    tips = []
    if parsed["size"]:
        tips.append("drop the size or try a neighbouring one")
    if parsed["max_price"] is not None:
        tips.append("raise the max price")
    tips.append(
        "use broader keywords (e.g. 'jacket' instead of 'designer bomber jacket')"
    )
    if len(tips) > 1:
        tips[-1] = "or " + tips[-1]

    return (
        f"No listings matched {searched}{where}. To find something, "
        + "; ".join(tips)
        + "."
    )


# ── running it directly ───────────────────────────────────────────────────────


def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(
        f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}"
    )
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(
        run_agent(
            query="looking for a vintage graphic tee under $30",
            wardrobe=get_example_wardrobe(),
        )
    )

    print("\n=== A query it can't ===")
    _show(
        run_agent(
            query="designer ballgown size XXS under $5",
            wardrobe=get_example_wardrobe(),
        )
    )

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
