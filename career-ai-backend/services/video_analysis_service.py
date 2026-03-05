import os
import requests

FACE_ENDPOINT = os.environ.get("FACE_ENDPOINT")
FACE_KEY = os.environ.get("FACE_KEY")


def analyze_face(image_bytes):

    url = f"{FACE_ENDPOINT}/face/v1.0/detect"

    params = {
        "returnFaceAttributes": "headPose"
    }

    headers = {
        "Ocp-Apim-Subscription-Key": FACE_KEY,
        "Content-Type": "application/octet-stream"
    }

    response = requests.post(
        url,
        params=params,
        headers=headers,
        data=image_bytes
    )

    try:
        faces = response.json()
    except ValueError:
        return {"confidence_score": 0, "eye_contact": False, "emotion": "api_error"}

    # If the API returned an error (dict with "error" key)
    if isinstance(faces, dict) and "error" in faces:
        print(f"Face API Error: {faces['error']}")
        return {"confidence_score": 0, "eye_contact": False, "emotion": "api_error"}

    # Ensure it's a list and has at least one face
    if not isinstance(faces, list) or len(faces) == 0:
        print(f"[DEBUG] Face API returned no faces or invalid list format. Response: {faces}, Status: {response.status_code}")
        return {
            "confidence_score": 0,
            "eye_contact": False,
            "emotion": "no_face"
        }

    face = faces[0]

    head_pose = face["faceAttributes"]["headPose"]

    # Azure retired the "emotion" attribute. We'll use a static "neutral" 
    # and base the confidence solely on the user making good eye contact (yaw and pitch close to 0).
    yaw, pitch = abs(head_pose["yaw"]), abs(head_pose["pitch"])
    
    # Good eye contact means looking straight at the camera (low yaw/pitch)
    eye_contact = yaw < 15 and pitch < 15
    
    # Simple confidence heuristic based on head pose
    if eye_contact:
        confidence_score = 95.0 - (yaw + pitch)
    else:
        confidence_score = max(50.0, 95.0 - (yaw * 1.5 + pitch * 1.5))

    return {
        "confidence_score": round(confidence_score, 2),
        "eye_contact": eye_contact,
        "emotion": "focused"
    }