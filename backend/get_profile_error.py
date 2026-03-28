import asyncio
import sys
sys.path.insert(0, 'd:\recruitment\backend')

import httpx
from app.core.security import create_access_token

async def test():
    # Get token for recruiter
    base_url = "http://localhost:8000"
    
    # Login first
    login_resp = await asyncio.gather(
        httpx.AsyncClient().post(
            f"{base_url}/auth/login",
            json={"email": "recruiter_pro@test.com", "password": "password123"}
        )
    )
    login_data = login_resp[0].json()
    token = login_data.get("token")
    
    # Get candidate ID from search
    search_resp = await asyncio.gather(
        httpx.AsyncClient().get(
            f"{base_url}/recruiter/candidates",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 1}
        )
    )
    search_data = search_resp[0].json()
    candidates = search_data.get("data", [])
    
    if not candidates:
        print("No candidates found!")
        return
    
    candidate_id = candidates[0]["id"]
    print(f"Testing with candidate ID: {candidate_id}")
    
    # Try to get profile
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{base_url}/recruiter/candidates/{candidate_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")

if __name__ == "__main__":
    asyncio.run(test())
