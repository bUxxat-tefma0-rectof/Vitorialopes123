import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import Bot

if __name__ == '__main__':
    bot = Bot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot encerrado!")
    except Exception as e:
        print(f"❌ Erro: {e}")
