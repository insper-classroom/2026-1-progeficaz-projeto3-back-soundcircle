from models.revoked_token import is_token_revoked


def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get("jti")
    if jti is None:
        return False
    return is_token_revoked(jti)
