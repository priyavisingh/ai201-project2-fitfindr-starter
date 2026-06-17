"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()

LLM_MODEL = "llama-3.3-70b-versatile"


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _call_llm(prompt: str, temperature: float = 0.7) -> str:
    """Call the Groq LLM and return the response text."""
    client = _get_groq_client()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase keyword tokens."""
    return [t for t in re.split(r"[^\w]+", text.lower()) if len(t) > 1]


def _score_listing(listing: dict, keywords: list[str]) -> int:
    """Score a listing by keyword overlap across searchable fields."""
    searchable = " ".join([
        listing.get("title", ""),
        listing.get("description", ""),
        listing.get("category", ""),
        " ".join(listing.get("style_tags", [])),
    ]).lower()

    return sum(1 for kw in keywords if kw in searchable)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()
    keywords = _tokenize(description)

    if not keywords:
        return []

    filtered = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and size.lower() not in listing["size"].lower():
            continue
        score = _score_listing(listing, keywords)
        if score > 0:
            filtered.append((score, listing))

    filtered.sort(key=lambda x: x[0], reverse=True)
    return [listing for _, listing in filtered]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    items = wardrobe.get("items", [])
    title = new_item.get("title", "this item")
    tags = ", ".join(new_item.get("style_tags", []))
    colors = ", ".join(new_item.get("colors", []))
    category = new_item.get("category", "item")

    try:
        if not items:
            prompt = f"""You are a personal stylist. A user found this thrifted item and has no wardrobe saved yet.

Item: {title}
Category: {category}
Style tags: {tags}
Colors: {colors}

Suggest general styling ideas — what types of pieces pair well with this item, what vibe it suits, and 1-2 complete outfit directions they could build. Be specific and practical. Keep it to 3-5 sentences."""
        else:
            wardrobe_lines = "\n".join(
                f"- {item['name']} ({item['category']}, {', '.join(item['style_tags'])})"
                for item in items
            )
            prompt = f"""You are a personal stylist. A user found this thrifted item and wants outfit ideas using their existing wardrobe.

New item: {title}
Category: {category}
Style tags: {tags}
Colors: {colors}

Their wardrobe:
{wardrobe_lines}

Suggest 1-2 complete outfit combinations using the new item and specific pieces from their wardrobe by name. Include a styling tip (tucking, rolling sleeves, layering, etc.). Keep it to 3-5 sentences."""

        return _call_llm(prompt, temperature=0.7)

    except Exception:
        tag_hint = tags if tags else category
        if items:
            names = ", ".join(item["name"] for item in items[:3])
            return (
                f"Pair {title} with pieces from your wardrobe like {names}. "
                f"The {tag_hint} vibe works well with relaxed, layered looks."
            )
        return (
            f"This {category} has a {tag_hint} feel — try pairing it with "
            f"relaxed denim and chunky sneakers for an easy everyday look."
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return (
            "Can't create a fit card without an outfit suggestion. "
            "Please run outfit styling first."
        )

    title = new_item.get("title", "this find")
    price = new_item.get("price", 0)
    platform = new_item.get("platform", "a thrift app")

    try:
        prompt = f"""Write a casual Instagram/TikTok caption for someone's outfit of the day. This is a real thrift find, not a product ad.

Item: {title}
Price: ${price:.0f}
Platform: {platform}
Outfit: {outfit}

Rules:
- 2-4 sentences, casual and authentic (like a real OOTD post)
- Mention the item, price, and platform naturally once each
- Capture the vibe in specific terms
- No hashtags, no "link in bio", no marketing language
- Sound like a real person sharing their fit"""

        return _call_llm(prompt, temperature=0.95)

    except Exception:
        return (
            f"thrifted this {title.lower()} off {platform} for ${price:.0f} "
            f"and i'm obsessed with how it came together 🖤"
        )
