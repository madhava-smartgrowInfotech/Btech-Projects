"""Capture authenticated screenshots too."""
import asyncio, requests
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
SHOT = BASE / "screenshots"

async def main():
    from playwright.async_api import async_playwright
    # create user via API
    import uuid
    email = f"shot{uuid.uuid4().hex[:6]}@example.com"
    r = requests.post("http://localhost:8000/api/auth/register", json={"name":"Shot Learner","email":email,"password":"secret123","confirm_password":"secret123"})
    tok = r.json().get("token","")
    requests.put("http://localhost:8000/api/profile", json={"education":"Bachelor Degree","skill_level":"Beginner","interests":"python, data science, machine learning","preferred_topics":"Machine Learning, Python","learning_style":"Self-paced","goals":"get a data job","course_preferences":"hands-on","weekly_hours":6,"age_band":"25-34","gender":"F"}, headers={"X-Token": tok})
    # seed an interaction
    requests.post("http://localhost:8000/api/interactions", json={"course_id":"PY101","event_type":"quiz","value":1.0}, headers={"X-Token": tok})
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width":1280,"height":800})
        await ctx.add_cookies([{"name":"lpq_token","value":tok,"domain":"localhost","path":"/"}])
        pg = await ctx.new_page()
        for route, name in [("/dashboard","05-dashboard.png"),("/recommendations","06-recommendations.png"),("/course/PY101","10-course-detail.png"),("/path","07-learning-path.png"),("/insights","08-insights.png"),("/activity","11-activity.png"),("/analytics","09-analytics.png"),("/onboarding","04-onboarding.png")]:
            await pg.goto("http://localhost:8000"+route, wait_until="networkidle", timeout=20000)
            await pg.wait_for_timeout(1500)
            await pg.screenshot(path=str(SHOT/name))
            print("shot", name)
        await b.close()
asyncio.run(main())
