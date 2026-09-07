import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
VISION_API_URL = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

SOCIAL_DOMAINS = ["instagram.com", "facebook.com", "linkedin.com", "twitter.com", "x.com"]


def get_web_detection(image_path: str):
    """
    Sends an image to Google Cloud Vision's Web Detection API and
    returns the full webDetection result.
    """
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    request_body = {
        "requests": [
            {
                "image": {"content": encoded_image},
                "features": [{"type": "WEB_DETECTION"}],
            }
        ]
    }

    response = requests.post(VISION_API_URL, json=request_body)
    response.raise_for_status()
    result = response.json()

    return result["responses"][0].get("webDetection", {})


def identify_top_entity(web_detection: dict):
    """
    Extracts the highest-confidence recognized entity (e.g. a person's name).
    """
    entities = web_detection.get("webEntities", [])
    named_entities = [e for e in entities if "description" in e]

    if not named_entities:
        return None, None

    top_entity = max(named_entities, key=lambda e: e["score"])
    return top_entity["description"], top_entity["score"]


def get_candidate_images(web_detection: dict):
    """
    Extracts every candidate page along with its direct image URLs,
    usable for face verification (as opposed to a webpage URL, which
    isn't an image).

    Returns:
        A list of dicts, each with 'page_url', 'page_title', and 'image_url'.
    """
    pages = web_detection.get("pagesWithMatchingImages", [])
    candidates = []

    for page in pages:
        image_urls = []
        if page.get("fullMatchingImages"):
            image_urls.extend(img["url"] for img in page["fullMatchingImages"])
        if page.get("partialMatchingImages"):
            image_urls.extend(img["url"] for img in page["partialMatchingImages"])

        for image_url in image_urls:
            candidates.append({
                "page_url": page["url"],
                "page_title": page.get("pageTitle", ""),
                "image_url": image_url,
            })

    return candidates


def categorize_pages(web_detection: dict):
    """
    Splits all matching pages into social media vs other websites
    (news, articles, blogs, etc.), each with title and URL.
    """
    pages = web_detection.get("pagesWithMatchingImages", [])
    social = []
    other = []

    for page in pages:
        entry = {"url": page["url"], "title": page.get("pageTitle", "")}
        if any(domain in page["url"] for domain in SOCIAL_DOMAINS):
            social.append(entry)
        else:
            other.append(entry)

    return social, other


def get_visually_similar_images(web_detection: dict, limit: int = 10):
    """
    Extracts visually similar image URLs as a fallback when no confirmed
    match is found. This is general visual similarity, not identity match.
    """
    similar = web_detection.get("visuallySimilarImages", [])
    return [img["url"] for img in similar[:limit]]


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python web_search.py <image_path>")
        sys.exit(1)

    web_detection = get_web_detection(sys.argv[1])

    entity_name, entity_score = identify_top_entity(web_detection)
    print(f"Top identified entity: {entity_name} (confidence: {entity_score})")

    candidates = get_candidate_images(web_detection)
    print(f"\nFound {len(candidates)} candidate images to verify:")
    for c in candidates:
        print(f"  page: {c['page_url']}")
        print(f"  image: {c['image_url']}")