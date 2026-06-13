"""
Droploo API service
Credentials: test_testcom / UZUOQBD6ZV6DHPQ9

Confirmed working endpoints (tested via Postman):
  GET  https://dropshipper.droploo.com/api/products
  GET  https://dropshipper.droploo.com/api/product/{id}
  POST https://backend.droploo.com/api/product/create-order
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _headers():
    """
    Headers exactly matching what Postman sends successfully.
    The server checks App-Key, App-Secret, Username.
    """
    return {
        "App-Key":      settings.DROPLOO_APP_KEY,
        "App-Secret":   settings.DROPLOO_APP_SECRET,
        "Username":     settings.DROPLOO_USERNAME,
        "Accept":       "application/json",
        "Content-Type": "application/json",
        # Mimic a real client to avoid server-side bot filtering
        "User-Agent":   "Mozilla/5.0 (compatible; Gazitrade/1.0)",
    }


def _get(path, timeout=30):
    """
    Generic GET. Returns (data_dict, None) on success or (None, error_str) on failure.
    """
    url = f"{settings.DROPLOO_BASE_URL}{path}"
    try:
        r = requests.get(url, headers=_headers(), timeout=timeout)
        logger.info(f"[Droploo] GET {path} → HTTP {r.status_code}")
        if r.status_code == 200:
            return r.json(), None
        # Return the actual server message so we can debug
        return None, f"HTTP {r.status_code}: {r.text[:300]}"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[Droploo] ConnectionError on {path}: {e}")
        return None, f"Connection failed: {e}"
    except requests.exceptions.Timeout:
        logger.error(f"[Droploo] Timeout on {path}")
        return None, "Request timed out after 30s"
    except Exception as e:
        logger.error(f"[Droploo] Unexpected error on {path}: {e}")
        return None, str(e)


def get_all_products():
    """GET /api/products → { products: [...], imagePath: '...' }"""
    data, err = _get("/products")
    if err:
        logger.error(f"[Droploo] get_all_products failed: {err}")
    return data


def get_product_detail(product_id):
    """GET /api/product/{id} → { product: { id, name, price, is_variable, ... } }"""
    data, err = _get(f"/product/{product_id}")
    if err:
        logger.error(f"[Droploo] get_product_detail({product_id}) failed: {err}")
    return data


def get_categories():
    """GET /api/categories → { categories: [...] } or None"""
    data, _ = _get("/categories")
    return data


def transfer_order(order):
    """
    POST https://backend.droploo.com/api/product/create-order
    Sends confirmed order to Droploo for fulfilment.
    Returns: { order_id: 'DRO...', message: '...' }
          or { status: 'error', message: '...' }
    """
    payload = {
        "invoice_number":       order.invoice_number,
        "customer_name":        order.customer_name,
        "customer_phone":       order.customer_phone,
        "delivery_cost":        float(order.delivery_cost),
        "customer_address":     order.customer_address,
        "price":                float(order.total),
        "discount":             float(order.discount),
        "advance":              float(order.advance),
        "product_quantity":     sum(i.qty for i in order.items.all()),
        "delivery_charge_type": order.delivery_type,
        "payment_type":         order.payment_type,
        "order_type":           "Dropshipping",
        "special_notes":        order.special_notes,
        "payment_gateway":      order.payment_gateway,
        "transaction_id":       order.transaction_id,
        "products": [
            {
                "id":    str(item.droploo_product_id),
                "price": float(item.price),
                "color": item.color or "",
                "size":  item.size  or "",
                "qty":   item.qty,
            }
            for item in order.items.all()
        ],
    }
    try:
        r = requests.post(
            settings.DROPLOO_ORDER_URL,
            json=payload,
            headers=_headers(),
            timeout=30
        )
        logger.info(f"[Droploo] transfer_order {order.invoice_number} → HTTP {r.status_code}")
        return r.json()
    except Exception as e:
        logger.error(f"[Droploo] transfer_order error: {e}")
        return {"status": "error", "message": str(e)}
