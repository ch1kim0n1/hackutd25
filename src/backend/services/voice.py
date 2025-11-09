from __future__ import annotations

import asyncio
import io
import logging
from typing import Optional, Dict, Any

try:
	from faster_whisper import WhisperModel  # type: ignore
	_WHISPER_AVAILABLE = True
except Exception:
	_WHISPER_AVAILABLE = False

try:
	import edge_tts  # type: ignore
	_EDGE_TTS_AVAILABLE = True
except Exception:
	_EDGE_TTS_AVAILABLE = False


class VoiceService:
	"""
	Voice interface service supporting STT (speech-to-text) and TTS (text-to-speech).
	Provider selection is automatic based on available libraries, with a mock fallback.
	"""

	def __init__(self, stt_model_size: str = "base", stt_compute_type: str = "int8", tts_voice: str = "en-US-JennyNeural"):
		self.logger = logging.getLogger(__name__)
		self.stt_model: Optional[WhisperModel] = None
		self.tts_default_voice = tts_voice

		if _WHISPER_AVAILABLE:
			try:
				self.stt_model = WhisperModel(stt_model_size, compute_type=stt_compute_type)
				self.logger.info("VoiceService: faster-whisper model loaded")
			except Exception as e:
				self.logger.warning(f"VoiceService: failed to load faster-whisper model: {e}")
				self.stt_model = None

	async def transcribe_bytes(self, audio_bytes: bytes, language: Optional[str] = None) -> Dict[str, Any]:
		"""
		STT: Transcribe an audio buffer to text.
		Returns: {"text": str, "segments": [...], "provider": str}
		"""
		if self.stt_model:
			try:
				# faster-whisper accepts file paths or numpy arrays; for bytes, write temp buffer
				# To avoid disk IO, use BytesIO and numpy with soundfile if available.
				# Minimal approach: write to temp file asynchronously.
				import tempfile
				import os
				loop = asyncio.get_event_loop()
				def _write_temp() -> str:
					fd, path = tempfile.mkstemp(suffix=".wav")
					with os.fdopen(fd, "wb") as f:
						f.write(audio_bytes)
					return path
				tmp_path = await loop.run_in_executor(None, _write_temp)
				try:
					segments, info = self.stt_model.transcribe(tmp_path, language=language)
					text_parts = []
					segment_dicts = []
					for seg in segments:
						text_parts.append(seg.text)
						segment_dicts.append({
							"start": seg.start,
							"end": seg.end,
							"text": seg.text,
						})
					return {
						"text": " ".join(t.strip() for t in text_parts if t.strip()),
						"segments": segment_dicts,
						"provider": "faster-whisper"
					}
				finally:
					try:
						import os
						os.remove(tmp_path)
					except Exception:
						pass
			except Exception as e:
				self.logger.error(f"VoiceService STT error: {e}", exc_info=True)

		# Mock fallback
		return {
			"text": "[transcription unavailable: STT provider not configured]",
			"segments": [],
			"provider": "mock"
		}

	async def synthesize_speech(self, text: str, voice: Optional[str] = None) -> Dict[str, Any]:
		"""
		TTS: Synthesize speech for the given text.
		Returns: {"audio_bytes": bytes, "mime_type": "audio/mpeg", "provider": str}
		"""
		use_voice = voice or self.tts_default_voice
		if _EDGE_TTS_AVAILABLE:
			try:
				mp3_buffer = io.BytesIO()
				communicate = edge_tts.Communicate(text=text, voice=use_voice)
				async for chunk in communicate.stream():
					if chunk["type"] == "audio":
						mp3_buffer.write(chunk["data"])
				return {
					"audio_bytes": mp3_buffer.getvalue(),
					"mime_type": "audio/mpeg",
					"provider": "edge-tts"
				}
			except Exception as e:
				self.logger.error(f"VoiceService TTS error: {e}", exc_info=True)

		# Mock fallback: generate empty audio with a message note
		self.logger.warning("VoiceService: TTS provider not available, returning empty audio")
		return {
			"audio_bytes": b"",
			"mime_type": "audio/mpeg",
			"provider": "mock"
		}


