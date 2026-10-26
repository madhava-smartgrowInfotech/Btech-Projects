"""Index of the StoryVox design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs/make_diagrams.py into docs/diagrams/ (matplotlib, 150 dpi).
Used by the block-diagram document (11), the full report, the decks and the paper.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Layered architecture of StoryVox: React console, FastAPI application with 11 API routes, the service layer, pretrained models, SQLite and WAV storage.",
     "The presentation tier is a React 19 single-page app with five pages (Home, Studio, History, Story and Evaluation) served by Vite on port 5402; the Vite proxy forwards every /api request to the FastAPI application on port 8402, "
     "and after `npm run build` the same FastAPI process serves the built frontend/dist files through a single-page-app fallback route. The application tier holds one APIRouter with eleven routes, the Pydantic request and response schemas, and the settings object that reads environment variables and carries the 15 languages, 8 styles and 3 lengths. "
     "The service tier contains story_generator, tts_service (with its TTSProvider chain), asr_service, evaluation_service and a few helper modules. Models are loaded lazily from the Hugging Face cache on first use: Qwen3-0.6B for stories, one facebook/mms-tts checkpoint per language for speech, whisper-small and a multilingual MiniLM only for evaluation. "
     "Everything is stored locally: three SQLite tables in data/storyvox.db, narration WAV files in data/audio and evaluation JSON and CSV files in data/evaluations."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "End-to-end workflow: enter an idea, validate, build the prompt, generate, parse, save, narrate, store the audio, play, manage history and evaluate.",
     "The user enters a story idea in the Studio and chooses a language, style, length and whether narration should start automatically. The API validates the request, builds a prompt that carries the style guidance, the paragraph target and a first-line title rule, and asks the language model for a story; if the model cannot be loaded or returns too little text, an offline composer writes a prompt-conditioned story instead. "
     "The title and body are parsed, counted and saved as a stories row. Narration then splits the text into chunks of at most 380 characters, synthesises each chunk with the checkpoint of the chosen language (or the operating-system voice if that fails), joins the chunks and stores the WAV file together with an audio_outputs row. "
     "The browser plays and downloads the audio through /api/audio/{id}, the History page lists, opens, re-narrates and deletes stories, and the Evaluation page runs the measurement loop. There is no separate translation step: the story is written directly in the chosen language."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0): StoryVox as one process with the user, the Hugging Face Hub and the operating-system speech engine.",
     "At level 0 the whole product is a single process. The user sends a story idea with a language, style and length, history actions and evaluation requests, and receives the story text, the narration audio, the story list and the evaluation metrics. "
     "The Hugging Face Hub is an external source of model weights and tokenizers; it is contacted only when a model is not yet in the local cache. The operating-system speech engine (SAPI through pyttsx3) receives text and returns audio only when the neural speech checkpoint cannot be used. "
     "No analytics service and no cloud storage appear on the diagram because the product does not use them."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: five processes (validate, generate story, synthesise narration, manage history, run evaluation) and the data stores D1 to D4.",
     "Level 1 splits the product into five processes. Process 1.0 validates the request (non-empty prompt of at most 2000 characters, a supported language, style and length). Process 2.0 generates the story text with the language model or the offline composer and writes the title, body and word count to the stories store (D1). "
     "Process 3.0 synthesises the narration, writes the WAV file to D3 and records the duration, model id, synthesis time and real-time factor in the audio_outputs store (D2). Process 4.0 reads D1, D2 and D3 to list, open, stream and delete stories and to regenerate narration. "
     "Process 5.0 runs the evaluation by calling processes 2.0 and 3.0 on built-in prompts, transcribing the audio and writing the metrics to the evaluation store (D4, one database row plus a JSON and a CSV file)."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: process 3.0 expanded into seven sub-processes, from chunking to the written WAV file, including the silence check and the fallback voice.",
     "Process 3.1 splits the story into chunks of at most 380 characters at sentence boundaries. Process 3.2 loads the facebook/mms-tts checkpoint of the chosen language once and caches it, downloading it from the Hugging Face cache on the first call. "
     "Process 3.3 runs the VITS model on every chunk, and process 3.4 normalises each waveform to a peak of 0.9 and joins the chunks with 0.25-second pauses at 16 kHz. Process 3.5 rejects empty or silent audio (RMS below 1e-4). "
     "A silent result, an empty result or any load or inference error sends the text to process 3.6, the operating-system voice, which saves a WAV file, reads it back and resamples it to 16 kHz. Process 3.7 computes the duration and the real-time factor, writes the WAV file to data/audio and returns the values that become an audio_outputs row."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram: API routes and schemas, the story and speech services with the TTSProvider hierarchy, evaluation and helper modules, and the three ORM classes.",
     "Most of StoryVox is written as modules of functions, so the diagram shows each module as a class-like box with its main operations. The routes module exposes eleven handlers; it validates with the Pydantic schemas, calls story_generator and tts_service directly, and reaches evaluation_service and the SQLAlchemy models through a session. "
     "TTSProvider is an abstract class with one method, synthesize; MMSTTSProvider and SystemTTSProvider implement it, and tts_service tries them in that order. asr_service wraps the Whisper pipeline, and evaluation_service combines the generator, the narration service, the recogniser and the helper functions for word and character error rates, TF-IDF cosine and ROUGE-L. "
     "Story owns zero or more AudioOutput objects through a cascading relationship, while Evaluation stands alone and stores its metrics as a JSON column."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_flow.png",
     "Sequence diagram of POST /api/stories/generate with narration, followed by the audio request.",
     "The browser posts the idea, language, style, length and synthesize flag. The route validates them (HTTP 422 on failure), calls generate_story_text, which returns the title, body, model id and elapsed seconds, and inserts the stories row. "
     "When synthesize is true, the route calls synthesize_story_narration; the service tries the MMS checkpoint, falls back to the operating-system voice if needed, writes the WAV file to data/audio and returns the path, duration, model id, synthesis time and real-time factor. "
     "The route inserts the audio_outputs row and answers with a StoryResponse that contains the audio URL. If narration raises an error, the story is still saved and returned without audio so that it can be narrated later. "
     "The browser then requests /api/audio/{id}, and the route streams the stored WAV file as audio/wav."),
    ("usecase", "Use-case diagram", "08_use_case.png",
     "Use-case diagram: the story creator and the library and evaluation user, twelve use cases, and the model cache and speech engine as supporting systems.",
     "The product has no accounts, so the two actors are roles of the same local user on different pages. The story creator, working in the Studio, enters an idea, chooses language, style and length, generates a story (which includes the first two), narrates it, plays it and downloads the WAV file. "
     "The library and evaluation user works on the History, Story and Evaluation pages: browses the history, opens a story, regenerates its narration, deletes a story together with its audio, runs an evaluation and views the metrics. "
     "The Hugging Face model cache and the operating-system speech engine are supporting systems used by story generation, narration and the evaluation run. Translation, rating, voice choice, speed control and reference-audio upload are not use cases of this build."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram of the SQLite database: stories (1) to audio_outputs (0..*), and the stand-alone evaluations table.",
     "The database data/storyvox.db has three tables created by SQLAlchemy from app/models/__init__.py. The stories table holds the prompt, title, body, language code and name, style, length option, word count, creation time and generation time. "
     "The audio_outputs table holds one row per narration with the story_id foreign key, the WAV path, duration, sample rate, speech model id, synthesis time and real-time factor, so one story can have several narrations after regeneration. "
     "Deleting a story removes its audio rows through the ORM cascade, and the route also deletes the WAV files; SQLite foreign-key enforcement is not switched on, so the cascade is done by the ORM rather than by the database. "
     "The evaluations table is independent: its metrics_json column keeps the whole result of one evaluation run, which is also written to data/evaluations as JSON and CSV."),
    ("algo", "Flowchart of the core algorithm", "10_flowchart_algorithm.png",
     "Flowchart of generate_story_text: validate, build the prompt, load the model once, sample, parse, check the length and otherwise use the offline composer.",
     "The function rejects an unknown language, style or length, an empty prompt and a prompt over 2000 characters with a ValueError that the route turns into HTTP 422. It builds a prompt from the style guidance, the paragraph target for the chosen length and the rule that the first line must start with 'Title:'. "
     "The Qwen3-0.6B text-generation pipeline is created once under a lock and cached; if loading fails the composer is used. Sampling uses a temperature of 0.8, top-p of 0.9 and a token budget of 220, 420 or 700 new tokens for Short, Medium and Long. "
     "The parser takes the 'Title:' line (or a short first line) as the title and the rest as the body. A body of fewer than 20 words, or any exception, switches to local_fallback_story, which always returns a story that quotes the idea, and the model id returned to the caller records which path produced the text."),
    ("tts_eval", "Flowchart of narration and evaluation", "11_flowchart_tts_evaluation.png",
     "Left: the narration provider chain with its silence check and fallback. Right: the evaluation loop that produces WER, CER, similarity, ROUGE-L and RTF.",
     "On the left, synthesize_story_narration checks the text and language, then tries the MMS provider: chunking, VITS inference, peak normalisation and joining. Empty or silent audio, or any load or inference error, sends the text to the operating-system provider; if that also fails, a RuntimeError becomes HTTP 500. "
     "The duration and the real-time factor (synthesis time divided by audio duration) are computed and the WAV file is written. On the right, run_evaluation takes the first n of five built-in prompts, generates a story, computes the prompt-story similarity (multilingual MiniLM, or a TF-IDF proxy) and ROUGE-L, narrates the story, and transcribes the audio with Whisper to obtain WER and CER against the story text. "
     "If the recogniser cannot be loaded the error is kept in the row and WER and CER stay empty; otherwise they are averaged. The averages and every sample are written to JSON and CSV, and the API route also stores one evaluations row."),
    ("model", "Model architecture", "12_model_architecture.png",
     "The four pretrained models used by StoryVox, each shown as its processing chain: Qwen3-0.6B, MMS-TTS (VITS), Whisper-small and multilingual MiniLM.",
     "StoryVox trains no model of its own; it combines four pretrained ones. Qwen3-0.6B is a decoder-only language model that continues the prompt token by token with sampling. "
     "Each facebook/mms-tts checkpoint is a VITS model: a text encoder, a stochastic duration predictor and a normalising flow, run in reverse at inference, produce the latent representation that a HiFi-GAN decoder turns into a 16 kHz waveform. "
     "Whisper-small (an encoder-decoder Transformer) and paraphrase-multilingual-MiniLM-L12-v2 (a 12-layer sentence encoder) are used only by the evaluation: the first turns the narration back into text for the word and character error rates, the second compares the prompt with the story. "
     "The language of the speech model is chosen by the language code, so supporting a language means mapping it to a checkpoint in app/config.py."),
]
