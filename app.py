# =============================================================================
#  PYTHON WEBHOOK SERVER - PRODUCTION READY UNTUK NORTHFLANK
# =============================================================================
from flask import Flask, request, jsonify
import ccxt
import json
import logging
import os # <-- Import pustaka 'os' untuk environment variables

# --- Konfigurasi Awal ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- PENGATURAN DARI ENVIRONMENT VARIABLES (LEBIH AMAN) ---
# Ambil konfigurasi dari Environment Variables yang akan Anda atur di Northflank.
# Ini jauh lebih aman daripada menuliskannya langsung di kode.
WEBHOOK_SECRET_KEY = os.environ.get('WEBHOOK_SECRET_KEY', 'default-secret-key-change-me')
API_KEY = os.environ.get('API_KEY')
API_SECRET = os.environ.get('API_SECRET')
EXCHANGE_ID = os.environ.get('EXCHANGE_ID', 'binance')
DEFAULT_TRADE_TYPE = os.environ.get('DEFAULT_TRADE_TYPE', 'future') # 'future' atau 'spot'

# Periksa apakah API keys ada
if not API_KEY or not API_SECRET:
    logging.error("FATAL: API_KEY atau API_SECRET tidak diatur di environment variables!")
    # Di lingkungan produksi, Anda mungkin ingin aplikasi berhenti jika kunci tidak ada.
    # exit() 

# Inisialisasi koneksi ke exchange
exchange_class = getattr(ccxt, EXCHANGE_ID)
exchange = exchange_class({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {
        'defaultType': DEFAULT_TRADE_TYPE,
    },
})

try:
    exchange.load_markets()
    logging.info(f"Berhasil terhubung ke {exchange.id} dan memuat pasar.")
except Exception as e:
    logging.error(f"Gagal terhubung ke exchange: {e}")

# --- Endpoint Webhook ---
@app.route('/webhook', methods=['POST'])
def webhook():
    logging.info("Webhook diterima!")
    try:
        data = json.loads(request.data)
        logging.info(f"Data diterima: {data}")

        if 'key' not in data or data['key'] != WEBHOOK_SECRET_KEY:
            logging.warning("Akses ditolak: Secret key tidak valid.")
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

        # Parsing data... (Sama seperti sebelumnya)
        strategy_id = data.get('strategy_id', 'N/A')
        action = data.get('action')
        side = data.get('side')
        symbol = data.get('symbol')
        qty = float(data.get('qty'))
        sl_price = float(data.get('stop_loss_price'))
        tp_price = float(data.get('take_profit_price'))

        logging.info(f"Sinyal ter-validasi dari '{strategy_id}': {action} {side} {qty} {symbol} | SL: {sl_price}, TP: {tp_price}")

        if action == 'enter':
            ccxt_symbol = symbol if '/' in symbol else f"{symbol[:-4]}/{symbol[-4:]}"
            order_type = 'market'
            params = {
                'stopLoss': {'type': 'stopMarket', 'triggerPrice': sl_price},
                'takeProfit': {'type': 'takeProfitMarket', 'triggerPrice': tp_price}
            }
            
            logging.info(f"Mempersiapkan order: {ccxt_symbol}, {order_type}, {side}, {qty}, params={params}")
            order = exchange.create_order(ccxt_symbol, order_type, side, qty, params=params)
            logging.info(f"========= ORDER BERHASIL DIKIRIM: {order['id']} =========")
            return jsonify({'status': 'success', 'order_details': order}), 200
        else:
            return jsonify({'status': 'ignored', 'message': f"Aksi '{action}' tidak didukung"}), 200

    except Exception as e:
        logging.error(f"Error saat memproses webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

# Server utama tidak perlu dijalankan dengan app.run() di sini
# Gunicorn akan mengimpor 'app' dari file ini.