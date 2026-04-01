import streamlit as st
import requests
import json

st.set_page_config(page_title="Extensiv API Tool", layout="wide")

st.title("📦 Extensiv API Tester (Auto ETag)")

# -----------------------------
# Session State Init
# -----------------------------
if "etag" not in st.session_state:
    st.session_state.etag = ""

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("🔑 Auth & Config")

access_token = st.sidebar.text_input("Access Token", type="password")
base_url = "https://secure-wms.com"

# -----------------------------
# API Selection
# -----------------------------
api_option = st.selectbox(
    "Select API Action",
    [
        "Get Order Details",
        "Delete Order Item",
        "Update Tracking",
        "Close Order"
    ]
)

# -----------------------------
# Common Inputs
# -----------------------------
order_id = st.text_input("Order ID")

# Show current ETag
st.info(f"Current ETag: {st.session_state.etag or 'Not Fetched'}")

# Manual override (optional)
manual_etag = st.text_input("Override ETag (Optional)")

# Final ETag to use
etag = manual_etag if manual_etag else st.session_state.etag

# -----------------------------
# Extra Inputs
# -----------------------------
item_id = None
payload = None

if api_option == "Delete Order Item":
    item_id = st.text_input("Item ID")

elif api_option == "Update Tracking":
    payload = st.text_area(
        "Tracking Payload (JSON)",
        value=json.dumps({
            "trackingNumber": "8459455201",
            "carrier": "USPS"
        }, indent=4)
    )

elif api_option == "Close Order":
    payload = st.text_area(
        "Close Order Payload (JSON)",
        value=json.dumps({
            "confirmDate": "2026-01-01T23:00:00",
            "trackingNumber": "FDX123456",
            "carrier": "FedEx"
        }, indent=4)
    )

# -----------------------------
# Fetch ETag Button
# -----------------------------
if st.button("🔄 Fetch ETag from Order"):
    if not access_token or not order_id:
        st.error("Access Token and Order ID required!")
    else:
        try:
            url = f"{base_url}/orders/{order_id}?detail=all&itemdetail=Allocationswithdetail"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/hal+json"
            }

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                etag_value = response.headers.get("ETag")

                if etag_value:
                    st.session_state.etag = etag_value
                    st.success(f"ETag fetched: {etag_value}")
                else:
                    st.warning("ETag not found in headers")

            else:
                st.error(f"Failed: {response.status_code}")
                st.text(response.text)

        except Exception as e:
            st.error(str(e))

# -----------------------------
# Execute API
# -----------------------------
if st.button("🚀 Execute API"):

    if not access_token or not order_id:
        st.error("Access Token and Order ID are required!")
        st.stop()

    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/hal+json"
        }

        url = ""

        # -----------------------------
        # API Logic
        # -----------------------------
        if api_option == "Get Order Details":
            url = f"{base_url}/orders/{order_id}?detail=all&itemdetail=Allocationswithdetail"
            response = requests.get(url, headers=headers)

            # 🔥 Auto store ETag here also
            etag_value = response.headers.get("ETag")
            if etag_value:
                st.session_state.etag = etag_value

        elif api_option == "Delete Order Item":
            if not item_id or not etag:
                st.error("Item ID and ETag required!")
                st.stop()

            url = f"{base_url}/orders/{order_id}/items/{item_id}"

            headers.update({
                "Content-Type": "application/hal+json",
                "If-Match": etag
            })

            response = requests.delete(url, headers=headers)

        elif api_option == "Update Tracking":
            if not etag:
                st.error("ETag required!")
                st.stop()

            url = f"{base_url}/orders/{order_id}/routing"

            headers.update({
                "Content-Type": "application/hal+json; charset=utf-8",
                "If-Match": etag
            })

            response = requests.put(url, headers=headers, data=payload)

        elif api_option == "Close Order":
            if not etag:
                st.error("ETag required!")
                st.stop()

            url = f"{base_url}/orders/{order_id}/confirmer"

            headers.update({
                "Content-Type": "application/json; charset=utf-8",
                "If-Match": etag
            })

            response = requests.post(url, headers=headers, data=payload)

        # -----------------------------
        # Response Output
        # -----------------------------
        st.subheader("📡 Response")
        st.write("Status Code:", response.status_code)

        try:
            st.json(response.json())
        except:
            st.text(response.text)

    except Exception as e:
        st.error(f"Error: {str(e)}")