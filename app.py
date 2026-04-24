from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/feed", methods=["GET"])
def get_feed():
    return jsonify({"message": "Feed funcionando!"})

if __name__ == "__main__":
    app.run(debug=True)