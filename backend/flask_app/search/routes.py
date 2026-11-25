from flask import Blueprint, Response

from flask_app.auth import current_user, token_required
from flask_app.common.serialization import json_response, read_query
from flask_app.common.validation import load_schema
from flask_app.search.schema import SearchQuerySchema
from flask_app.search.service import search_cards_service

search_bp = Blueprint("search", __name__)


@search_bp.get("/api/search/cards")
@token_required
def search_cards() -> Response:
    payload = load_schema(SearchQuerySchema(), read_query())
    return json_response(search_cards_service(current_user(), payload))
