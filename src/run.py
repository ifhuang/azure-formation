__author__ = 'Yifu Huang'

from src.azureformation import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)