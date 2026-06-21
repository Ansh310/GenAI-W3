import os
import re
import requests

HF_BASE = "https://huggingface.co"


def normalize_arxiv_id(
    value: str,
) -> str:

    value = value.strip()

    patterns = [
        r"arxiv\.org/abs/([^/?]+)",
        r"huggingface\.co/papers/([^/?]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            value,
        )

        if match:
            return match.group(1)

    return value


def _headers():

    token = os.getenv("HF_TOKEN")

    if token:
        return {
            "Authorization":
            f"Bearer {token}"
        }

    return {}


def paper_search(
    query: str,
    limit: int = 5,
) -> dict:

    try:

        response = requests.get(
            f"{HF_BASE}/api/papers/search",
            params={"q": query},
            headers=_headers(),
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        papers = []

        for item in data[:limit]:

            paper_id = item.get("id", {})

            if isinstance(paper_id, dict):
                arxiv_id = paper_id.get("id", "")
            else:
                arxiv_id = paper_id

            papers.append(
                {
                    "arxiv_id":
                    arxiv_id,
                    "title":
                    item.get(
                        "title",
                        "",
                    ),
                    "abstract":
                    item.get(
                        "summary",
                        ""
                    )[:1000],
                    "url":
                    f"https://arxiv.org/abs/{arxiv_id}",
                }
            )

        return {"papers": papers}

    except Exception as e:
        return {"error": str(e)}


def read_paper(
    arxiv_id: str,
) -> dict:

    try:

        arxiv_id = normalize_arxiv_id(
            arxiv_id
        )

        meta = requests.get(
            f"{HF_BASE}/api/papers/{arxiv_id}",
            headers=_headers(),
            timeout=20,
        )

        if meta.status_code == 404:
            return {
                "error":
                "Paper not indexed"
            }

        meta.raise_for_status()

        metadata = meta.json()

        md_url = (
            f"{HF_BASE}/papers/"
            f"{arxiv_id}.md"
        )

        md_resp = requests.get(
            md_url,
            headers=_headers(),
            timeout=20,
        )

        content = ""

        if md_resp.ok:
            content = md_resp.text

        return {
            "arxiv_id": arxiv_id,
            "title":
            metadata.get(
                "title",
                "",
            ),
            "abstract":
            metadata.get(
                "summary",
                "",
            ),
            "content":
            content[:30000],
            "url":
            f"https://arxiv.org/abs/{arxiv_id}",
        }

    except Exception as e:
        return {"error": str(e)}
