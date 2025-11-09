from __future__ import annotations

import asyncio
import io
import logging
import re
from typing import Optional, Dict, Any, List, Tuple

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

try:
	import librosa  # type: ignore
	_LIBROSA_AVAILABLE = True
except Exception:
	_LIBROSA_AVAILABLE = False

try:
	import soundfile  # type: ignore
	_SOUNDFILE_AVAILABLE = True
except Exception:
	_SOUNDFILE_AVAILABLE = False


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

	def detect_voice_activity(self, audio_bytes: bytes, threshold: float = 0.02) -> Dict[str, Any]:
		"""
		Voice Activity Detection (VAD): Detect if audio contains speech.
		Uses energy-based detection for fast processing.
		
		Args:
			audio_bytes: Audio data in WAV format
			threshold: Energy threshold for speech detection
		
		Returns:
			{"has_speech": bool, "confidence": float, "voice_segments": List}
		"""
		try:
			if not _LIBROSA_AVAILABLE:
				return {"has_speech": True, "confidence": 0.5, "voice_segments": [], "provider": "mock"}
			
			import numpy as np
			
			# Load audio
			y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
			
			# Calculate energy
			energy = np.sqrt(np.mean(y ** 2, axis=0) if y.ndim > 1 else y ** 2)
			
			# Frame-based analysis
			frame_length = sr // 10  # 100ms frames
			if len(y) < frame_length:
				return {"has_speech": energy > threshold, "confidence": float(energy), "voice_segments": []}
			
			# Detect voiced frames
			voiced_frames = []
			start_frame = None
			segments = []
			
			for i in range(0, len(y), frame_length):
				frame = y[i:i + frame_length]
				frame_energy = np.sqrt(np.mean(frame ** 2))
				
				if frame_energy > threshold:
					if start_frame is None:
						start_frame = i / sr
					voiced_frames.append(True)
				else:
					if start_frame is not None:
						segments.append({"start": start_frame, "end": i / sr})
						start_frame = None
					voiced_frames.append(False)
			
			if start_frame is not None:
				segments.append({"start": start_frame, "end": len(y) / sr})
			
			has_speech = len(segments) > 0
			confidence = float(np.mean(voiced_frames)) if voiced_frames else 0.0
			
			return {
				"has_speech": has_speech,
				"confidence": confidence,
				"voice_segments": segments,
				"provider": "librosa-energy"
			}
		except Exception as e:
			self.logger.error(f"VAD error: {e}", exc_info=True)
			return {"has_speech": True, "confidence": 0.5, "voice_segments": [], "provider": "mock"}

	async def reduce_noise(self, audio_bytes: bytes) -> bytes:
		"""
		Reduce background noise from audio.
		Uses spectral subtraction if librosa available, otherwise returns original.
		
		Args:
			audio_bytes: Audio data in WAV format
		
		Returns:
			Denoised audio bytes
		"""
		try:
			if not _LIBROSA_AVAILABLE or not _SOUNDFILE_AVAILABLE:
				return audio_bytes
			
			import numpy as np
			import librosa  # type: ignore
			import soundfile  # type: ignore
			
			# Load audio
			y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
			
			# Compute STFT
			D = librosa.stft(y)
			magnitude = np.abs(D)
			phase = np.angle(D)
			
			# Estimate noise from silent frames
			noise_duration = int(sr * 0.5)  # First 500ms assumed noise
			noise_profile = np.median(magnitude[:, :noise_duration], axis=1, keepdims=True)
			
			# Spectral subtraction
			alpha = 2.0
			denoised_magnitude = magnitude - alpha * noise_profile
			denoised_magnitude = np.maximum(denoised_magnitude, 0.1 * magnitude)  # Floor
			
			# Reconstruct
			D_denoised = denoised_magnitude * np.exp(1j * phase)
			y_denoised = librosa.istft(D_denoised)
			
			# Convert back to WAV bytes
			output = io.BytesIO()
			soundfile.write(output, y_denoised, sr, format='WAV')
			output.seek(0)
			return output.read()
		except Exception as e:
			self.logger.warning(f"Noise reduction failed: {e}, returning original audio")
			return audio_bytes

	def parse_voice_commands(self, text: str) -> Dict[str, Any]:
		"""
		Parse voice input for recognized commands.
		Returns structured command data for executor agent.
		
		Args:
			text: Transcribed voice text
		
		Returns:
			{"command_type": str, "action": str, "params": dict, "raw_text": str, "confidence": float}
		"""
		text_lower = text.lower().strip()
		
		# Trading commands
		trading_patterns = {
			r"buy\s+(\d+)\s+shares?(?:\s+of)?\s+([a-z]+)": ("buy", "symbol"),
			r"sell\s+(\d+)\s+shares?(?:\s+of)?\s+([a-z]+)": ("sell", "symbol"),
			r"buy\s+([a-z]+)": ("buy_market", "symbol"),
			r"sell\s+([a-z]+)": ("sell_market", "symbol"),
		}
		
		for pattern, (action, param_type) in trading_patterns.items():
			match = re.search(pattern, text_lower)
			if match:
				params = {}
				if param_type == "symbol":
					if action in ["buy", "sell"]:
						params["quantity"] = int(match.group(1))
						params["symbol"] = match.group(2).upper()
					else:
						params["symbol"] = match.group(1).upper()
				return {
					"command_type": "trading",
					"action": action,
					"params": params,
					"raw_text": text,
					"confidence": 0.9
				}
		
		# Goal commands
		goal_patterns = {
			r"i want\s+\$?([\d,]+)\s+(?:in|by)\s+(\d+)\s+years?": "goal_create",
			r"set\s+goal.*\$?([\d,]+)": "goal_update",
			r"what's?\s+my\s+goal(?:s)?": "goal_list",
		}
		
		for pattern, action in goal_patterns.items():
			if re.search(pattern, text_lower):
				return {
					"command_type": "goal",
					"action": action,
					"params": {"raw_input": text},
					"raw_text": text,
					"confidence": 0.85
				}
		
		# Portfolio commands
		portfolio_patterns = {
			r"what's?\s+my\s+portfolio": "portfolio_view",
			r"show\s+my\s+holdings?": "portfolio_view",
			r"portfolio\s+summary": "portfolio_summary",
		}
		
		for pattern, action in portfolio_patterns.items():
			if re.search(pattern, text_lower):
				return {
					"command_type": "portfolio",
					"action": action,
					"params": {},
					"raw_text": text,
					"confidence": 0.9
				}
		
		# Default: informational/question
		return {
			"command_type": "information",
			"action": "query",
			"params": {"query": text},
			"raw_text": text,
			"confidence": 0.5
		}


