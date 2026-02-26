"""
Tests for the CardTrader MCP Server (Full API Bridge).

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

FAKE_TOKEN = "test_token_abc123"


def _patch_config():
    """Patch _get_config to return a fake token."""
    return patch.object(server, "_get_config", return_value={"api_token": FAKE_TOKEN})


def _reset_headers():
    """Reset the cached headers between tests."""
    server._client_headers = None


# ---------------------------------------------------------------------------
# Test: Configuration
# ---------------------------------------------------------------------------

class TestConfig(unittest.TestCase):

    def test_config_from_env_token(self):
        with patch.dict(os.environ, {"MCP_CARDTRADER_TOKEN": "tok123"}, clear=False):
            # Remove other config sources
            with patch.dict(os.environ, {}, clear=False):
                cfg = server._get_config()
                self.assertEqual(cfg["api_token"], "tok123")

    def test_config_from_env_json(self):
        cfg_json = json.dumps({"api_token": "json_tok"})
        with patch.dict(os.environ, {"MCP_CARDTRADER_CONFIG": cfg_json}, clear=False):
            cfg = server._get_config()
            self.assertEqual(cfg["api_token"], "json_tok")

    def test_config_from_file(self):
        with patch.dict(os.environ, {}, clear=True):
            fake_cfg = json.dumps({"api_token": "file_tok"})
            m_open = unittest.mock.mock_open(read_data=fake_cfg)
            with patch("builtins.open", m_open), \
                 patch("os.path.exists", return_value=True):
                cfg = server._get_config()
                self.assertEqual(cfg["api_token"], "file_tok")

    def test_config_missing_raises(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch("os.path.exists", return_value=False):
            with self.assertRaises(Exception):
                server._get_config()


# ---------------------------------------------------------------------------
# Test: HTTP helpers
# ---------------------------------------------------------------------------

class TestHTTPHelpers(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    @patch("server.requests.get")
    def test_get(self, mock_get):
        mock_get.return_value = _mock_response({"ok": True})
        with _patch_config():
            result = server._get("info")
        self.assertEqual(result, {"ok": True})
        mock_get.assert_called_once()

    @patch("server.requests.post")
    def test_post(self, mock_post):
        mock_post.return_value = _mock_response({"result": "ok"})
        with _patch_config():
            result = server._post("cart/add", {"product_id": 1, "quantity": 1})
        self.assertEqual(result, {"result": "ok"})

    @patch("server.requests.put")
    def test_put(self, mock_put):
        mock_put.return_value = _mock_response({"result": "ok"})
        with _patch_config():
            result = server._put("products/1", {"price": 5.0})
        self.assertEqual(result, {"result": "ok"})

    @patch("server.requests.delete")
    def test_delete(self, mock_delete):
        mock_delete.return_value = _mock_response({"result": "ok"})
        with _patch_config():
            result = server._delete("products/1")
        self.assertEqual(result, {"result": "ok"})


# ---------------------------------------------------------------------------
# Test: Reference tools
# ---------------------------------------------------------------------------

class TestReferenceTools(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    @patch("server._get")
    def test_get_app_info(self, mock_get):
        mock_get.return_value = {"id": 1, "name": "TestApp", "user_id": 42}
        with _patch_config():
            result = _parse(server.get_app_info())
        self.assertEqual(result["id"], 1)

    @patch("server._get")
    def test_list_games(self, mock_get):
        mock_get.return_value = {"array": [
            {"id": 1, "name": "magic", "display_name": "Magic: the Gathering"},
            {"id": 7, "name": "lorcana", "display_name": "Disney Lorcana"},
        ]}
        with _patch_config():
            result = _parse(server.list_games())
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["name"], "lorcana")

    @patch("server._get")
    def test_list_games_plain_array(self, mock_get):
        """Handles API returning a plain array (no wrapper)."""
        mock_get.return_value = [{"id": 1, "name": "magic"}]
        with _patch_config():
            result = _parse(server.list_games())
        self.assertIsInstance(result, list)

    @patch("server._get")
    def test_list_categories(self, mock_get):
        mock_get.return_value = [{"id": 1, "name": "Single Cards", "game_id": 1}]
        with _patch_config():
            result = _parse(server.list_categories(game_id=1))
        self.assertEqual(len(result), 1)

    @patch("server._get")
    def test_list_expansions_filter(self, mock_get):
        mock_get.return_value = [
            {"id": 100, "game_id": 1, "code": "M20", "name": "Core Set 2020"},
            {"id": 200, "game_id": 7, "code": "TFC", "name": "The First Chapter"},
        ]
        with _patch_config():
            result = _parse(server.list_expansions(game_id=7))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["code"], "TFC")

    @patch("server._get")
    def test_list_blueprints(self, mock_get):
        mock_get.return_value = [{"id": 500, "name": "Test Card", "expansion_id": 100}]
        with _patch_config():
            result = _parse(server.list_blueprints(expansion_id=100))
        self.assertEqual(result[0]["name"], "Test Card")


# ---------------------------------------------------------------------------
# Test: Marketplace tools
# ---------------------------------------------------------------------------

class TestMarketplaceTools(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    def test_marketplace_requires_filter(self):
        result = _parse(server.list_marketplace_products())
        self.assertIn("error", result)

    @patch("server._get")
    def test_list_marketplace_products(self, mock_get):
        mock_get.return_value = {"500": [{"id": 1, "price": {"cents": 100}}]}
        with _patch_config():
            result = _parse(server.list_marketplace_products(blueprint_id=500))
        self.assertIn("500", result)

    @patch("server._get")
    def test_get_cart(self, mock_get):
        mock_get.return_value = {"id": 1, "subcarts": []}
        with _patch_config():
            result = _parse(server.get_cart())
        self.assertEqual(result["id"], 1)

    @patch("server._post")
    def test_add_to_cart(self, mock_post):
        mock_post.return_value = {"id": 1, "subcarts": []}
        with _patch_config():
            result = _parse(server.add_to_cart(product_id=1, quantity=1))
        self.assertIn("id", result)
        call_body = mock_post.call_args[0][1]
        self.assertEqual(call_body["product_id"], 1)
        self.assertTrue(call_body["via_cardtrader_zero"])

    @patch("server._post")
    def test_add_to_cart_with_address(self, mock_post):
        mock_post.return_value = {"id": 1}
        addr = json.dumps({"name": "Test", "city": "Madrid"})
        with _patch_config():
            server.add_to_cart(product_id=1, quantity=1, billing_address=addr)
        call_body = mock_post.call_args[0][1]
        self.assertEqual(call_body["billing_address"]["name"], "Test")

    @patch("server._post")
    def test_remove_from_cart(self, mock_post):
        mock_post.return_value = {"id": 1}
        with _patch_config():
            result = _parse(server.remove_from_cart(product_id=1, quantity=1))
        self.assertIn("id", result)

    @patch("server._post")
    def test_purchase_cart(self, mock_post):
        mock_post.return_value = {"id": 1, "purchased": True}
        with _patch_config():
            result = _parse(server.purchase_cart())
        self.assertIn("id", result)

    @patch("server._get")
    def test_list_shipping_methods(self, mock_get):
        mock_get.return_value = [{"id": 1, "name": "Standard"}]
        with _patch_config():
            result = _parse(server.list_shipping_methods(username="seller1"))
        self.assertEqual(result[0]["name"], "Standard")


# ---------------------------------------------------------------------------
# Test: Wishlist tools
# ---------------------------------------------------------------------------

class TestWishlistTools(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    @patch("server._get")
    def test_list_wishlists(self, mock_get):
        mock_get.return_value = [{"id": 1, "name": "My List"}]
        with _patch_config():
            result = _parse(server.list_wishlists())
        self.assertEqual(result[0]["name"], "My List")

    @patch("server._get")
    def test_get_wishlist(self, mock_get):
        mock_get.return_value = {"id": 1, "name": "My List", "items": []}
        with _patch_config():
            result = _parse(server.get_wishlist(wishlist_id=1))
        self.assertEqual(result["id"], 1)

    @patch("server._post")
    def test_create_wishlist(self, mock_post):
        mock_post.return_value = {"id": 2, "name": "New"}
        items = json.dumps([{"blueprint_id": 500, "quantity": 1}])
        with _patch_config():
            result = _parse(server.create_wishlist(name="New", game_id=7, items=items))
        self.assertEqual(result["name"], "New")
        call_body = mock_post.call_args[0][1]
        self.assertEqual(call_body["deck"]["game_id"], 7)
        self.assertIn("deck_items_attributes", call_body["deck"])

    @patch("server._post")
    def test_create_wishlist_text(self, mock_post):
        mock_post.return_value = {"id": 3, "name": "Text"}
        with _patch_config():
            result = _parse(server.create_wishlist(
                name="Text", game_id=1, items_text="4 Lightning Bolt"
            ))
        call_body = mock_post.call_args[0][1]
        self.assertIn("deck_items_from_text_deck", call_body["deck"])

    def test_create_wishlist_requires_items(self):
        result = _parse(server.create_wishlist(name="X", game_id=1))
        self.assertIn("error", result)

    @patch("server._delete")
    def test_delete_wishlist(self, mock_del):
        mock_del.return_value = {"result": "ok"}
        with _patch_config():
            result = _parse(server.delete_wishlist(wishlist_id=1))
        self.assertNotIn("error", result)


# ---------------------------------------------------------------------------
# Test: Inventory tools
# ---------------------------------------------------------------------------

class TestInventoryTools(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    @patch("server._get")
    def test_list_my_expansions(self, mock_get):
        mock_get.return_value = [{"id": 100, "name": "Test Exp"}]
        with _patch_config():
            result = _parse(server.list_my_expansions())
        self.assertEqual(len(result), 1)

    @patch("server._get")
    def test_list_my_products(self, mock_get):
        mock_get.return_value = [{"id": 1, "name_en": "Card", "quantity": 3}]
        with _patch_config():
            result = _parse(server.list_my_products(expansion_id=100))
        self.assertEqual(result[0]["quantity"], 3)

    @patch("server._post")
    def test_create_product(self, mock_post):
        mock_post.return_value = {"result": "ok", "resource": {"id": 10}}
        with _patch_config():
            result = _parse(server.create_product(
                blueprint_id=500, price=3.50, quantity=2
            ))
        self.assertEqual(result["result"], "ok")

    @patch("server._post")
    def test_create_product_with_properties(self, mock_post):
        mock_post.return_value = {"result": "ok"}
        props = json.dumps({"condition": "Near Mint", "mtg_language": "en"})
        with _patch_config():
            server.create_product(
                blueprint_id=500, price=1.0, quantity=1, properties=props
            )
        call_body = mock_post.call_args[0][1]
        self.assertEqual(call_body["properties"]["condition"], "Near Mint")

    @patch("server._put")
    def test_update_product(self, mock_put):
        mock_put.return_value = {"result": "ok"}
        with _patch_config():
            result = _parse(server.update_product(product_id=10, price=5.0))
        self.assertEqual(result["result"], "ok")

    @patch("server._delete")
    def test_delete_product(self, mock_del):
        mock_del.return_value = {"result": "ok"}
        with _patch_config():
            result = _parse(server.delete_product(product_id=10))
        self.assertNotIn("error", result)

    @patch("server._post")
    def test_increment_product(self, mock_post):
        mock_post.return_value = {"result": "ok"}
        with _patch_config():
            result = _parse(server.increment_product(product_id=10, delta_quantity=-1))
        self.assertEqual(result["result"], "ok")
        call_body = mock_post.call_args[0][1]
        self.assertEqual(call_body["delta_quantity"], -1)

    @patch("server._delete")
    def test_remove_product_image(self, mock_del):
        mock_del.return_value = {"result": "ok"}
        with _patch_config():
            result = _parse(server.remove_product_image(product_id=10))
        self.assertNotIn("error", result)


# ---------------------------------------------------------------------------
# Test: Batch operations
# ---------------------------------------------------------------------------

class TestBatchTools(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    @patch("server._post")
    def test_batch_create(self, mock_post):
        mock_post.return_value = {"job": "uuid-123"}
        products = json.dumps([
            {"blueprint_id": 1, "price": 1.0, "quantity": 1},
            {"blueprint_id": 2, "price": 2.0, "quantity": 1},
        ])
        with _patch_config():
            result = _parse(server.batch_create_products(products=products))
        self.assertEqual(result["job"], "uuid-123")

    def test_batch_create_invalid_json(self):
        result = _parse(server.batch_create_products(products="not json"))
        self.assertIn("error", result)

    @patch("server._post")
    def test_batch_update(self, mock_post):
        mock_post.return_value = {"job": "uuid-456"}
        products = json.dumps([{"id": 10, "price": 5.0}])
        with _patch_config():
            result = _parse(server.batch_update_products(products=products))
        self.assertEqual(result["job"], "uuid-456")

    @patch("server._post")
    def test_batch_delete_json(self, mock_post):
        mock_post.return_value = {"job": "uuid-789"}
        with _patch_config():
            result = _parse(server.batch_delete_products(
                product_ids='[{"id": 1}, {"id": 2}]'
            ))
        self.assertEqual(result["job"], "uuid-789")

    @patch("server._post")
    def test_batch_delete_csv(self, mock_post):
        mock_post.return_value = {"job": "uuid-csv"}
        with _patch_config():
            result = _parse(server.batch_delete_products(product_ids="1,2,3"))
        self.assertEqual(result["job"], "uuid-csv")
        call_body = mock_post.call_args[0][1]
        self.assertEqual(len(call_body["products"]), 3)

    @patch("server._get")
    def test_get_job_status(self, mock_get):
        mock_get.return_value = {"uuid": "u1", "state": "completed", "stats": {"ok": 2}}
        with _patch_config():
            result = _parse(server.get_job_status(uuid="u1"))
        self.assertEqual(result["state"], "completed")


# ---------------------------------------------------------------------------
# Test: CSV Import tools
# ---------------------------------------------------------------------------

class TestCSVImportTools(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    @patch("server._get")
    def test_csv_import_status(self, mock_get):
        mock_get.return_value = {"id": 1, "imported_count": 50, "skipped_count": 2}
        with _patch_config():
            result = _parse(server.get_csv_import_status(import_id=1))
        self.assertEqual(result["imported_count"], 50)

    @patch("server._get")
    def test_csv_import_skipped(self, mock_get):
        mock_get.return_value = {"csv": "row1\nrow2"}
        with _patch_config():
            result = _parse(server.get_csv_import_skipped(import_id=1))
        self.assertIn("csv", result)


# ---------------------------------------------------------------------------
# Test: Order tools
# ---------------------------------------------------------------------------

class TestOrderTools(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    @patch("server._get")
    def test_list_orders(self, mock_get):
        mock_get.return_value = [{"id": 100, "state": "paid"}]
        with _patch_config():
            result = _parse(server.list_orders(state="paid"))
        self.assertEqual(result[0]["state"], "paid")

    @patch("server._get")
    def test_list_orders_date_filter(self, mock_get):
        mock_get.return_value = []
        with _patch_config():
            server.list_orders(from_date="2024-01-01", to_date="2024-12-31")
        # _get is called as _get("orders", params_dict)
        call_args = mock_get.call_args[0]  # positional args
        params = call_args[1]  # second positional arg is the params dict
        self.assertIn("from", params)
        self.assertEqual(params["from"], "2024-01-01")
        self.assertEqual(params["to"], "2024-12-31")

    @patch("server._get")
    def test_get_order(self, mock_get):
        mock_get.return_value = {"id": 100, "order_items": []}
        with _patch_config():
            result = _parse(server.get_order(order_id=100))
        self.assertEqual(result["id"], 100)

    @patch("server._put")
    def test_set_tracking_code(self, mock_put):
        mock_put.return_value = {"id": 100, "tracking_code": "TRACK1"}
        with _patch_config():
            result = _parse(server.set_tracking_code(order_id=100, tracking_code="TRACK1"))
        self.assertNotIn("error", result)

    @patch("server._put")
    def test_ship_order(self, mock_put):
        mock_put.return_value = {"id": 100, "state": "sent"}
        with _patch_config():
            result = _parse(server.ship_order(order_id=100))
        self.assertEqual(result["state"], "sent")

    @patch("server._put")
    def test_request_cancellation(self, mock_put):
        mock_put.return_value = {"id": 100, "state": "request_for_cancel"}
        explanation = "The card is damaged and cannot be shipped to the buyer safely."
        with _patch_config():
            result = _parse(server.request_cancellation(
                order_id=100, cancel_explanation=explanation
            ))
        call_body = mock_put.call_args[0][1]
        self.assertEqual(call_body["cancel_explanation"], explanation)

    @patch("server._put")
    def test_confirm_cancellation(self, mock_put):
        mock_put.return_value = {"id": 100, "state": "canceled"}
        with _patch_config():
            result = _parse(server.confirm_cancellation(order_id=100, relist_if_cancelled=True))
        call_body = mock_put.call_args[0][1]
        self.assertTrue(call_body["relist_if_cancelled"])


# ---------------------------------------------------------------------------
# Test: CT Zero Box tools
# ---------------------------------------------------------------------------

class TestCT0BoxTools(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    @patch("server._get")
    def test_list_ct0_box_items(self, mock_get):
        mock_get.return_value = [{"id": 1, "name": "Card A"}]
        with _patch_config():
            result = _parse(server.list_ct0_box_items())
        self.assertEqual(len(result), 1)

    @patch("server._get")
    def test_get_ct0_box_item(self, mock_get):
        mock_get.return_value = {"id": 1, "name": "Card A", "quantity": {"ok": 1}}
        with _patch_config():
            result = _parse(server.get_ct0_box_item(item_id=1))
        self.assertEqual(result["id"], 1)


# ---------------------------------------------------------------------------
# Test: Version tool
# ---------------------------------------------------------------------------

class TestVersionTool(unittest.TestCase):

    def test_show_version(self):
        result = _parse(server.show_version())
        self.assertIn("version", result)
        self.assertEqual(result["version"], "1.0.0")

    def test_show_version_includes_changelog(self):
        result = _parse(server.show_version())
        self.assertIn("recent_changes", result)
        self.assertIsInstance(result["recent_changes"], list)
        self.assertGreater(len(result["recent_changes"]), 0)


# ---------------------------------------------------------------------------
# Test: Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling(unittest.TestCase):

    def setUp(self):
        _reset_headers()

    @patch("server._get", side_effect=Exception("Connection timeout"))
    def test_tool_returns_error_on_exception(self, mock_get):
        with _patch_config():
            result = _parse(server.get_app_info())
        self.assertIn("error", result)
        self.assertIn("Connection timeout", result["error"])

    def test_ok_format(self):
        result = server._ok({"key": "value"})
        parsed = json.loads(result)
        self.assertEqual(parsed["key"], "value")

    def test_err_format(self):
        result = server._err("something went wrong")
        parsed = json.loads(result)
        self.assertEqual(parsed["error"], "something went wrong")


if __name__ == "__main__":
    unittest.main()
