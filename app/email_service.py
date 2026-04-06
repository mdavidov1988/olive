import httpx
import os


async def send_magic_link(email: str, token: str):
    base_url = os.getenv("BASE_URL", "http://localhost:8080")
    link = f"{base_url}/auth/verify?token={token}"
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "Olive <onboarding@resend.dev>")

    if not api_key:
        print(f"[DEV] Magic link for {email}: {link}")
        return

    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": from_email,
                "to": email,
                "subject": "Your Olive login link",
                "html": (
                    f"<p>Click to log in to Olive:</p>"
                    f'<p><a href="{link}" style="display:inline-block;padding:12px 24px;'
                    f'background:#7C3AED;color:white;border-radius:8px;text-decoration:none;'
                    f'font-weight:bold;">Log In to Olive</a></p>'
                    f"<p style='color:#888;font-size:13px;'>This link expires in 15 minutes.</p>"
                ),
            },
        )


async def send_invite(email: str, token: str, baby_name: str, inviter_name: str):
    base_url = os.getenv("BASE_URL", "http://localhost:8080")
    link = f"{base_url}/invite/accept?token={token}"
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "Olive <onboarding@resend.dev>")

    if not api_key:
        print(f"[DEV] Invite link for {email}: {link}")
        return

    who = inviter_name or "Someone"
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": from_email,
                "to": email,
                "subject": f"You're invited to track {baby_name} on Olive",
                "html": (
                    f"<p>{who} invited you to help track <strong>{baby_name}</strong> on Olive.</p>"
                    f'<p><a href="{link}" style="display:inline-block;padding:12px 24px;'
                    f'background:#7C3AED;color:white;border-radius:8px;text-decoration:none;'
                    f'font-weight:bold;">Accept Invite</a></p>'
                    f"<p style='color:#888;font-size:13px;'>This invite expires in 7 days.</p>"
                ),
            },
        )
