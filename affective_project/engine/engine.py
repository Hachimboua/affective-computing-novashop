"""Public engine entry point; perception and later phases are composed here."""
import os
import time

from . import config
from .affect.fusion import fuse_text_voice
from .policy.policy import choose_action
from .policy.replies import render_reply
from .perception.text_estimator import estimate_text
from .state.tracker import StateTracker
from .voice.features import AudioInputError, numpy_available
from .voice.voice_estimator import estimate_voice


def _internal_error_response(error):
    """Return a contract-valid clarification while exposing the error type."""
    return {
        "valence": 0.0,
        "activity": 0.0,
        "dominance": 0.0,
        "confidence": 0.05,
        "label": "neutral",
        "action": "ASK_CLARIFICATION",
        "reply": (
            "I could not process that message. Please try rephrasing it or "
            "share a little more detail. / Não consegui processar a mensagem. "
            "Tente formulá-la de outra forma ou partilhe mais detalhes."
        ),
        "flags": ["internal_error"],
        "details": {
            "error_type": type(error).__name__,
            "engine_version": "1.0",
        },
    }


class Engine:
    def __init__(self):
        self.reset()

    def reset(self):
        """Start a conversation with no retained message history."""
        self.state_tracker = StateTracker()

    def process(self, text, audio_path=None, image_path=None):
        """Return a valid result on errors, unless strict testing is enabled."""
        try:
            return self._process(text, audio_path, image_path)
        except Exception as error:
            if os.environ.get("ENGINE_STRICT") == "1":
                raise
            self.reset()
            return _internal_error_response(error)

    def _process(self, text, audio_path=None, image_path=None):
        """Estimate affect, update state, apply policy, and render a reply."""
        pipeline_started = time.perf_counter()
        stage_started = pipeline_started
        estimate = estimate_text(
            text, context_valence=self.state_tracker.context_valence
        )
        text_estimate = estimate
        text_ms = (time.perf_counter() - stage_started) * 1000.0
        voice_estimate = None
        audio_flags = set()
        voice_ms = 0.0
        fusion_ms = 0.0
        if audio_path is not None:
            stage_started = time.perf_counter()
            if config.VOICE_ENABLED and numpy_available():
                try:
                    voice_estimate = estimate_voice(audio_path)
                except AudioInputError:
                    audio_flags.add("audio_unavailable")
                else:
                    audio_flags.add("audio_used")
            else:
                audio_flags.add("audio_unavailable")
            voice_ms = (time.perf_counter() - stage_started) * 1000.0
            if voice_estimate is not None:
                stage_started = time.perf_counter()
                estimate, _ = fuse_text_voice(estimate, voice_estimate)
                fusion_ms = (time.perf_counter() - stage_started) * 1000.0
        stage_started = time.perf_counter()
        state = self.state_tracker.begin_turn(estimate, text)
        state_ms = (time.perf_counter() - stage_started) * 1000.0
        stage_started = time.perf_counter()
        decision = choose_action(estimate, state, text)
        action = decision["action"]
        flags = sorted(
            set(estimate.flags)
            | set(state["flags"])
            | set(decision["flags"])
            | audio_flags
        )
        context_intent = self.state_tracker.context_intent
        reply = render_reply(
            action,
            estimate.intent,
            estimate.language,
            state["turn"],
            estimate.entities,
            flags,
            context_intent=context_intent,
        )
        policy_reply_ms = (time.perf_counter() - stage_started) * 1000.0
        stage_started = time.perf_counter()
        self.state_tracker.record_action(action)
        state_ms += (time.perf_counter() - stage_started) * 1000.0
        state_details = {
            "valence": round(float(state["valence"]), 3),
            "activity": round(float(state["activity"]), 3),
            "trend": round(float(state["trend"]), 3),
            "neg_streak": state["neg_streak"],
            "clar_streak": (
                state["clar_streak"] + 1
                if action == "ASK_CLARIFICATION"
                else 0
            ),
        }
        evidence = [
            [
                item["term"],
                *[
                    round(float(value), 3)
                    for value in item["contribution"]
                ],
            ]
            for item in estimate.evidence[: config.DETAILS_EVIDENCE_LIMIT]
        ]
        timing_ms = {"text": round(text_ms, 3)}
        if audio_path is not None:
            timing_ms.update(
                {
                    "voice": round(voice_ms, 3),
                    "fusion": round(fusion_ms, 3),
                }
            )
        timing_ms.update(
            {
                "state": round(state_ms, 3),
                "policy_reply": round(policy_reply_ms, 3),
                "total": 0.0,
            }
        )
        details = {
            "lang": estimate.language,
            "lang_confidence": float(estimate.language_confidence),
            "intent": estimate.intent,
            "evidence": evidence,
            "evidence_count": len(estimate.evidence),
            "sarcasm": round(float(estimate.sarcasm_score), 3),
            "text": {
                "v": round(float(text_estimate.valence), 3),
                "a": round(float(text_estimate.activity), 3),
                "d": round(float(text_estimate.dominance), 3),
                "c": round(float(text_estimate.confidence), 3),
            },
            "voice": (
                voice_estimate.as_dict()
                if voice_estimate is not None
                else None
            ),
            "second_label": estimate.label_details["second_label"],
            "label_distance": round(
                float(estimate.label_details["label_distance"]), 3
            ),
            "second_distance": (
                round(float(estimate.label_details["second_distance"]), 3)
                if estimate.label_details["second_distance"] is not None
                else None
            ),
            "state": state_details,
            "rule": decision["rule"],
            "reason": decision["reason"],
            "timing_ms": timing_ms,
            "engine_version": "1.0",
        }
        if context_intent is not None and estimate.intent == "UNKNOWN":
            # Logged only when the reply actually used the earlier intent,
            # which keeps the one-line log entry short.
            details["context_intent"] = context_intent
        if voice_estimate is not None:
            details["fused"] = {
                "v": round(float(estimate.valence), 3),
                "a": round(float(estimate.activity), 3),
                "d": round(float(estimate.dominance), 3),
                "c": round(float(estimate.confidence), 3),
            }
        result = {
            "valence": float(estimate.valence),
            "activity": float(estimate.activity),
            "dominance": float(estimate.dominance),
            "confidence": float(estimate.confidence),
            "label": str(estimate.label),
            "action": action,
            "reply": reply,
            "flags": flags,
            "details": details,
        }
        timing_ms["total"] = round(
            (time.perf_counter() - pipeline_started) * 1000.0, 3
        )
        return result
