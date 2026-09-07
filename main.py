import sys
import os
import tempfile
import requests
import time
from face_module.face_encoder import get_face_encoding, verify_faces
from search_module.web_search import get_web_detection, identify_top_entity, get_candidate_images, get_visually_similar_images
from hash_module.hasher import build_metadata, hash_metadata
from chain_module.chain_writer import store_hash_on_chain, get_record_from_chain


def download_temp_image(image_url: str):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name
    except Exception:
        return None


def name_appears_in_page(entity_name: str, page_title: str, page_url: str):
    if not entity_name:
        return False
    name_parts = [p.lower() for p in entity_name.split() if len(p) > 2]
    haystack = (page_title + " " + page_url).lower()
    return any(part in haystack for part in name_parts)


def find_all_verified_matches(original_image_path: str, web_detection: dict, entity_name: str):
    candidates = get_candidate_images(web_detection)
    verified_matches = []

    for candidate in candidates:
        temp_path = download_temp_image(candidate["image_url"])
        if temp_path is None:
            continue

        try:
            verified, distance = verify_faces(original_image_path, temp_path)
        except Exception:
            verified, distance = False, None
        finally:
            os.remove(temp_path)

        if verified and name_appears_in_page(entity_name, candidate["page_title"], candidate["page_url"]):
            verified_matches.append({
                "page_url": candidate["page_url"],
                "page_title": candidate["page_title"],
                "distance": distance,
            })

    return verified_matches


def _execute_pipeline(image_path: str):
    """
    Runs the full pipeline and returns a dictionary of results.
    This is the single source of truth used by both the CLI and the API.
    """
    result = {}

    face_encoding = get_face_encoding(image_path)
    result["encoding_length"] = len(face_encoding)

    web_detection = get_web_detection(image_path)
    entity_name, entity_score = identify_top_entity(web_detection)
    result["identified_entity"] = entity_name
    result["confidence"] = entity_score

    verified_matches = find_all_verified_matches(image_path, web_detection, entity_name)

    if verified_matches:
        match_status = "VERIFIED"
        matched_url = verified_matches[0]["page_url"]
        distance = verified_matches[0]["distance"]
    else:
        match_status = "UNVERIFIED"
        distance = None
        similar_images = get_visually_similar_images(web_detection)
        if similar_images:
            matched_url = similar_images[0]
        else:
            raise ValueError("No matches or similar images found at all.")

    result["match_status"] = match_status
    result["matched_url"] = matched_url
    result["distance"] = distance
    result["verified_match_count"] = len(verified_matches)

    metadata = build_metadata(matched_url, face_encoding)
    metadata["match_status"] = match_status
    record_hash = hash_metadata(metadata)
    result["hash"] = record_hash

    tx_hash = store_hash_on_chain(record_hash)
    result["tx_hash"] = tx_hash
    result["explorer_url"] = f"https://amoy.polygonscan.com/tx/{tx_hash}"

    time.sleep(10)

    from chain_module.chain_writer import contract
    record_count = contract.functions.getRecordCount().call()
    latest_record_id = record_count - 1
    stored_hash, timestamp, submitter = get_record_from_chain(latest_record_id)

    result["record_id"] = latest_record_id
    result["stored_hash"] = stored_hash
    result["timestamp"] = timestamp
    result["submitter"] = submitter
    result["on_chain_match"] = (stored_hash == record_hash)

    return result


def run_pipeline(image_path: str):
    """
    CLI entry point: runs the pipeline and prints progress, like before.
    """
    print("=" * 60)
    print("STEP 1: Face Detection & Encoding")
    print("=" * 60)

    print("\n" + "=" * 60)
    print("STEP 2: Web Search & Face Verification")
    print("=" * 60)

    result = _execute_pipeline(image_path)

    print(f"Identified: {result['identified_entity']} (confidence: {result['confidence']})")
    print(f"Match status: {result['match_status']}")
    print(f"Matched URL: {result['matched_url']}")

    print("\n" + "=" * 60)
    print("STEP 3: Metadata & Hashing")
    print("=" * 60)
    print(f"SHA-256 hash: {result['hash']}")

    print("\n" + "=" * 60)
    print("STEP 4: Blockchain Write")
    print("=" * 60)
    print(f"Transaction: {result['explorer_url']}")

    print("\n" + "=" * 60)
    print("STEP 5: Blockchain Verification")
    print("=" * 60)
    print(f"Record #{result['record_id']} — on-chain match: {'PASSED' if result['on_chain_match'] else 'FAILED'}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for k, v in result.items():
        print(f"{k}: {v}")

    return result


def run_pipeline_for_api(image_path: str):
    """
    API entry point: returns the result dict, no printing.
    """
    return _execute_pipeline(image_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_face_image>")
        sys.exit(1)

    run_pipeline(sys.argv[1])