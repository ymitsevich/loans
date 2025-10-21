"""Manual smoke test that exercises the full application workflow."""

from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid

import httpx


async def run_check() -> int:
    base_url = os.getenv("LOANS_API_BASE_URL", "http://localhost:8000")
    applicant_id = f"applicant-{uuid.uuid4().hex[:8]}"
    payload = {
        "applicant_id": applicant_id,
        "amount": 4500,
        "term_months": 24,
    }

    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        submit = await client.post("/application", json=payload)
        submit.raise_for_status()
        print(f"Submitted application {applicant_id}: {submit.json()}")

        deadline = time.monotonic() + float(os.getenv("LOANS_STATUS_TIMEOUT", "15"))
        poll_interval = float(os.getenv("LOANS_STATUS_POLL_INTERVAL", "0.5"))

        while True:
            status_resp = await client.get(f"/application/{applicant_id}")
            if status_resp.status_code == 404:
                print("Application not yet persisted; retrying...")
            else:
                status_resp.raise_for_status()
                body = status_resp.json()
                print(f"Latest status: {body}")
                if body.get("status") != "pending":
                    print("Application processed successfully.")
                    return 0

            if time.monotonic() > deadline:
                print("Timed out waiting for application processing.", file=sys.stderr)
                return 1
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    sys.exit(asyncio.run(run_check()))
