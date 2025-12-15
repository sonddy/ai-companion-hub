"""
Gradio dashboard exposing the main Riko pipeline pieces (LLM chat, TTS, ASR).
Run from the project root so config paths resolve correctly.
"""
import os
import uuid
from pathlib import Path

import gradio as gr
import yaml
from faster_whisper import WhisperModel

from process.llm_funcs.llm_scr import llm_response
from process.tts_func.sovits_ping import sovits_gen


ROOT_DIR = Path(__file__).resolve().parent.parent
os.chdir(ROOT_DIR)

CONFIG_PATH = ROOT_DIR / "character_config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    char_config = yaml.safe_load(f)

# Heavy models are loaded once at startup for responsiveness in the UI callbacks.
whisper_model = WhisperModel("base.en", device="cpu", compute_type="float32")
audio_dir = ROOT_DIR / "audio"
audio_dir.mkdir(exist_ok=True)


def summarize_config():
    preset = char_config["presets"]["default"]
    sovits = char_config["sovits_ping_config"]
    return (
        f"**Model:** {char_config['model']}\n\n"
        f"**History file:** {char_config['history_file']}\n\n"
        f"**System prompt (preview):**\n```\n{preset['system_prompt'].strip()}\n```\n\n"
        f"**TTS voice sample:** {sovits['ref_audio_path']}"
    )


def run_llm_chat(user_text: str):
    if not user_text or not user_text.strip():
        return "Enter a message first."
    try:
        return llm_response(user_text.strip())
    except Exception as exc:
        return f"LLM call failed: {exc}"


def transcribe_audio(audio_path: str):
    if not audio_path:
        return "Record or upload audio first."
    segments, _ = whisper_model.transcribe(audio_path)
    transcript = " ".join([seg.text for seg in segments]).strip()
    return transcript or "No speech detected."


def generate_tts(text: str):
    if not text or not text.strip():
        return None, "Enter text to synthesize."

    outfile = audio_dir / f"web_{uuid.uuid4().hex}.wav"
    path = sovits_gen(text.strip(), outfile)
    if not path:
        return None, "TTS failed; confirm the GPT-SoVITS API is running."

    return str(path), f"Saved to {outfile.name}"


with gr.Blocks(title="Riko Functionality Dashboard") as demo:
    gr.Markdown(
        "# Riko Functionality Dashboard\n"
        "Use this page to exercise the LLM, speech-to-text, and text-to-speech pieces."
    )

    gr.Markdown(summarize_config())

    with gr.Tab("LLM Chat"):
        gr.Markdown("Send text to the LLM (history is preserved on disk).")
        chat_in = gr.Textbox(lines=3, label="Message", placeholder="Talk to Riko…")
        chat_btn = gr.Button("Generate reply")
        chat_out = gr.Textbox(lines=6, label="Response", interactive=False)
        chat_btn.click(run_llm_chat, inputs=chat_in, outputs=chat_out)

    with gr.Tab("Text → Speech"):
        gr.Markdown("Send text to GPT-SoVITS and listen to the synthesized voice.")
        tts_in = gr.Textbox(lines=3, label="Text to read")
        tts_btn = gr.Button("Synthesize")
        tts_audio = gr.Audio(label="Synthesized audio", autoplay=True)
        tts_status = gr.Markdown()
        tts_btn.click(generate_tts, inputs=tts_in, outputs=[tts_audio, tts_status])

    with gr.Tab("Speech → Text"):
        gr.Markdown("Record or upload audio to see the Faster-Whisper transcription.")
        asr_in = gr.Audio(
            sources=["microphone", "upload"],
            type="filepath",
            label="Speak or upload audio",
        )
        asr_btn = gr.Button("Transcribe")
        asr_out = gr.Textbox(lines=4, label="Transcription", interactive=False)
        asr_btn.click(transcribe_audio, inputs=asr_in, outputs=asr_out)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        show_api=False,
    )







