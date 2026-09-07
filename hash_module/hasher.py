import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlparse


def build_metadata(matched_url: str, face_encoding: list):
    """
    Builds a metadata record describing the discovered match.

    Args:
        matched_url: the URL of the social media post that matched the face.
        face_encoding: the face embedding vector used for the search.

    Returns:
        A dictionary containing the matched URL, platform name, discovery
        timestamp, and the face encoding.
    """
    platform = urlparse(matched_url).netloc

    metadata = {
        "matched_url": matched_url,
        "platform": platform,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "face_encoding": face_encoding,
    }
    return metadata


def hash_metadata(metadata: dict):
    """
    Generates a SHA-256 hash of a metadata dictionary.

    Args:
        metadata: the metadata dictionary to hash.

    Returns:
        A hex string representing the SHA-256 hash of the metadata.
    """
    metadata_string = json.dumps(metadata, sort_keys=True)
    metadata_bytes = metadata_string.encode("utf-8")
    hash_object = hashlib.sha256(metadata_bytes)
    return hash_object.hexdigest()


if __name__ == "__main__":
    test_url = "https://in.linkedin.com/in/narendramodi"
    test_encoding = [0.1, 0.2, 0.3]

    metadata = build_metadata(test_url, test_encoding)
    print("Metadata:")
    print(json.dumps(metadata, indent=2))

    record_hash = hash_metadata(metadata)
    print(f"\nSHA-256 hash: {record_hash}")