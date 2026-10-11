"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3 — state. The item search picks has to be the item both
        # model calls receive: compare the `in:` lines of the suggest_outfit
        # and create_fit_card trace steps against selected_item. Picks
        # "Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)", the example
        # in criteria.md, and a different item from criteria 1 and 4.
        "name": "selected item reaches both model calls",
        "query": "levi's 501 jeans under $40",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4 — the fit card. The same query criteria.md names, run
        # five times (run_eval.py does the repeats) so the cards can be
        # compared: 2-4 sentences, price, platform, and no repeated first
        # sentence. Search picks "Y2K Baby Tee — Butterfly Print" ($18, depop),
        # so the price to look for is $18.
        "name": "fit card stays within spec",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5 — a user with nothing saved still gets model-written
        # advice, not suggest_outfit's fixed fallback sentence. Picks
        # "Denim Jacket — Light Wash, Cropped" ($42, poshmark).
        "name": "empty wardrobe gets real advice",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
