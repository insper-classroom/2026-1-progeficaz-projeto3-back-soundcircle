"""
Seed de 20 músicas reais populares.
Usado como fallback quando a RapidAPI está indisponível (rate limit, etc).
Isso garante que o usuário nunca veja templates genéricos como 'Música Pop 1'.
"""

SEED_TRACKS = [
    {"spotify_id": "seed_01", "name": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours", "cover_url": "https://i.scdn.co/image/ab67616d0000b2738863bc11d2aa12b54f5aeb36", "duration_ms": 200000, "spotify_url": "https://open.spotify.com/track/0VjIjW4GlUfm5Mv8vyyLtU"},
    {"spotify_id": "seed_02", "name": "Levitating", "artist": "Dua Lipa", "album": "Future Nostalgia", "cover_url": "https://i.scdn.co/image/ab67616d0000b273bd26ede1ae69327010d49946", "duration_ms": 203000, "spotify_url": "https://open.spotify.com/track/39LLxExYz6ewLAcYrzQQyP"},
    {"spotify_id": "seed_03", "name": "Stay", "artist": "The Kid LAROI, Justin Bieber", "album": "F*CK LOVE 3", "cover_url": "https://i.scdn.co/image/ab67616d0000b273c4e5b86c09a1e5674d3b0d19", "duration_ms": 141000, "spotify_url": "https://open.spotify.com/track/5PjdY0CKGZdEuoNab3yDmX"},
    {"spotify_id": "seed_04", "name": "Shape of You", "artist": "Ed Sheeran", "album": "÷ (Divide)", "cover_url": "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96", "duration_ms": 234000, "spotify_url": "https://open.spotify.com/track/7qiZfU4dY9lQabv8lsDsK7"},
    {"spotify_id": "seed_05", "name": "Someone You Loved", "artist": "Lewis Capaldi", "album": "Divinely Uninspired", "cover_url": "https://i.scdn.co/image/ab67616d0000b273fc2101e6889d6ce90277f533", "duration_ms": 182000, "spotify_url": "https://open.spotify.com/track/7qEHsqek33rTcFNT9PFqLf"},
    {"spotify_id": "seed_06", "name": "Sunflower", "artist": "Post Malone, Swae Lee", "album": "Spider-Man", "cover_url": "https://i.scdn.co/image/ab67616d0000b273e2e352d89826aef6dbd5ff8f", "duration_ms": 158000, "spotify_url": "https://open.spotify.com/track/3KkXRkHbMCARz0aVfEt68P"},
    {"spotify_id": "seed_07", "name": "As It Was", "artist": "Harry Styles", "album": "Harry's House", "cover_url": "https://i.scdn.co/image/ab67616d0000b273b46f74097655d7f755ca5b58", "duration_ms": 167000, "spotify_url": "https://open.spotify.com/track/4Dvkj6JhhA12EX05fT7y2e"},
    {"spotify_id": "seed_08", "name": "Heat Waves", "artist": "Glass Animals", "album": "Dreamland", "cover_url": "https://i.scdn.co/image/ab67616d0000b2739e495fb707973f3398700c29", "duration_ms": 238000, "spotify_url": "https://open.spotify.com/track/02MWAaffLxlfxAUY7c5dvx"},
    {"spotify_id": "seed_09", "name": "Perfect", "artist": "Ed Sheeran", "album": "÷ (Divide)", "cover_url": "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96", "duration_ms": 263000, "spotify_url": "https://open.spotify.com/track/0tgVpDi06FyKpA1zm0rEO5"},
    {"spotify_id": "seed_10", "name": "Believer", "artist": "Imagine Dragons", "album": "Evolve", "cover_url": "https://i.scdn.co/image/ab67616d0000b2735675e83f707f1d7271e5cf8a", "duration_ms": 204000, "spotify_url": "https://open.spotify.com/track/0pqnGHJpmpxLKifKRmU6WP"},
    {"spotify_id": "seed_11", "name": "Peaches", "artist": "Justin Bieber", "album": "Justice", "cover_url": "https://i.scdn.co/image/ab67616d0000b2738b5c6e0c6f8f4e5b0e1b4e4f", "duration_ms": 198000, "spotify_url": "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh"},
    {"spotify_id": "seed_12", "name": "Bad Guy", "artist": "Billie Eilish", "album": "WHEN WE ALL FALL ASLEEP", "cover_url": "https://i.scdn.co/image/ab67616d0000b27350a3147b4edd7701a876c558", "duration_ms": 194000, "spotify_url": "https://open.spotify.com/track/2Fxmhks0bxGSBdJ92vM42m"},
    {"spotify_id": "seed_13", "name": "Uptown Funk", "artist": "Mark Ronson, Bruno Mars", "album": "Uptown Special", "cover_url": "https://i.scdn.co/image/ab67616d0000b273e419ccba0baa8bd3f3d7fcf2", "duration_ms": 270000, "spotify_url": "https://open.spotify.com/track/32OlwWuMpZ6b0aN2RZOeMS"},
    {"spototify_id": "seed_14", "name": "Closer", "artist": "The Chainsmokers, Halsey", "album": "Collage", "cover_url": "https://i.scdn.co/image/ab67616d0000b273495ce6da9aeb159e94eaa453", "duration_ms": 244000, "spotify_url": "https://open.spotify.com/track/7BKLCZ1jbUBVqRi2FVlTVw"},
    {"spotify_id": "seed_15", "name": "Starboy", "artist": "The Weeknd, Daft Punk", "album": "Starboy", "cover_url": "https://i.scdn.co/image/ab67616d0000b2734718e2b124f79258be7bc452", "duration_ms": 230000, "spotify_url": "https://open.spotify.com/track/5aAx2yezTd8zXrkmtKl66Z"},
    {"spotify_id": "seed_16", "name": "Señorita", "artist": "Shawn Mendes, Camila Cabello", "album": "Romance", "cover_url": "https://i.scdn.co/image/ab67616d0000b273b0a9c586d086495506a9ef7c", "duration_ms": 191000, "spotify_url": "https://open.spotify.com/track/0TK2YIli7K1eL4a6j3dK7e"},
    {"spotify_id": "seed_17", "name": "Good 4 U", "artist": "Olivia Rodrigo", "album": "SOUR", "cover_url": "https://i.scdn.co/image/ab67616d0000b273a91c10fe9472d9bf895c4f8f", "duration_ms": 178000, "spotify_url": "https://open.spotify.com/track/6HU7h9RYOaPRFeh0R3UeAr"},
    {"spotify_id": "seed_18", "name": "Save Your Tears", "artist": "The Weeknd", "album": "After Hours", "cover_url": "https://i.scdn.co/image/ab67616d0000b2738863bc11d2aa12b54f5aeb36", "duration_ms": 215000, "spotify_url": "https://open.spotify.com/track/5QO79kh1waicV47iQA3Rjl"},
    {"spotify_id": "seed_19", "name": "Anti-Hero", "artist": "Taylor Swift", "album": "Midnights", "cover_url": "https://i.scdn.co/image/ab67616d0000b273bb54dde68cd23e2a268ae0f5", "duration_ms": 200000, "spotify_url": "https://open.spotify.com/track/0V3wPSX9ygBnCm8psDIegu"},
    {"spotify_id": "seed_20", "name": "Watermelon Sugar", "artist": "Harry Styles", "album": "Fine Line", "cover_url": "https://i.scdn.co/image/ab67616d0000b27377fdcfda6535601aff081b6a", "duration_ms": 174000, "spotify_url": "https://open.spotify.com/track/6UelLqGlWMcVH1E5c4H7lY"},
]


def get_seed_tracks():
    """Retorna cópia das 20 músicas seed."""
    return [dict(t) for t in SEED_TRACKS]
