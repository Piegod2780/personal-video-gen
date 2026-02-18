# Personal LongCat Video Generator

This repository contains a simple Streamlit application that wraps the open‑source **LongCat‑Video** model via the `fal.ai` model API.  The goal of the app is to make it easy for a user to generate long, coherent videos from either a text prompt or a source image without needing to run the heavyweight model on their own hardware.

## Features

* **Text‑to‑Video** – type a descriptive prompt and have a video generated at 720p/30 fps.
* **Image‑to‑Video** – upload a still image and describe how it should move; the app animates your scene.
* Adjustable duration, guidance scale and inference steps.
* Displays the generated video in the browser and provides a download link.

## Prerequisites

This application relies on the [fal.ai](https://fal.ai/) model API, which hosts LongCat‑Video on GPUs.  You will need a **Fal API key** in order to make requests.  Keys can be obtained for free on the Fal dashboard.

Before running locally or deploying, set an environment variable named `FAL_KEY` to your API key.  The `fal‑client` library will automatically read this variable.

## Running locally

1. Create a Python virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Export your API key:

   ```bash
   export FAL_KEY=your‑fal‑api‑key
   ```

4. Run the application with Streamlit:

   ```bash
   streamlit run app.py
   ```

5. Open the provided URL in your browser.  Upload an image or just type a prompt, adjust the sliders and click **Generate Video**.

## Deploying on Render

Render.com makes it easy to host Python and Streamlit applications from a Git repository.  This repository includes a `render.yaml` file that defines a web service with the proper build and start commands.

1. Push this repository to your own GitHub account.
2. Log in to [Render](https://render.com/) and click **New Web Service**.
3. Connect your GitHub account and select the repository you just pushed.
4. Accept the default Python environment.  Under **Start Command** Render will automatically use the command specified in the `render.yaml` file.
5. Add an environment variable named `FAL_KEY` containing your Fal API key in the service settings.
6. Click **Create Web Service**.  Render will build the container, install dependencies and serve your Streamlit app.  Once the build finishes you will get a public URL.

Note: The Fal API charges per generated second of video (see their pricing for details).  Running LongCat‑Video on your own hardware requires a high‑end GPU; using Fal offloads this heavy compute to their infrastructure.  If you prefer to run the model locally, you can follow the instructions in the original [LongCat‑Video](https://github.com/meituan-longcat/LongCat-Video) repository.
