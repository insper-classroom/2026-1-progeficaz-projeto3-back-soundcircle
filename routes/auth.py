from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_access_cookies,
    unset_access_cookies,
)
import bcrypt
from models.user import get_user_by_email, get_user_by_display_name, create_user, get_user_by_id
from models.revoked_token import revoke_token
from utils.helpers import sanitize_text

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(silent=True) or {}
        email = sanitize_text(data.get("email", ""))
        password = data.get("password", "")
        display_name = sanitize_text(data.get("display_name", ""))

        if not email or not password or not display_name:
            return jsonify({"error": "E-mail, senha e nome de exibição são obrigatórios."}), 400

        if "@" not in email or "." not in email:
            return jsonify({"error": "E-mail inválido."}), 400

        if len(password) < 6:
            return jsonify({"error": "A senha deve ter pelo menos 6 caracteres."}), 400

        if get_user_by_email(email):
            return jsonify({"error": "E-mail já cadastrado."}), 409

        if get_user_by_display_name(display_name):
            return jsonify({"error": "Nome de exibição já está em uso."}), 409

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = create_user(email, password_hash, display_name)

        token = create_access_token(
            identity=user["_id"],
            additional_claims={
                "display_name": user["display_name"],
                "email": user["email"],
            },
        )

        resp = jsonify({
            "message": "Usuário criado com sucesso.",
            "user": {
                "id": user["_id"],
                "email": user["email"],
                "display_name": user["display_name"],
            },
        })
        set_access_cookies(resp, token)
        return resp, 201
    except Exception as e:
        current_app.logger.exception("Erro no registro")
        return jsonify({"error": "Erro interno ao processar cadastro. Tente novamente."}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True) or {}
        email = sanitize_text(data.get("email", ""))
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "E-mail e senha são obrigatórios."}), 400

        user = get_user_by_email(email)
        if not user:
            return jsonify({"error": "E-mail ou senha incorretos."}), 401

        if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return jsonify({"error": "E-mail ou senha incorretos."}), 401

        token = create_access_token(
            identity=user["_id"],
            additional_claims={
                "display_name": user["display_name"],
                "email": user["email"],
            },
        )

        resp = jsonify({
            "message": "Login realizado com sucesso.",
            "user": {
                "id": user["_id"],
                "email": user["email"],
                "display_name": user["display_name"],
            },
        })
        set_access_cookies(resp, token)
        return resp, 200
    except Exception as e:
        current_app.logger.exception("Erro no login")
        return jsonify({"error": "Erro interno ao processar login. Tente novamente."}), 500


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    exp = get_jwt()["exp"]
    revoke_token(jti, exp)

    resp = jsonify({"message": "Logout realizado com sucesso."})
    unset_access_cookies(resp)
    return resp, 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required(optional=True)
def me():
    identity = get_jwt_identity()
    if not identity:
        return jsonify({"authenticated": False}), 200

    user = get_user_by_id(identity)
    if not user:
        return jsonify({"authenticated": False}), 200

    return jsonify({
        "authenticated": True,
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "display_name": user["display_name"],
        },
    }), 200