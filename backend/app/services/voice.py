from __future__ import annotations

import asyncio
import io
import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

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

	def parse_goal_commands(self, text: str) -> Dict[str, Any]:
		"""
		Parse natural language goal commands into structured goal data.
		Enhanced goal parsing functionality from VoiceGoalParser.

		Examples:
		- "I want $1 million in 10 years"
		- "Save $50,000 for a house down payment by 2028"
		- "Retire with $2M in 20 years"
		- "I need $100k for college in 5 years"

		Args:
			text: Natural language goal description

		Returns:
			Dict with extracted goal parameters
		"""
		text_lower = text.lower()

		# Goal type patterns
		goal_patterns = {
			'retirement': ['retire', 'retirement'],
			'house': ['house', 'home', 'down payment', 'mortgage'],
			'education': ['college', 'university', 'education', 'tuition'],
			'vacation': ['vacation', 'trip', 'travel'],
			'car': ['car', 'vehicle', 'auto'],
			'emergency': ['emergency fund', 'rainy day'],
		}

		# Extract parameters
		target_amount = self._extract_goal_amount(text_lower)
		years, target_date = self._extract_goal_timeline(text_lower)
		goal_type = self._extract_goal_type(text_lower, goal_patterns)
		monthly_contribution = self._extract_monthly_contribution(text_lower)
		risk_tolerance = self._extract_risk_tolerance(text_lower)

		# Generate goal name
		goal_name = self._generate_goal_name(target_amount, years, goal_type)

		return {
			"name": goal_name,
			"goal_type": goal_type,
			"target_amount": target_amount,
			"target_date": target_date,
			"years_to_goal": years,
			"monthly_contribution": monthly_contribution,
			"risk_tolerance": risk_tolerance,
			"voice_input_text": text,
			"parsed_successfully": target_amount is not None and years is not None
		}

	def _extract_goal_amount(self, text: str) -> Optional[float]:
		"""Extract dollar amount from text"""
		import re
		from datetime import date

		# Pattern 1: $X million/M/k/thousand
		patterns = [
			r'\$?\s*(\d+(?:\.\d+)?)\s*million',
			r'\$?\s*(\d+(?:\.\d+)?)\s*M\b',
			r'\$?\s*(\d+(?:\.\d+)?)\s*k\b',
			r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
		]

		for pattern in patterns:
			match = re.search(pattern, text, re.IGNORECASE)
			if match:
				amount = float(match.group(1).replace(',', ''))

				# Apply multiplier
				if 'million' in text.lower() or ' M' in text or ' m' in text:
					amount *= 1_000_000
				elif ' k' in text.lower():
					amount *= 1_000

				return amount

		return None

	def _extract_goal_timeline(self, text: str) -> Tuple[Optional[int], Optional[str]]:
		"""Extract timeline (years or target date)"""
		import re
		from datetime import date
		from dateutil.relativedelta import relativedelta
		import dateutil.parser as date_parser

		# Pattern 1: "in X years"
		match = re.search(r'in\s+(\d+)\s+years?', text)
		if match:
			years = int(match.group(1))
			target_date = (date.today() + relativedelta(years=years)).isoformat()
			return years, target_date

		# Pattern 2: "by YYYY" or "by Month Year"
		match = re.search(r'by\s+(\d{4})', text)
		if match:
			year = int(match.group(1))
			target_date = date(year, 12, 31).isoformat()
			years = year - date.today().year
			return years, target_date

		return None, None

	def _extract_goal_type(self, text: str, goal_patterns: Dict[str, List[str]]) -> str:
		"""Extract goal type from keywords"""
		for goal_type, keywords in goal_patterns.items():
			if any(keyword in text for keyword in keywords):
				return goal_type

		return 'general'

	def _extract_monthly_contribution(self, text: str) -> Optional[float]:
		"""Extract monthly contribution amount if mentioned"""
		import re

		# Pattern: "save/contribute $X per month/monthly"
		patterns = [
			r'save\s+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s+per\s+month',
			r'contribute\s+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s+monthly',
			r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s+per\s+month',
		]

		for pattern in patterns:
			match = re.search(pattern, text, re.IGNORECASE)
			if match:
				return float(match.group(1).replace(',', ''))

		return None

	def _extract_risk_tolerance(self, text: str) -> str:
		"""Extract risk tolerance from text"""
		text_lower = text.lower()

		if any(word in text_lower for word in ['conservative', 'safe', 'low risk']):
			return 'conservative'
		elif any(word in text_lower for word in ['aggressive', 'high risk', 'growth']):
			return 'aggressive'
		else:
			return 'moderate'

	def _generate_goal_name(self, amount: Optional[float], years: Optional[int], goal_type: str) -> str:
		"""Generate a descriptive goal name"""
		if amount and years:
			amount_str = f"${amount:,.0f}" if amount >= 1000 else f"${amount:.0f}"
			return f"{goal_type.title()} Goal: {amount_str} in {years} years"
		elif amount:
			amount_str = f"${amount:,.0f}" if amount >= 1000 else f"${amount:.0f}"
			return f"{goal_type.title()} Goal: {amount_str}"
		else:
			return f"{goal_type.title()} Goal"


# Voice Command Security Classes (consolidated from voice_security.py)
class CommandType(str, Enum):
	"""Types of voice commands that may require confirmation"""
	BUY = "buy"
	SELL = "sell"
	REBALANCE = "rebalance"
	SET_GOAL = "set_goal"
	CANCEL_ORDER = "cancel_order"


class VoiceCommandTracker:
	"""
	Tracks voice commands per user for rate limiting and confirmation.
	In production, use Redis instead of in-memory dict.
	"""

	def __init__(self):
		# {user_id: {command_id: {timestamp, command_type, amount, symbol, confirmed}}}
		self.pending_commands: Dict[str, Dict[str, dict]] = {}
		# {user_id: [timestamp1, timestamp2, ...]} for rate limiting
		self.command_timestamps: Dict[str, List[float]] = {}
		self.RATE_LIMIT_WINDOW = 60  # seconds
		self.MAX_COMMANDS_PER_WINDOW = 5  # 5 commands per minute
		self.CONFIRMATION_TIMEOUT = 30  # seconds to confirm command

	def check_rate_limit(self, user_id) -> tuple[bool, Optional[str]]:
		"""
		Check if user exceeds rate limit (5 commands per minute).

		Returns:
			(is_allowed: bool, error_message: Optional[str])
		"""
		import time
		user_id_str = str(user_id)
		now = time.time()

		# Initialize tracking for new users
		if user_id_str not in self.command_timestamps:
			self.command_timestamps[user_id_str] = []

		# Remove old timestamps outside the window
		self.command_timestamps[user_id_str] = [
			ts for ts in self.command_timestamps[user_id_str]
			if now - ts < self.RATE_LIMIT_WINDOW
		]

		# Check if limit exceeded
		command_count = len(self.command_timestamps[user_id_str])
		if command_count >= self.MAX_COMMANDS_PER_WINDOW:
			return False, f"Rate limit exceeded: {command_count}/{self.MAX_COMMANDS_PER_WINDOW} commands in last minute"

		# Record this command
		self.command_timestamps[user_id_str].append(now)

		return True, None

	def create_pending_command(
		self,
		user_id,
		command_id: str,
		command_type: CommandType,
		amount: Optional[float] = None,
		symbol: Optional[str] = None,
		metadata: Optional[Dict] = None
	) -> Dict:
		"""
		Create a pending command requiring confirmation.

		Returns:
			Dict with command details and confirmation requirements
		"""
		import time
		from uuid import UUID

		user_id_str = str(user_id)
		now = time.time()

		# Initialize user commands dict
		if user_id_str not in self.pending_commands:
			self.pending_commands[user_id_str] = {}

		# Determine if confirmation is required (high-value trades)
		requires_confirmation = False
		if command_type in [CommandType.BUY, CommandType.SELL] and amount:
			# Require confirmation for trades over $10k
			requires_confirmation = amount > 10000

		confirmation_token = None
		if requires_confirmation:
			import secrets
			confirmation_token = secrets.token_urlsafe(8)

		command = {
			"command_id": command_id,
			"command_type": command_type.value,
			"amount": amount,
			"symbol": symbol,
			"timestamp": now,
			"requires_confirmation": requires_confirmation,
			"confirmation_token": confirmation_token,
			"confirmed": False,
			"metadata": metadata or {}
		}

		self.pending_commands[user_id_str][command_id] = command

		return command

	def confirm_command(self, user_id, command_id: str, confirmation_phrase: str) -> tuple[bool, Optional[str]]:
		"""
		Confirm a pending command.

		Returns:
			(success: bool, error_message: Optional[str])
		"""
		import time

		user_id_str = str(user_id)

		if user_id_str not in self.pending_commands or command_id not in self.pending_commands[user_id_str]:
			return False, "Command not found"

		command = self.pending_commands[user_id_str][command_id]

		# Check timeout
		if time.time() - command["timestamp"] > self.CONFIRMATION_TIMEOUT:
			del self.pending_commands[user_id_str][command_id]
			return False, "Command confirmation timeout"

		# Check confirmation phrase
		valid_phrases = ["yes", "confirm", "execute", "proceed", "approved"]
		if confirmation_phrase.lower() not in valid_phrases:
			return False, f"Invalid confirmation phrase. Use: {', '.join(valid_phrases)}"

		# Mark as confirmed
		command["confirmed"] = True
		command["confirmed_at"] = time.time()

		return True, None

	def reject_command(self, user_id, command_id: str) -> tuple[bool, Optional[str]]:
		"""Reject a pending command"""
		user_id_str = str(user_id)

		if user_id_str not in self.pending_commands or command_id not in self.pending_commands[user_id_str]:
			return False, "Command not found"

		del self.pending_commands[user_id_str][command_id]
		return True, None

	def get_pending_command(self, user_id, command_id: str) -> Optional[Dict]:
		"""Get a specific pending command"""
		user_id_str = str(user_id)
		return self.pending_commands.get(user_id_str, {}).get(command_id)

	def list_pending_commands(self, user_id) -> List[Dict]:
		"""List all pending commands for a user"""
		import time

		user_id_str = str(user_id)
		if user_id_str not in self.pending_commands:
			return []

		# Filter out expired commands
		valid_commands = []
		for cmd_id, cmd in self.pending_commands[user_id_str].items():
			if time.time() - cmd["timestamp"] <= self.CONFIRMATION_TIMEOUT:
				valid_commands.append(cmd)
			else:
				# Remove expired command
				del self.pending_commands[user_id_str][cmd_id]

		return valid_commands

	def cleanup_expired_commands(self):
		"""Clean up expired pending commands"""
		import time

		current_time = time.time()
		for user_id in list(self.pending_commands.keys()):
			for cmd_id in list(self.pending_commands[user_id].keys()):
				cmd = self.pending_commands[user_id][cmd_id]
				if current_time - cmd["timestamp"] > self.CONFIRMATION_TIMEOUT:
					del self.pending_commands[user_id][cmd_id]

			# Remove empty user entries
			if not self.pending_commands[user_id]:
				del self.pending_commands[user_id]


class VoiceCommandValidator:
	"""Validates voice commands against business rules"""

	@staticmethod
	def validate_order(symbol: str, quantity: float, account_balance: float) -> tuple[bool, Optional[str]]:
		"""
		Validate trading order parameters.

		Returns:
			(is_valid: bool, error_message: Optional[str])
		"""
		# Validate symbol format
		if not symbol or len(symbol) > 5 or not symbol.isalpha():
			return False, "Invalid stock symbol format"

		# Validate quantity
		if quantity <= 0 or quantity > 10000:
			return False, "Quantity must be between 1 and 10,000 shares"

		# Check if fractional shares are whole numbers (for simplicity)
		if quantity != int(quantity):
			return False, "Fractional shares not supported"

		# Estimate order value (rough calculation)
		estimated_value = quantity * 100  # Rough estimate
		if estimated_value > account_balance * 0.9:  # Max 90% of balance
			return False, f"Order value (${estimated_value:,.0f}) exceeds 90% of account balance"

		return True, None


class VoiceCommandLogger:
	"""Logs voice command activities for security and auditing"""

	@staticmethod
	def log_command(user_id, command_type: str, status: str, details: Optional[Dict] = None, error: Optional[str] = None):
		"""Log a voice command event"""
		import logging
		logger = logging.getLogger(__name__)

		log_data = {
			"user_id": str(user_id),
			"command_type": command_type,
			"status": status,
			"timestamp": datetime.now().isoformat()
		}

		if details:
			log_data.update(details)

		if error:
			log_data["error"] = error

		if status == "error":
			logger.warning(f"Voice command failed: {log_data}")
		else:
			logger.info(f"Voice command {status}: {log_data}")


# Global instances
voice_command_tracker = VoiceCommandTracker()


