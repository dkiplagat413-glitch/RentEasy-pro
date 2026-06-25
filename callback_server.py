from flask import Flask, request, jsonify

from supabase import create_client
import toml
import threading
import requests
import time
import os

app = Flask(__name__)


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@app.route("/callback", methods=["POST"])
def mpesa_callback():
    data = request.get_json()

    try:
        body = data["Body"]["stkCallback"]
        result_code = body["ResultCode"]

        if result_code == 0:
            items = body["CallbackMetadata"]["Item"]
            amount = next(i["Value"] for i in items if i["Name"] == "Amount")
            mpesa_code = next(i["Value"] for i in items if i["Name"] == "MpesaReceiptNumber")
            phone = next(i["Value"] for i in items if i["Name"] == "PhoneNumber")

            supabase.table("payments").update({
                "status": "completed",
                "transaction_id": mpesa_code
            }).eq("phone_number", str(phone)).eq("status", "pending").execute()

        else:
            print(f"Payment failed with code: {result_code}")

    except Exception as e:
        print(f"Callback error: {e}")

    return jsonify({"ResultCode": 0, "ResultDesc": "Success"})


def keep_alive():
    while True:
        time.sleep(600)
        try:
            requests.get("https://mpesa-callback-bddq.onrender.com/")
        except:
            pass


@app.route("/", methods=["GET"])
def home():
    return "M-Pesa Callback Server Running", 200


if __name__ == "__main__":
    t = threading.Thread(target=keep_alive, daemon=True)
    t.start()
    app.run(port=5000)


