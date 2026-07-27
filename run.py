import sys
import os
import threading
from flask import Flask

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Servidor web simples para o Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🐕 Bot Online!"

def start_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))

# Iniciar Flask em thread separada
threading.Thread(target=start_flask, daemon=True).start()

# Iniciar bot
from main import main

if __name__ == '__main__':
    main()
