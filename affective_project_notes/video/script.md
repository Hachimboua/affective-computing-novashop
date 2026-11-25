# Video demo script (5:00 maximum)

> Follows the brief, section 5.2. **Do not cut the results**; you may cut loading
> and waiting. Values marked `[[value from log]]` must be read from your own
> session log when you record (they are hidden here because your SAM ratings
> are not finished). Rewrite the narration in your own words if you like; keep
> it short and say *why* the engine chose each action.

## Before recording (checklist)

- [ ] Your SAM ratings are done (so seeing the engine's values cannot bias them).
- [ ] Windows notifications off; close other windows.
- [ ] Screen recorder at 1920×1080; terminal font at least 16 pt.
- [ ] `logs/` contains only `README.txt` (so the demo logs are easy to find).
- [ ] Remember: **"Play scenario" does not reset the conversation.** Press **Reset session** before each scenario, otherwise the next scenario starts with the previous one's emotional state. Each reset starts a new log file, so you will end with about five `session_*.txt` files; keep all of them.
- [ ] Microphone test for the voice-over (or plan to use `captions.srt`).
- [ ] `py -3.12 -m unittest discover tests` passes just before recording.

## Timeline

### 0:00–0:30 — Start
**Screen:** File Explorer in `affective_project` → terminal → type `python run_app.py` → the interface opens.
**Say:** "This is the NovaShop affective engine running in the unchanged course interface. I type or play messages; for each one the engine estimates valence, activity and dominance, keeps a state over the conversation, and chooses one of six actions. Everything runs offline in Python."
**Point at:** the 2D map (x valence, y activity), the 3D checkbox (enabled because the engine returns dominance), the confidence bar, the session log panel.

### 0:30–1:25 — M1, calm customer
**Screen:** select `[MANDATORY] M1`, press **Reset session**, then **Play scenario** (messages arrive every 1.5 s).
**Expected (scenario file):** low activity, neutral to positive valence, simple answers, positive close at the end.
**Say per point:** "Message 1 is a calm question: the point is near the centre [[value from log]], label [[value from log]], action ANSWER." … "The last message thanks and closes: closing intent with positive valence and no sarcasm, so rule R3 chooses CLOSE_POSITIVE." Point at `details.rule` in the log.

### 1:25–2:25 — M2, growing frustration
**Screen:** select M2, **Reset session**, **Play scenario**.
**Expected:** valence falls and activity rises message by message; a human is offered or the case escalated before the end.
**Say:** "Watch the numbered points move left and up: [[values from log]]. The state is a confidence-weighted moving average, so one message does not change it all at once." At the human offer: "Rule [[rule from log]] fires because [[reason from log]]." At the lawyer message: "A legal threat is an explicit signal, so rule R2 escalates regardless of the emotion estimate."

### 2:25–3:15 — M3, explicit requests
**Screen:** select M3, **Reset session**, **Play scenario**.
**Expected:** explicit signals (asking for a person, a legal or authority threat) win over the emotion estimate.
**Say:** "Message 2 asks for a human, so rule R1 handles it ([[action from log]]) and the reply says it is an automated assistant." "Message 3 starts with 'Thank you' but threatens to go to the consumer protection authority: the explicit threat wins, so it escalates instead of closing."

### 3:15–4:15 — M4, ambiguity, sarcasm and Portuguese
**Screen:** select M4, **Reset session**, **Play scenario**.
**Expected:** lower confidence on ambiguous input, clarification when unsure, sarcasm noticed, Portuguese handled.
**Say:** "'ok' on its own is ambiguous: low confidence [[value from log]], so it asks for clarification." "'Great, another delay. Really great.' uses positive words about a negative event: the sarcasm flag appears and the valence becomes negative, so it does not close." "The last message is Portuguese: it is detected as Portuguese, recognised as a positive closing, and answered in Portuguese."

### 4:15–5:00 — Log, exported file and voice
**Screen:** expand the Session log panel; scroll one entry; show `rule` and `reason` in DETAILS. Open `logs/session_<date>_<time>.txt` in Notepad.
**Say:** "Every step is in this plain-text log: input, map values, confidence, label, action, flags, latency, reply and our details, including the rule that fired."
**Voice (optional channel):** Reset session. Click **Audio (optional)...**, choose `assets/audio/calm_clean.wav`, type "Where is my parcel? I need it for work tomorrow." and press **Send**. Then Reset session again, attach `agitated_clean.wav`, and send the same text (the attachment is cleared after each Send).
**Say:** "Same words, different voice. The text alone gives activity −0.05. With the calm recording the fused activity is −0.19; with the agitated one it rises to +0.17. Voice mostly changes activity, not valence. With a noisy recording the voice confidence drops, so the engine falls back to the text."

## After recording

1. Trim only loading/waiting. Check the length is at most 5:00.
2. Compress if the file is too large for Moodle:
   `ffmpeg -i raw.mp4 -vf scale=-2:720 -c:v libx264 -preset veryfast -crf 28 -c:a aac -b:a 96k video_demo.mp4`
3. Check the duration: `ffprobe -v error -show_entries format=duration -of csv=p=0 video_demo.mp4` (must be ≤ 300).
4. Keep all the session logs created during the recording (one per reset, all with the recording's date and time in their names): they go into `code/logs/` in the zip. Pass all of them to `package.py --demo-log`.
