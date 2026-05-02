import requests
from config import Config

RAPIDAPI_HOST = "spotify23.p.rapidapi.com"
RAPIDAPI_BASE = f"https://{RAPIDAPI_HOST}"


def fetch_top_tracks(limit=20):
    """
    Busca tracks populares na RapidAPI do Spotify.
    Retorna lista de dicts normalizados ou None em caso de falha.
    """
    headers = {
        "X-RapidAPI-Key": Config.RAPID_API_SPOTIFY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }

    try:
        response = requests.get(
            f"{RAPIDAPI_BASE}/search/",
            headers=headers,
            params={
                "q": "trending",
                "type": "tracks",
                "offset": "0",
                "limit": str(limit),
                "numberOfTopResults": "5",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        items = data.get("tracks", {}).get("items", [])
        tracks = []

        for item in items[:limit]:
            track_data = item.get("data", {})
            album = track_data.get("albumOfTrack", {})
            cover_url = ""
            sources = album.get("coverArt", {}).get("sources", [])
            if sources:
                cover_url = sources[0].get("url", "")

            artists = [
                a.get("profile", {}).get("name", "")
                for a in track_data.get("artists", {}).get("items", [])
            ]

            tracks.append({
                "spotify_id": track_data.get("id", ""),
                "name": track_data.get("name", ""),
                "artist": ", ".join(filter(None, artists)),
                "album": album.get("name", ""),
                "cover_url": cover_url,
                "duration_ms": track_data.get("duration", {}).get("totalMilliseconds", 0),
                "spotify_url": album.get("sharingInfo", {}).get("shareUrl", ""),
            })

        return tracks

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("[RapidAPI] Rate limit excedido. Usando fallback mock.")
        else:
            print(f"[RapidAPI] Erro HTTP {e.response.status_code}: {e}")
        return None
    except Exception as e:
        print(f"[RapidAPI] Erro inesperado: {e}")
        return None


from services.seed_tracks import get_seed_tracks


def get_mock_tracks():
    """
    Fallback quando a RapidAPI falha (rate limit, indisponível).
    Retorna 20 músicas REAIS populares em vez de templates genéricos.
    """
    return get_seed_tracks()
