"""
Tests for the Lorcast MCP Server (Disney Lorcana Card Data).

Uses unittest with unittest.mock to patch HTTP calls. No real API calls are made.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure the module under test can be imported
sys.path.insert(0, os.path.dirname(__file__))

import server


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(json_data, status_code=200, text=None):
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = text if text is not None else json.dumps(json_data)
    resp.raise_for_status.return_value = None
    return resp


def _parse(result: str):
    """Parse a JSON string returned by a tool."""
    return json.loads(result)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SETS = {
    "results": [
        {
            "id": "set_7ecb0e0c71af496a9e0110e23824e0a5",
            "name": "The First Chapter",
            "code": "1",
            "released_at": "2023-08-18",
            "prereleased_at": "2023-08-18",
        },
        {
            "id": "set_142d2dfb5d4b4b739a1017dc4bb0fcd2",
            "name": "Rise of the Floodborn",
            "code": "2",
            "released_at": "2023-11-17",
            "prereleased_at": "2023-11-17",
        },
    ]
}

SAMPLE_SET = {
    "id": "set_7ecb0e0c71af496a9e0110e23824e0a5",
    "name": "The First Chapter",
    "code": "1",
    "released_at": "2023-08-18T00:00:00.000Z",
    "prereleased_at": "2023-08-18T00:00:00.000Z",
}

SAMPLE_CARD = {
    "id": "crd_cbc18e77d7ec4d50bf19650a9a559686",
    "name": "Elsa",
    "version": "Spirit of Winter",
    "layout": "normal",
    "released_at": "2023-08-18",
    "image_uris": {
        "digital": {
            "small": "https://cards.lorcast.io/card/digital/small/crd_cbc18e77d7ec4d50bf19650a9a559686.avif?1709690747",
            "normal": "https://cards.lorcast.io/card/digital/normal/crd_cbc18e77d7ec4d50bf19650a9a559686.avif?1709690747",
            "large": "https://cards.lorcast.io/card/digital/large/crd_cbc18e77d7ec4d50bf19650a9a559686.avif?1709690747",
        }
    },
    "cost": 8,
    "inkwell": False,
    "ink": "Amethyst",
    "type": ["Character"],
    "classifications": ["Floodborn", "Hero", "Queen", "Sorcerer"],
    "text": "Shift 6",
    "move_cost": None,
    "strength": 4,
    "willpower": 6,
    "lore": 3,
    "rarity": "Enchanted",
    "illustrators": ["Matthew Robert Davies"],
    "collector_number": "207",
    "lang": "en",
    "flavor_text": None,
    "tcgplayer_id": 510153,
    "legalities": {"core": "legal"},
    "set": {
        "id": "set_7ecb0e0c71af496a9e0110e23824e0a5",
        "code": "1",
        "name": "The First Chapter",
    },
    "prices": {"usd": None, "usd_foil": 1267.58},
}

SAMPLE_SEARCH_RESULTS = {"results": [SAMPLE_CARD]}

SAMPLE_SET_CARDS = [SAMPLE_CARD]


# ---------------------------------------------------------------------------
# Test: HTTP helpers
# ---------------------------------------------------------------------------

class TestHTTPHelpers(unittest.TestCase):

    def setUp(self):
        server._last_request_time = 0.0

    @patch("server.requests.get")
    def test_get_success(self, mock_get):
        mock_get.return_value = _mock_response({"ok": True})
        result = server._get("sets")
        self.assertEqual(result, {"ok": True})
        mock_get.assert_called_once()

    @patch("server.requests.get")
    def test_get_with_params(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SEARCH_RESULTS)
        result = server._get("cards/search", params={"q": "elsa"})
        self.assertEqual(result, SAMPLE_SEARCH_RESULTS)
        call_kwargs = mock_get.call_args
        self.assertEqual(call_kwargs.kwargs.get("params") or call_kwargs[1].get("params"), {"q": "elsa"})

    @patch("server.requests.get")
    def test_get_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_resp
        with self.assertRaises(Exception):
            server._get("sets/invalid")


# ---------------------------------------------------------------------------
# Test: show_version
# ---------------------------------------------------------------------------

class TestShowVersion(unittest.TestCase):

    def test_show_version(self):
        result = _parse(server.show_version())
        self.assertIn("version", result)
        self.assertIn("server", result)
        self.assertEqual(result["server"], "Lorcast MCP Server")
        self.assertEqual(result["api_base_url"], "https://api.lorcast.com/v0")


# ---------------------------------------------------------------------------
# Test: Sets
# ---------------------------------------------------------------------------

class TestSets(unittest.TestCase):

    def setUp(self):
        server._last_request_time = 0.0

    @patch("server.requests.get")
    def test_list_sets(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SETS)
        result = _parse(server.list_sets())
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["name"], "The First Chapter")

    @patch("server.requests.get")
    def test_get_set_by_code(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SET)
        result = _parse(server.get_set("1"))
        self.assertEqual(result["name"], "The First Chapter")
        self.assertEqual(result["code"], "1")

    @patch("server.requests.get")
    def test_get_set_by_id(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SET)
        result = _parse(server.get_set("set_7ecb0e0c71af496a9e0110e23824e0a5"))
        self.assertEqual(result["name"], "The First Chapter")

    @patch("server.requests.get")
    def test_get_set_cards(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SET_CARDS)
        result = _parse(server.get_set_cards("1"))
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["name"], "Elsa")

    @patch("server.requests.get")
    def test_get_set_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_resp
        result = _parse(server.get_set("9999"))
        self.assertIn("error", result)


# ---------------------------------------------------------------------------
# Test: Cards
# ---------------------------------------------------------------------------

class TestCards(unittest.TestCase):

    def setUp(self):
        server._last_request_time = 0.0

    @patch("server.requests.get")
    def test_search_cards(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SEARCH_RESULTS)
        result = _parse(server.search_cards("elsa"))
        self.assertIn("results", result)
        self.assertEqual(result["results"][0]["name"], "Elsa")

    @patch("server.requests.get")
    def test_search_cards_with_unique(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SEARCH_RESULTS)
        result = _parse(server.search_cards("elsa", unique="prints"))
        self.assertIn("results", result)
        # Verify the params were passed
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        self.assertEqual(params["unique"], "prints")

    @patch("server.requests.get")
    def test_search_cards_complex_query(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SEARCH_RESULTS)
        result = _parse(server.search_cards("elsa set:1 rarity:enchanted"))
        self.assertIn("results", result)

    @patch("server.requests.get")
    def test_get_card(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_CARD)
        result = _parse(server.get_card("1", "207"))
        self.assertEqual(result["name"], "Elsa")
        self.assertEqual(result["version"], "Spirit of Winter")
        self.assertEqual(result["rarity"], "Enchanted")
        self.assertEqual(result["cost"], 8)

    @patch("server.requests.get")
    def test_get_card_full_data(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_CARD)
        result = _parse(server.get_card("1", "207"))
        self.assertEqual(result["ink"], "Amethyst")
        self.assertEqual(result["strength"], 4)
        self.assertEqual(result["willpower"], 6)
        self.assertEqual(result["lore"], 3)
        self.assertIn("Character", result["type"])
        self.assertIn("Floodborn", result["classifications"])

    @patch("server.requests.get")
    def test_get_card_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_resp
        result = _parse(server.get_card("1", "9999"))
        self.assertIn("error", result)


# ---------------------------------------------------------------------------
# Test: Card Images
# ---------------------------------------------------------------------------

class TestCardImages(unittest.TestCase):

    def setUp(self):
        server._last_request_time = 0.0

    @patch("server.requests.get")
    def test_get_card_image_uris(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_CARD)
        result = _parse(server.get_card_image_uris("1", "207"))
        self.assertEqual(result["name"], "Elsa")
        self.assertIn("image_uris", result)
        digital = result["image_uris"]["digital"]
        self.assertIn("small", digital)
        self.assertIn("normal", digital)
        self.assertIn("large", digital)
        self.assertTrue(digital["large"].startswith("https://cards.lorcast.io/"))


# ---------------------------------------------------------------------------
# Test: Prices
# ---------------------------------------------------------------------------

class TestPrices(unittest.TestCase):

    def setUp(self):
        server._last_request_time = 0.0

    @patch("server.requests.get")
    def test_get_card_prices(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_CARD)
        result = _parse(server.get_card_prices("1", "207"))
        self.assertEqual(result["name"], "Elsa")
        self.assertIn("prices", result)
        self.assertEqual(result["prices"]["usd_foil"], 1267.58)
        self.assertIsNone(result["prices"]["usd"])
        self.assertEqual(result["rarity"], "Enchanted")


# ---------------------------------------------------------------------------
# Test: Convenience / ink & rarity search
# ---------------------------------------------------------------------------

class TestConvenienceTools(unittest.TestCase):

    def setUp(self):
        server._last_request_time = 0.0

    @patch("server.requests.get")
    def test_get_cards_by_ink(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SEARCH_RESULTS)
        result = _parse(server.get_cards_by_ink("Amethyst"))
        self.assertIn("results", result)
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        self.assertEqual(params["q"], "ink:Amethyst")

    @patch("server.requests.get")
    def test_get_cards_by_rarity(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_SEARCH_RESULTS)
        result = _parse(server.get_cards_by_rarity("Enchanted"))
        self.assertIn("results", result)
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        self.assertEqual(params["q"], "rarity:Enchanted")


# ---------------------------------------------------------------------------
# Test: _ok / _err helpers
# ---------------------------------------------------------------------------

class TestHelperFunctions(unittest.TestCase):

    def test_ok(self):
        result = json.loads(server._ok({"key": "value"}))
        self.assertEqual(result["key"], "value")

    def test_err(self):
        result = json.loads(server._err("something went wrong"))
        self.assertEqual(result["error"], "something went wrong")


if __name__ == "__main__":
    unittest.main()
