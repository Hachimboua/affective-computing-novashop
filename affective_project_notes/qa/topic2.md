# Topic 2 — Affective model, map and voice: likely questions

1. **What are valence, activity and dominance?**
   Valence: unpleasant ↔ pleasant. Activity (arousal): calm ↔ agitated. Dominance: feeling helpless ↔ in control (PAD model, Mehrabian & Russell, 1974). The map uses valence on x and activity on y (Russell's circumplex, 1980); returning dominance enables the 3D view.
   *Follow-up: why do you need dominance?* To separate fear (low control) from anger (high control): both are negative and activated.

2. **How do you get a label from the numbers?**
   `engine/affect/space.py`: nearest of 7 prototypes (`config.LABEL_PROTOTYPES`) by weighted Euclidean distance (dominance weight 0.5); inside radius 0.18 of the origin → neutral. The runner-up and distances go to the log.
   *Follow-up: why nearest prototype and not rules?* One table to explain and change; every point always gets a label.

3. **Why these seven labels?**
   They are the kit's vocabulary (neutral, calm, joy, anger, frustration, fear, sadness) and they match what the scenarios ask for (P2 sadness, P3 fear).

4. **Dimensional versus discrete models?**
   Discrete: a fixed set of basic emotions. Dimensional: continuous space. We estimate dimensions first and derive labels from them, so the map and the label are always consistent.

5. **What is the SAM?**
   Self-Assessment Manikin (Bradley & Lang, 1994): pictorial 9-point scales for valence, arousal and dominance. Our raters use it; we convert with (r − 5)/4.

6. **What happens when confidence is low?**
   The label stays the nearest prototype, the flag `low_confidence` is added, and the policy may ask for clarification. A separate "uncertain" label would always count as wrong against human labels.

7. **How does the voice channel work? (framing, windowing)**
   `engine/voice/features.py`: pre-emphasis 0.97; 25 ms frames every 10 ms (`VOICE_FRAME_MS`, `VOICE_HOP_MS`) because speech is roughly stationary over ~20–30 ms; a Hamming window reduces spectral leakage at frame edges; FFT gives the power spectrum.
   *Follow-up: what does the hop do?* Overlap between frames so short events are not missed.

8. **What are MFCCs?**
   Power spectrum → 26 mel-spaced triangular filters (mel scale follows human pitch perception) → log → DCT → first 13 coefficients: a compact description of the spectral envelope (timbre). We compute them; activity mainly uses energy, pitch variability and rate.

9. **How do you estimate pitch?**
   Autocorrelation per voiced frame: the lag with the highest correlation between 75 and 500 Hz gives F0; median smoothing removes octave jumps.

10. **Why not use absolute pitch for activity?**
    Speakers differ: the kit's `speaker_low` (~90 Hz) and `speaker_high` (~260 Hz) are both calm. We use energy (0.65), pitch *variability* (0.20) and rate (0.15), standardised against `reference_stats.json`. Result: both stay calm (−0.10 and −0.18).

11. **How are text and voice combined?**
    Late fusion (`engine/affect/fusion.py`): each modality's estimate is weighted by its confidence and a per-dimension weight; voice weighs 0.6 on activity, 0.1 on valence. Agreement gives a small confidence bonus, conflict a penalty. Noisy audio has confidence 0.05, so the text dominates.

12. **What are the voice limits?**
    Six synthetic files only, no real speakers, rough SNR estimate (noisy files are treated as no speech), speaker and microphone dependence, language-independent but culture-dependent prosody.

## Live-change drills (verified)

1. **Wider neutral zone.** `LABEL_NEUTRAL_RADIUS = 0.45` in `config.py`. "A little slow, but okay." changes from frustration to neutral (V −0.38).
2. **Change what fear means.** In `config.TIER_VAD`, set `"FEAR": (-0.60, 0.55, 0.30)` (positive dominance). Restart (the lexicon is loaded once). "I'm scared my card details were stolen!" changes from fear (D −0.52) to anger (D +0.33). Set it back.
3. **Make the voice count more.** `VOICE_ACTIVITY_Z_SCALE = 0.70`. Send "Where is my parcel? I need it for work tomorrow." with `agitated_clean.wav`: fused activity rises from about +0.17 to +0.33; with `calm_clean.wav` it drops from −0.19 to −0.34. Or set `VOICE_ENABLED = False`: the flag `audio_unavailable` appears and activity stays at the text value (−0.05).
