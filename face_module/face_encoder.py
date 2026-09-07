from deepface import DeepFace


def get_face_encoding(image_path: str, model_name: str = "Facenet", detector_backend: str = "mtcnn"):
    """
    Detects a face in the given image and returns its embedding vector.

    Args:
        image_path: path to the image file containing a face.
        model_name: which face recognition model DeepFace should use.
        detector_backend: which face detector DeepFace should use to locate the face.

    Returns:
        A list of floats representing the face embedding.
    """
    result = DeepFace.represent(img_path=image_path, model_name=model_name, detector_backend=detector_backend)
    embedding = result[0]["embedding"]
    return embedding


def verify_faces(img1_path: str, img2_path: str, model_name: str = "Facenet", detector_backend: str = "mtcnn"):
    """
    Compares two face images and determines whether they show the same person.

    Args:
        img1_path: path to the first image.
        img2_path: path to the second image.
        model_name: which face recognition model DeepFace should use.
        detector_backend: which face detector DeepFace should use.

    Returns:
        A tuple of (verified: bool, distance: float). Lower distance means
        more similar; verified is DeepFace's own threshold-based judgment.
    """
    result = DeepFace.verify(
        img1_path=img1_path,
        img2_path=img2_path,
        model_name=model_name,
        detector_backend=detector_backend,
        enforce_detection=False,
    )
    return result["verified"], result["distance"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python face_encoder.py <image_path>")
        sys.exit(1)
    encoding = get_face_encoding(sys.argv[1])
    print(f"Encoding length: {len(encoding)}")
    print(f"First 5 values: {encoding[:5]}")