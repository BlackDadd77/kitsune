from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

LOCAL_DIR = "./tanganemas_bunga_padi_v15_final"
DB_PELANGGAN = os.path.join(LOCAL_DIR, "bot/pelanggan.json")
LOG_FILE = "transaction_webhook.log"

def log_transaction(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}\n"
    print(entry.strip())
    with open(LOG_FILE, "a") as f:
        f.write(entry)

@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    try:
        # Terima data dari Gateway Pembayaran (ToyyibPay / Billplz / Custom API)
        data = request.form.to_dict() if request.form else request.json
        
        if not data:
            return jsonify({"status": "error", "message": "Tiada data diterima"}), 400

        # Contoh parameter standard gateway: billcode, status (1 = Berhasil), order_id, phone
        order_id = data.get('order_id', data.get('billcode', 'UNKNOWN_ID'))
        status = str(data.get('status', '0'))
        customer_phone = data.get('phone', data.get('customer_phone', '600000000000'))
        customer_name = data.get('name', 'Pelanggan Tangan Emas')

        log_transaction(f"WEBHOOK MASUK: Order ID {order_id} | Status: {status} | Tel: {customer_phone}")

        if status == '1': # 1 bermaksud transaksi BERJAYA
            # Baca database pelanggan.json yang ada
            if os.path.exists(DB_PELANGGAN):
                with open(DB_PELANGGAN, 'r', encoding='utf-8') as f:
                    pelanggan_list = json.load(f)
            else:
                pelanggan_list = []

            # Tambah atau kemas kini status pelanggan kepada VIP / Unlimited
            new_record = {
                "order_id": order_id,
                "nama": customer_name,
                "phone": customer_phone,
                "status_akaun": "AKTIF_UNLIMITED",
                "tarikh_bayar": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            pelanggan_list.append(new_record)

            # Simpan semula ke dalam pelanggan.json
            os.makedirs(os.path.dirname(DB_PELANGGAN), exist_ok=True)
            with open(DB_PELANGGAN, 'w', encoding='utf-8') as f:
                json.dump(pelanggan_list, f, indent=4, ensure_ascii=False)

            log_transaction(f"✅ Akaun berjaya diaktifkan & dikemas kini dalam pelanggan.json untuk {customer_phone}")
            
            return jsonify({"status": "success", "message": "Akaun diaktifkan secara real-time"}), 200
        else:
            log_transaction(f"⚠️ Transaksi gagal atau pending untuk Order ID: {order_id}")
            return jsonify({"status": "pending_or_failed", "message": "Status bukan kejayaan"}), 200

    except Exception as e:
            log_transaction(f"❌ Ralat Webhook: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Memulakan Server Webhook Termux pada port 5000...")
    app.run(host='0.0.0.0', port=5000)
