import os
import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_EY"))

def generate_video(prompt: str, duration: int = 6):
    """
    Generate a video using OpenAI Sora.
    """
    response = client.videos.generate(
        model="sora-1",
        prompt=prompt,
        duration=duration,  # seconds
        resolution="720p"
    )

    video_url = response.data[0].url  # Extract video URL from response
    return video_url


def main():
    st.set_page_config(page_title="Sora Video Generator", layout="wide")
    st.title("Personal Sora Video Generator")

    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is not set in environment variables.")
        return

    prompt = st.text_area("Enter your video prompt", height=150)
    duration = st.slider("Video length (seconds)", 3, 20, 6)

    if st.button("Generate Video"):
        if not prompt.strip():
            st.warning("Enter a prompt.")
            return

        try:
            with st.spinner("Generating video with Sora..."):
                video_url = generate_video(prompt, duration)
            st.success("Video generated.")
            st.video(video_url)
            st.markdown(f"[Download video]({video_url})")
        except Exception as e:
            st.error(f"Generation failed: {e}")


if __name__ == "__main__":
    main()
