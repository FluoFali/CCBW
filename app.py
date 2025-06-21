import os, time, requests, uvicorn
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from fastapi import FastAPI
from pydantic import BaseModel

# ---------- config ----------
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE", "")
HEADERS = {
    "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
    "User-Agent": "Mozilla/5.0"
}
CSRF_TOKEN = ""
# ---------- helpers ----------
def refresh_csrf() -> bool:
    global CSRF_TOKEN, HEADERS
    r = requests.post("https://groups.roblox.com/v1/groups/2/users", headers=HEADERS)
    if r.status_code == 403 and "x-csrf-token" in r.headers:
        CSRF_TOKEN = r.headers["x-csrf-token"]
        HEADERS["x-csrf-token"] = CSRF_TOKEN
        return True
    return False
def create_badge_image(n: int) -> bytes:
    img = Image.new("RGB", (300, 300), "SkyBlue")
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), str(n), font=ImageFont.load_default(size=260), fill="white")
    buf = BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()
def upload_badge(universe_id: int, name: str, desc: str, img: bytes):
    if not refresh_csrf(): return {"error": "no csrf"}
    files = {
        "name": (None, name),
        "description": (None, desc),
        "paymentSourceType": (None, "1"),
        "files": ("badge.png", img, "image/png"),
        "expectedCost": (None, "0"),
        "isActive": (None, "true")
    }
    url = f"https://badges.roblox.com/v1/universes/{universe_id}/badges"
    r = requests.post(url, headers=HEADERS, files=files)
    return r.json() if r.ok else {"error": r.text}
# ---------- API ----------
app = FastAPI()
class BadgeReq(BaseModel):
    universe_id: int
    number: int
    badge_name: str
    badge_description: str
@app.post("/create_badge")
def create_badge(b: BadgeReq):
    img = create_badge_image(b.number)
    return upload_badge(b.universe_id, b.badge_name, b.badge_description, img)
@app.get("/ping")
def ping(): return {"pong": time.time()}
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
