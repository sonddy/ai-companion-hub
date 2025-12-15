# Project Riko

Project Riko is a anime focused LLM project by Just Rayen. She listens, and remembers your conversations. It combines OpenAI’s GPT, GPT-SoVITS voice synthesis, and Faster-Whisper ASR into a fully configurable conversational pipeline.

**tested with python 3.10 Windows >10 and Linux Ubuntu**
## ✨ Features

- 💬 **LLM-based dialogue** using OpenAI API (configurable system prompts)
- 🧠 **Conversation memory** to keep context during interactions
- 🔊 **Voice generation** via GPT-SoVITS API
- 🎧 **Speech recognition** using Faster-Whisper
- 📁 Clean YAML-based config for personality configuration


## ⚙️ Configuration

All prompts and parameters are stored in `config.yaml`.

```yaml
OPENAI_API_KEY: sk-YOURAPIKEY
history_file: chat_history.json
model: "gpt-4.1-mini"
presets:
  default:
    system_prompt: |
      You are a helpful assistant named Riko.
      You speak like a snarky anime girl.
      Always refer to the user as "senpai".

sovits_ping_config:
  text_lang: en
  prompt_lang : en
  ref_audio_path : D:\PyProjects\waifu_project\riko_project\character_files\main_sample.wav
  prompt_text : This is a sample voice for you to just get started with because it sounds kind of cute but just make sure this doesn't have long silences.
  
````

You can define personalities by modiying the config file.


## 🛠️ Setup

### Install Dependencies

```bash
pip install uv 
uv pip install -r extra-req.txt
uv pip install -r requirements.txt
```

**If you want to use GPU support for Faster whisper** Make sure you also have:

* CUDA & cuDNN installed correctly (for Faster-Whisper GPU support)
* `ffmpeg` installed (for audio processing)


## 🧪 Usage

### 1. Launch the GPT-SoVITS API 

### 2. Run the main script:


```bash
python main_chat.py
```

The flow:

1. Riko listens to your voice via microphone (push to talk)
2. Transcribes it with Faster-Whisper
3. Passes it to GPT (with history)
4. Generates a response
5. Synthesizes Riko's voice using GPT-SoVITS
6. Plays the output back to you

### 3. Try the web dashboard (UI)

Launch a Gradio page that exposes the LLM, text-to-speech, and speech-to-text pieces:

```bash
python server/web_ui.py
```

Then open http://127.0.0.1:7860 to chat, synthesize voice, or transcribe audio from your browser. Run this from the project root so `character_config.yaml` is picked up correctly.

### 4. Browser TTS (bypass CORS) via proxy

If you open `character_files/index.html` in a browser and get fetch/CORS errors, run the local FastAPI proxy and point the page to it (default is already set to this):

```bash
uvicorn server.tts_proxy:app --port 8001
```

The proxy forwards to your GPT-SoVITS server (defaults to `http://127.0.0.1:9880/tts`). Adjust `TARGET_TTS_URL` env var if your TTS host/port differs.

If you only need a test tone (no GPT-SoVITS available), start the mock TTS:

```bash
uvicorn server.mock_tts:app --port 8002
```

Then point the page endpoint to `http://127.0.0.1:8002/tts` for a quick sanity check.

### 4b. Nicky mini web client (Cursor/PowerShell friendly)

Clean, standalone HTML lives at `nicky/index.html`. Run everything from the project root:

1. (Optional) Start the mock tone server if GPT-SoVITS is not up:
   ```powershell
   uvicorn server.mock_tts:app --port 8002
   ```
2. Start the browser-friendly proxy (so CORS is open):
   ```powershell
   uvicorn server.tts_proxy:app --port 8001
   ```
3. Serve the static files (needed to avoid mixed-content blocking):
   ```powershell
   python -m http.server 8080
   ```
4. Open `http://127.0.0.1:8080/nicky/index.html` (works in Cursor preview or any browser).
5. In the page, set the endpoint to:
   - Proxy: `http://127.0.0.1:8001/tts` (default)
   - Mock: `http://127.0.0.1:8002/tts` (quick tone test)

PowerShell health check examples:
```powershell
Invoke-WebRequest http://127.0.0.1:8001/health
Invoke-WebRequest http://127.0.0.1:8002/health
```

### 5. Convenience launcher for GPT-SoVITS + proxy

Assuming you cloned GPT-SoVITS next to this project (e.g., `../GPT-SoVITS`) and installed its deps/models, you can start both the upstream API and the local proxy together:

```bash
python scripts/run_tts_stack.py
```

Defaults:
- GPT-SoVITS TTS: http://127.0.0.1:9880/tts
- Proxy: http://127.0.0.1:8001/tts (used by the browser page)

Use `GPT_SOVITS_PATH` env var if your clone lives elsewhere.


## 📌 TODO / Future Improvements

* [ ] GUI or web interface
* [ ] Live microphone input support
* [ ] Emotion or tone control in speech synthesis
* [ ] VRM model frontend


## 🧑‍🎤 Credits

* Voice synthesis powered by [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
* ASR via [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)
* Language model via [OpenAI GPT](https://platform.openai.com)


## 📜 License

MIT — feel free to clone, modify, and build your own waifu voice companion.


