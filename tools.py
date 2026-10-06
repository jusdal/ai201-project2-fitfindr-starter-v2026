"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import config  # noqa: F401 — you'll use this in search_listings
import re
from generate import generate
from utils.data_loader import load_listings

# ── Tool 1: search_listings ───────────────────────────────────────────────────

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "if",
    "in",
    "into",
    "is",
    "it",
    "no",
    "not",
    "of",
    "on",
    "or",
    "such",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "was",
    "will",
    "with",
}


def _keywords(text: str) -> set[str]:
    """
    Return a set of keywords from a string, lowercased and stripped of stopwords.

    Args:
        text: a string to extract keywords from

    Returns:
        A set of keywords.
    """
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _size_tokens(size: str) -> set[str]:
    """
    Return a set of tokens from a size string, lowercased.

    Args:
        size: a size string to extract tokens from

    Returns:
        A set of size tokens.
    """
    cleaned = re.sub(r"\([^)]*\)", " ", size or "")  # remove parenthetical content
    parts = [p.strip().upper() for p in cleaned.split("/")]
    return {p for p in parts if p}


def _size_matches(wanted: str | None, listing_size: str) -> bool:
    """
    Determine if a listing size matches a wanted size.

    Args:
        wanted: the desired size string
        listing_size: the size string from the listing

    Returns:
        True if the listing size matches the wanted size, False otherwise.
    """
    if not wanted:
        return True  # No size filtering if wanted is None or empty
    listing_tokens = _size_tokens(listing_size)
    if any(token.startswith("ONE SIZE") for token in listing_tokens):
        return True  # "One Size" matches any wanted size
    return bool(_size_tokens(wanted) & listing_tokens)  # Check for intersection


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    wanted = _keywords(description)
    if not wanted:
        return []

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if not _size_matches(size, listing["size"]):
            continue

        searchable = " ".join(
            [
                listing["title"],
                listing["description"],
                listing["category"],
                " ".join(listing["style_tags"]),
                " ".join(listing["colors"]),
                listing["brand"] or "",
            ]
        )
        score = len(wanted & _keywords(searchable))
        if score > 0:
            scored.append((score, listing))

    # sorted() is stable, so ties keep their order from the data file
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    item_text = _describe_item(new_item)
    items = (wardrobe or {}).get("items") or []

    if not items:
        prompt = (
            f"Someone is thinking about buying this thrifted piece:\n{item_text}\n\n"
            "They haven't told us what's in their wardrobe. Give one or two "
            "outfit ideas built around this piece, using common staples "
            "(e.g. jeans, a plain tee, sneakers) rather than specific items "
            "they own. Keep it to a short paragraph or a few bullet points."
        )
    else:
        wardrobe_text = "\n".join(_describe_wardrobe_item(i) for i in items)
        prompt = (
            f"Someone is thinking about buying this thrifted piece:\n{item_text}\n\n"
            f"Here is what's already in their wardrobe:\n{wardrobe_text}\n\n"
            "Suggest one or two outfits built around the new piece. Each outfit "
            "must name the specific wardrobe pieces it uses, exactly as they're "
            "named above. Only use pieces from the list. Keep it to a short "
            "paragraph or a few bullet points."
        )

    response = generate(prompt, system=_STYLIST_SYSTEM)
    if response.strip():
        return response
    return (
        f"Try the {new_item.get('title', 'piece')} with simple basics — straight "
        "jeans, a plain tee and clean sneakers — and let it be the focal point."
    )


_STYLIST_SYSTEM = (
    "You are a stylist who helps people style secondhand clothing. Be specific "
    "and practical. Never invent clothing the user owns."
)


def _describe_item(item: dict) -> str:
    """Format a listing dict as a few lines for a prompt. Brand may be None."""
    lines = [
        f"- Title: {item.get('title', 'Unknown item')}",
        f"- Category: {item.get('category', 'unknown')}",
        f"- Colors: {', '.join(item.get('colors') or []) or 'unknown'}",
        f"- Style: {', '.join(item.get('style_tags') or []) or 'unknown'}",
        f"- Description: {item.get('description', '')}",
    ]
    if item.get("brand"):
        lines.append(f"- Brand: {item['brand']}")
    return "\n".join(lines)


def _describe_wardrobe_item(item: dict) -> str:
    """Format one wardrobe item as a single prompt line. Notes may be None."""
    line = (
        f"- {item.get('name', 'Unnamed item')} ({item.get('category', 'unknown')}; "
        f"colors: {', '.join(item.get('colors') or []) or 'unknown'}; "
        f"style: {', '.join(item.get('style_tags') or []) or 'unknown'})"
    )
    if item.get("notes"):
        line += f" — {item['notes']}"
    return line


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "Can't write a fit card without an outfit suggestion."

    prompt = (
        f"Write a social media caption about this thrifted find:\n"
        f"{_describe_item(new_item)}\n"
        f"- Price: ${new_item.get('price', 0):.2f}\n"
        f"- Platform: {new_item.get('platform', 'a thrift app')}\n\n"
        f"How it's being styled:\n{outfit}\n\n"
        "Write two to four sentences, in first person, the way someone would "
        "actually post it — casual, not a product description. Mention the "
        "item's title, its price and the platform exactly once each. Be "
        "specific about the vibe of the outfit. Return only the caption."
    )
    return generate(prompt, system=_CAPTION_SYSTEM)


_CAPTION_SYSTEM = (
    "You write short, natural social media captions for people showing off "
    "secondhand finds. Sound like a real person, not a brand."
)
