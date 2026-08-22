from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_workspace_loads_modular_styles_and_script():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "/assets/styles.css" in html
    assert "/assets/comparison.css" in html
    assert "/assets/itinerary.css" in html
    assert "/assets/app.js" in html

def test_itinerary_script_contains_v4_migration_and_validation():
    script = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    assert 'atlas.workspace.v4' in script
    assert "migrateState" in script
    assert "validateDay" in script
    assert "moveDragged" in script
    assert "suggestionCatalog" in script
