# SignBridge - Overview

SignBridge lets a Deaf or hard-of-hearing person who uses **Indian Sign Language (ISL)** and a hearing
person hold a conversation on one screen, in both directions, in real time and without needing the internet.

## The problem

- Most people do not understand ISL and interpreters are rarely available.
- Existing tools work one way only (signs to text), and struggle with continuous signing in real conditions.
- The hearing side of the conversation gets no live subtitles.

## Who it is for

- Deaf and hard-of-hearing ISL users
- Hearing people who talk with them: family, shop and office staff, hospitals, public services
- Sign-language trainers (practice mode gives instant feedback on each sign)

## What it does

| # | Feature | How |
|---|---------|-----|
| F1 | Live sign recognition | Webcam -> MediaPipe landmarks -> small ONNX models -> sign + confidence. 50 everyday words and fingerspelling A-Z / 1-9. |
| F2 | Sentence formation | Signs collect in a strip; a ~3 s pause closes the sentence. Offline grammar rules build it; when online, Gemini polishes the wording. |
| F3 | Speech output | The sentence is spoken with offline text-to-speech (pyttsx3 -> WAV in the browser). |
| F4 | Speech -> live subtitles | The hearing person talks; faster-whisper (on this computer) shows large live subtitles, updated every ~1.2 s. |
| F5 | Conversation mode | Both directions on one screen; the transcript can be saved (History) and downloaded. |
| F6 | Offline + latency | Everything runs locally on CPU; FPS and per-frame latency are shown live, online status in the header. |
| F7 | Evaluation | Accuracy, per-class F1, confusion matrices, continuous-signing WER and latency of every stage (Performance page). |

## Screens

1. **Landing** - what SignBridge does.
2. **Login / register** - demo account `demo@signbridge.app` / `demo1234`.
3. **Conversation** - camera with hand skeleton, live top-3 guess, sign strip, sentence + speech; subtitles and microphone for the hearing person; transcript with save / download.
4. **Practice** - pick a sign or letter, sign it, get right / wrong feedback and a session score.
5. **History** - saved conversations, read / download / delete.
6. **Model performance** - accuracy, confusion matrices, per-class table, latency and reliability.

## Starting vocabulary (50 words)

Greetings: hello, how are you, thank you, good morning, good night, alright, pleased ·
Pronouns: I, you, he, she, we, they · People: mother, father, brother, sister, friend, family, baby,
doctor, teacher, police · Places: hospital, house, school, market, bank, office, restaurant ·
Describing: good, bad, happy, sad, sick, hot, cold, new, fast, slow · Time: today, tomorrow,
yesterday, morning, night, time · Things: medicine, money, book, bathroom.
Plus fingerspelling **A-Z and 1-9** for names and any other word.

## Not in this version

Text-to-sign avatar playback, a recorder for teaching new signs, and packaging for Raspberry Pi / Jetson.
