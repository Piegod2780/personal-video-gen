"""
Streamlit application for generating videos using the open‑source LongCat‑Video model
via the fal.ai model API.  Users can choose between text‑to‑video and image‑to‑video
generation modes, adjust basic parameters, and view/download the resulting video.
"""

import os
import tempfile
from typing import Optional

import streamlit as st

try:
    # fal_client is only available after installing requirements
    from fal_client import FalClient  # type: ignore
except ImportError:
    FalClient = None  # type: ignore


def get_client() -> Optional[FalClient]:
    """Initialize a FalClient with the FAL_KEY from the environment.

    Returns
    -------
    FalClient or None
        A client instance if credentials are found, otherwise None.
    """
    api_key = os.getenv("FAL_KEY")
    if not api_key:
        return None
    try:
        return FalClient(api_key)  # type: ignore
    except Exception:
        # If instantiation fails, return None so the caller can handle it
        return None


def upload_image(client: FalClient, image_bytes: bytes) -> str:
    """Upload an image to fal.media and return the hosted URL.

    Parameters
    ----------
    client : FalClient
        An initialized fal client.
    image_bytes : bytes
        Raw bytes of the image file.

    Returns
    -------
    str
        URL of the uploaded image.
    """
    # Write to a temporary file because fal_client.upload_file expects a file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(image_bytes)
        tmp.flush()
        # upload_file will return a URL that can be passed back into other requests
        image_url: str = client.upload_file(tmp.name)  # type: ignore
    return image_url


def generate_text_to_video(
    client: FalClient,
    prompt: str,
    num_frames: int,
    guidance_scale: float,
    num_inference_steps: int,
    negative_prompt: Optional[str] = None,
) -> str:
    """Generate a video from text using the LongCat‑Video model on fal.ai.

    Parameters
    ----------
    client : FalClient
        An initialized fal client.
    prompt : str
        The text description of the desired video.
    num_frames : int
        Total number of frames to generate.  At 30 fps, frames/30 = seconds.
    guidance_scale : float
        CFG guidance scale value.
    num_inference_steps : int
        Number of inference steps per frame.
    negative_prompt : Optional[str], optional
        A negative prompt to discourage undesired elements.

    Returns
    -------
    str
        URL of the generated video.
    """
    # Build the arguments dictionary.  Additional parameters can be added here.
    arguments: dict = {
        "prompt": prompt,
        "num_frames": num_frames,
        "guidance_scale": guidance_scale,
        "num_inference_steps": num_inference_steps,
    }
    # Only include negative_prompt if the user provided one
    if negative_prompt:
        arguments["negative_prompt"] = negative_prompt
    # 30 fps output
    arguments["fps"] = 30
    # Use fal.ai endpoint for text‑to‑video generation at 720p
    result = client.subscribe("fal-ai/longcat-video/text-to-video/720p", arguments)  # type: ignore
    # The response includes a nested structure with the video URL
    # According to fal examples, the result has a "video" field
    video = result.get("video")
    if isinstance(video, dict) and "url" in video:
        return video["url"]
    # Fallback: the API might return data under "data"
    data = result.get("data")
    if isinstance(data, dict):
        video_field = data.get("video")
        if isinstance(video_field, dict) and "url" in video_field:
            return video_field["url"]
    raise RuntimeError("Unexpected response format from fal API: missing video URL")


def generate_image_to_video(
    client: FalClient,
    image_url: str,
    prompt: str,
    num_frames: int,
    guidance_scale: float,
    num_inference_steps: int,
    negative_prompt: Optional[str] = None,
) -> str:
    """Generate a video from an image and text prompt using LongCat‑Video on fal.ai.

    Parameters
    ----------
    client : FalClient
        An initialized fal client.
    image_url : str
        URL of the image uploaded to fal.media.
    prompt : str
        Description guiding the animation.
    num_frames : int
        Number of frames to generate.  At 30 fps, frames/30 = seconds.
    guidance_scale : float
        CFG guidance scale.
    num_inference_steps : int
        Number of inference steps.
    negative_prompt : Optional[str], optional
        Negative prompt.

    Returns
    -------
    str
        URL of the generated video.
    """
    arguments: dict = {
        "image_url": image_url,
        "prompt": prompt,
        "num_frames": num_frames,
        "guidance_scale": guidance_scale,
        "num_inference_steps": num_inference_steps,
    }
    if negative_prompt:
        arguments["negative_prompt"] = negative_prompt
    arguments["fps"] = 30
    result = client.subscribe("fal-ai/longcat-video/image-to-video/720p", arguments)  # type: ignore
    video = result.get("video")
    if isinstance(video, dict) and "url" in video:
        return video["url"]
    data = result.get("data")
    if isinstance(data, dict):
        video_field = data.get("video")
        if isinstance(video_field, dict) and "url" in video_field:
            return video_field["url"]
    raise RuntimeError("Unexpected response format from fal API: missing video URL")


def main() -> None:
    """Main function to define the Streamlit UI and handle events."""
    st.set_page_config(page_title="LongCat Video Generator", layout="wide")
    st.title("Personal LongCat Video Generator")
    st.markdown(
        "Generate long AI videos using the open‑source LongCat‑Video model via the "
        "[fal.ai](https://fal.ai/models/fal-ai/longcat-video) API.  Select a generation "
        "mode, describe your scene, adjust the parameters and click **Generate Video**."
    )

    # Check that fal_client is available
    if FalClient is None:
        st.error(
            "The fal-client library is not installed.  Please run `pip install -r requirements.txt` "
            "before launching this app."
        )
        return

    # Initialize client
    client = get_client()
    if client is None:
        st.error(
            "Fal API key not found.  Set the `FAL_KEY` environment variable in your deployment "
            "environment.  You can obtain a key by signing up at fal.ai."
        )
        return

    # Mode selection
    mode = st.selectbox("Select generation mode", ["Text-to-Video", "Image-to-Video"])

    prompt = st.text_area(
        "Prompt",
        placeholder="Describe your video: scene, motion, camera angles, style...",
        height=150,
    )
    negative_prompt = st.text_input(
        "Negative prompt (optional)",
        placeholder="Elements to avoid, e.g. blurry, static, poor quality...",
    )

    # Duration slider (seconds)
    st.subheader("Generation parameters")
    duration_seconds = st.slider(
        "Video length (seconds)",
        min_value=3,
        max_value=20,
        value=6,
        help="Longer videos cost more credits and may be less consistent."
    )
    fps = 30
    num_frames = int(duration_seconds * fps)
    guidance_scale = st.slider(
        "Guidance scale", min_value=1.0, max_value=10.0, value=4.0, step=0.5,
        help="Higher values follow the prompt more closely but may reduce diversity."
    )
    num_inference_steps = st.slider(
        "Number of inference steps", min_value=8, max_value=50, value=40,
        help="Higher steps improve quality but increase generation time."
    )

    image_file = None
    if mode == "Image-to-Video":
        image_file = st.file_uploader(
            "Upload an image (jpg/png/webp/gif)",
            type=["jpg", "jpeg", "png", "webp", "gif", "avif"],
        )

    generate_button = st.button("Generate Video", disabled=False)

    if generate_button:
        # Validate input
        if not prompt:
            st.warning("Please enter a prompt to guide the video generation.")
            return
        try:
            if mode == "Text-to-Video":
                with st.spinner("Generating video from text... this may take a few minutes"):
                    video_url = generate_text_to_video(
                        client,
                        prompt,
                        num_frames,
                        guidance_scale,
                        num_inference_steps,
                        negative_prompt if negative_prompt else None,
                    )
            else:
                if image_file is None:
                    st.warning("Please upload an image to animate.")
                    return
                # Read bytes from the uploaded file
                image_bytes = image_file.read()
                with st.spinner("Uploading image..."):
                    image_url = upload_image(client, image_bytes)
                with st.spinner("Generating video from image... this may take a few minutes"):
                    video_url = generate_image_to_video(
                        client,
                        image_url,
                        prompt,
                        num_frames,
                        guidance_scale,
                        num_inference_steps,
                        negative_prompt if negative_prompt else None,
                    )
            # Display the video
            st.success("Video generated successfully!")
            st.video(video_url)
            st.markdown(f"[Download video]({video_url})")
        except Exception as e:
            st.error(f"Generation failed: {e}")


if __name__ == "__main__":
    main()
