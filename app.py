from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from utils.jwt_helpers import check_if_token_revoked
from routes.auth import auth_bp
from routes.user import user_bp
from routes.feed import feed_bp
from routes.friends import friends_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.FLASK_SECRET_KEY
app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = Config.JWT_ACCESS_TOKEN_EXPIRES
app.config["JWT_TOKEN_LOCATION"] = Config.JWT_TOKEN_LOCATION
app.config["JWT_COOKIE_SECURE"] = Config.JWT_COOKIE_SECURE
app.config["JWT_COOKIE_SAMESITE"] = Config.JWT_COOKIE_SAMESITE
app.config["JWT_COOKIE_CSRF_PROTECT"] = Config.JWT_COOKIE_CSRF_PROTECT
app.config["JWT_ACCESS_COOKIE_NAME"] = Config.JWT_ACCESS_COOKIE_NAME
app.config["JWT_ERROR_MESSAGE_KEY"] = "error"

CORS(
    app,
    origins=[Config.FRONTEND_URL],
    supports_credentials=True,
)

jwt = JWTManager(app)
jwt.token_in_blocklist_loader(check_if_token_revoked)

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(feed_bp)
app.register_blueprint(friends_bp)


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Recurso não encontrado."}), 404


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({"error": "Dados inválidos ou malformados."}), 422


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Erro interno do servidor."}), 500


if __name__ == "__main__":
    app.run(debug=True)
