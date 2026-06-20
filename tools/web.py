import os
import requests
import trafilatura

SERPER_URL = (
    "https://google.serper.dev/search"
)


def web_search(
    query: str,
    num_results: int = 5,
) -> dict:

    api_key = os.getenv(
        "SERPER_API_KEY"
    )

    if not api_key:
        return {
            "error":
            "SERPER_API_KEY not set"
        }

    try:

        response = requests.post(
            SERPER_URL,
            headers={
                "X-API-KEY": api_key,
                "Content-Type":
                "application/json",
            },
            json={"q": query},
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get(
            "organic",
            []
        )[:num_results]:

            results.append(
                {
                    "title":
                    item.get(
                        "title",
                        "",
                    ),
                    "url":
                    item.get(
                        "link",
                        "",
                    ),
                    "snippet":
                    item.get(
                        "snippet",
                        "",
                    ),
                }
            )

        return {
            "query": query,
            "results": results,
        }

    except Exception as e:
        return {"error": str(e)}


def web_fetch(
    url: str,
) -> dict:

    try:

        downloaded = (
            trafilatura.fetch_url(url)
        )

        if not downloaded:
            return {
                "error":
                "Failed to download page"
            }

        text = trafilatura.extract(
            downloaded,
            include_links=True,
            include_images=False,
        )

        if not text:
            text = downloaded[:10000]

        return {
            "url": url,
            "content": text[:15000],
        }

    except Exception as e:
        return {"error": str(e)}