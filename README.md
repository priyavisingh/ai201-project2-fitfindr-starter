# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

| Tool | Inputs | Returns | Purpose |
|------|--------|---------|---------|
| `search_listings` | `description` (str), `size` (str \| None), `max_price` (float \| None) | `list[dict]` — each dict is a full listing with fields: `id`, `title`, `description`, `category`, `style_tags` (list[str]), `size`, `condition`, `price` (float), `colors` (list[str]), `brand` (str \| None), `platform` (str). Sorted by relevance (best match first). Returns `[]` if nothing matches — never raises. | Searches the mock listings dataset by keywords, optional size, and price ceiling |
| `suggest_outfit` | `new_item` (dict), `wardrobe` (dict) | `str` — non-empty outfit suggestion naming specific wardrobe pieces, or general styling advice if `wardrobe["items"]` is empty. Never raises. | Uses Groq LLM (`llama-3.3-70b-versatile`) to suggest outfit combinations |
| `create_fit_card` | `outfit` (str), `new_item` (dict) | `str` — 2–4 sentence casual social caption mentioning item name, price, and platform once each; varies across runs (temperature 0.95). Returns an error message string if `outfit` is empty — never raises. | Uses Groq LLM to generate a shareable Instagram/TikTok caption |

**Planning loop:** `run_agent()` in `agent.py` parses the query with regex, then calls `search_listings()`. If `session["search_results"]` is empty, it sets `session["error"]` and returns early without calling `suggest_outfit` or `create_fit_card`. If results exist, it sets `session["selected_item"] = results[0]`, calls `suggest_outfit()`, then `create_fit_card()`, and returns the session.

**State management:** All state lives in a `session` dict. `selected_item` from search is passed directly to `suggest_outfit` and `create_fit_card`. `outfit_suggestion` from `suggest_outfit` is passed directly to `create_fit_card` — no re-parsing or user re-entry between steps.

**AI usage:** (1) For tool implementations, I gave Cursor the Tool 1–3 spec blocks from `planning.md` and the `tools.py` stubs; I revised the output to use simple keyword scoring and `try/except` fallbacks for LLM failures. (2) For the planning loop, I gave Cursor the Architecture diagram and Planning Loop + State Management sections; I revised the size-parsing regex after a failing test for `"in size M"` queries.

---

## Interaction Walkthrough

**User query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1 — Tool called:**
- Tool: `search_listings`
- Input: `description="vintage graphic tee"`, `size=None`, `max_price=30.0`
- Why this tool: User wants to find a thrift item — search runs first before any styling
- Output: List of matching listings; top result `lst_002` — *Y2K Baby Tee — Butterfly Print*, $18, Depop — stored as `session["selected_item"]`

**Step 2 — Tool called:**
- Tool: `suggest_outfit`
- Input: `new_item=session["selected_item"]`, `wardrobe=example_wardrobe`
- Why this tool: User asked how to style it — uses the found item and their wardrobe
- Output: Outfit string pairing the tee with baggy jeans and chunky sneakers from the wardrobe

**Step 3 — Tool called:**
- Tool: `create_fit_card`
- Input: `outfit=session["outfit_suggestion"]`, `new_item=session["selected_item"]`
- Why this tool: Generate a shareable caption for the complete look
- Output: Casual Instagram-style caption mentioning item, price, and platform

**Final output to user:** Three Gradio panels — top listing details, outfit suggestion, and fit card caption.

---

## Error Handling and Fail Points

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No results match the query | Agent sets `session["error"]` to: *"No listings found for 'designer ballgown' in size XXS under $5. Try broadening your search — remove the size filter, raise your price limit, or use different keywords."* Returns early; `outfit_suggestion` and `fit_card` stay `None`. UI shows error in first panel only, other two panels empty. |
| `suggest_outfit` | Wardrobe is empty | Not an error — returns general styling advice (e.g., pairing suggestions based on item style tags). Agent continues to fit card. |
| `create_fit_card` | Outfit input is missing or incomplete | Returns: *"Can't create a fit card without an outfit suggestion. Please run outfit styling first."* |

---

## Spec Reflection

**One way planning.md helped during implementation:**

Writing the conditional planning loop in planning.md before coding made the early-exit branch after empty search results explicit. When implementing `run_agent()`, I could follow the spec step-by-step — especially the rule to not call `suggest_outfit` when search returns nothing — which prevented a common rubric failure.

**One divergence from your spec, and why:**

The spec suggested parsing size with patterns like `size M` or `in M`. During testing, queries like `"90s track jacket in size M"` failed because `in` alone matched before `size`. I updated the regex to `(?:\b(?:size|in)\s+)+` so chained phrases like `in size M` correctly extract `M` as the size.

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
