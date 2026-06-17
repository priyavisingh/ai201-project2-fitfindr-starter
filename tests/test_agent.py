from agent import run_agent, _parse_query
from utils.data_loader import get_example_wardrobe


def test_parse_query_extracts_price_and_description():
    parsed = _parse_query("vintage graphic tee under $30")
    assert parsed["max_price"] == 30.0
    assert "graphic tee" in parsed["description"].lower()


def test_parse_query_extracts_size():
    parsed = _parse_query("90s track jacket in size M")
    assert parsed["size"] == "M"
    assert "track jacket" in parsed["description"].lower()


def test_agent_no_results_sets_error():
    session = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    assert session["error"] is not None
    assert session["outfit_suggestion"] is None
    assert session["fit_card"] is None


def test_agent_happy_path_populates_state():
    session = run_agent(
        query="vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    assert session["error"] is None
    assert session["selected_item"] is not None
    assert session["outfit_suggestion"]
    assert session["fit_card"]


def test_state_selected_item_flows_from_search():
    """Rubric: selected_item from search is passed to suggest_outfit without re-entry."""
    session = run_agent(
        query="vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    assert session["selected_item"] is session["search_results"][0]
    assert session["selected_item"]["id"] == session["search_results"][0]["id"]


def test_state_outfit_flows_to_fit_card():
    """Rubric: outfit_suggestion from suggest_outfit feeds create_fit_card on happy path."""
    session = run_agent(
        query="vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    assert session["outfit_suggestion"]
    assert session["fit_card"]
    assert session["error"] is None


def test_no_results_error_is_actionable():
    session = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    assert "try broadening" in session["error"].lower()
    assert "designer ballgown" in session["error"].lower()
