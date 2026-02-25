"""
TTS Calibration Server
Riceve audio Opus da AtomS3R, triggera TTS su Alexa via HA, misura durata con VAD.
Ogni frase ripetuta 3 volte, prende mediana, scarta outlier.
Output: CSV + report con coefficienti regressione.
"""

import asyncio
import csv
import json
import logging
import os
import statistics
import time
from pathlib import Path

import httpx
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("calibration")

app = FastAPI(title="TTS Calibration Server")

# --- Configurazione ---
HA_URL = os.getenv("HA_URL", "http://192.168.1.18:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")
ALEXA_ENTITY_ID = os.getenv("ALEXA_ENTITY_ID", "media_player.echo_studio")
RESULTS_DIR = Path("/data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_RATE = 16000

# Parametri calibrazione
REPETITIONS = 3                # ripetizioni per frase
PAUSE_BETWEEN_PHRASES = 8.0   # secondi tra misurazioni
OUTLIER_THRESHOLD = 0.30       # scarta se devia >30% dalla mediana
VAD_THRESHOLD = 0.3            # soglia VAD (abbassata per audio catturato via aria)
AUDIO_GAIN = 3.0               # amplificazione audio (il mic cattura da speaker esterno)


# --- Silero VAD ---
class SileroVAD:
    """Voice Activity Detection usando Silero VAD (ONNX)."""

    def __init__(self, threshold: float = VAD_THRESHOLD):
        import onnxruntime
        model_path = Path(__file__).parent / "silero_vad.onnx"
        if not model_path.exists():
            self._download_model(model_path)
        self.session = onnxruntime.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )
        self.threshold = threshold
        self._sr = np.array([SAMPLE_RATE], dtype=np.int64)
        # Detect model version by checking input names
        input_names = [inp.name for inp in self.session.get_inputs()]
        self._v5 = "state" in input_names  # v5 uses single 'state' tensor
        if self._v5:
            self._state = np.zeros((2, 1, 128), dtype=np.float32)
            logger.info("Silero VAD v5 detected (state input)")
        else:
            self._h = np.zeros((2, 1, 64), dtype=np.float32)
            self._c = np.zeros((2, 1, 64), dtype=np.float32)
            logger.info("Silero VAD v4 detected (h/c inputs)")

    def _download_model(self, path: Path):
        import urllib.request
        url = "https://raw.githubusercontent.com/snakers4/silero-vad/master/src/silero_vad/data/silero_vad.onnx"
        logger.info(f"Downloading Silero VAD model to {path}...")
        urllib.request.urlretrieve(url, str(path))
        logger.info("Download complete.")

    def reset(self):
        if self._v5:
            self._state = np.zeros((2, 1, 128), dtype=np.float32)
        else:
            self._h = np.zeros((2, 1, 64), dtype=np.float32)
            self._c = np.zeros((2, 1, 64), dtype=np.float32)

    def is_speech(self, audio_chunk: np.ndarray, gain: float = 1.0) -> bool:
        if len(audio_chunk) != 512:
            return False
        audio = audio_chunk.astype(np.float32) * gain / 32768.0
        audio = np.clip(audio, -1.0, 1.0)
        audio = audio.reshape(1, -1)
        if self._v5:
            ort_inputs = {
                "input": audio,
                "state": self._state,
                "sr": self._sr,
            }
            out, self._state = self.session.run(None, ort_inputs)
        else:
            ort_inputs = {
                "input": audio,
                "h": self._h,
                "c": self._c,
                "sr": self._sr,
            }
            out, self._h, self._c = self.session.run(None, ort_inputs)
        return float(out[0][0]) > self.threshold


# --- Opus Decoder ---
class OpusDecoder:
    def __init__(self):
        try:
            import opuslib
            self.decoder = opuslib.Decoder(SAMPLE_RATE, 1)
        except ImportError:
            self.decoder = None
            logger.warning("opuslib non disponibile")

    def decode(self, opus_data: bytes) -> np.ndarray | None:
        if not self.decoder:
            return None
        try:
            pcm = self.decoder.decode(opus_data, 320)
            return np.frombuffer(pcm, dtype=np.int16)
        except Exception:
            return None


# --- HA Client ---
async def trigger_alexa_tts(phrase: str, entity_id: str) -> float:
    """Chiama notify.alexa_media su HA. Ritorna il timestamp di invio."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        t_send = time.time()
        resp = await client.post(
            f"{HA_URL}/api/services/notify/alexa_media",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "message": phrase,
                "target": entity_id,
            },
        )
        if resp.status_code not in (200, 201):
            logger.error(f"HA TTS error: {resp.status_code} {resp.text}")
        else:
            logger.info(f"TTS sent ({len(phrase)} chars) to {entity_id}")
        return t_send


# --- Stato globale ---
# audio_queue persiste tra riconnessioni WS — measure_single legge da qui
audio_queue: asyncio.Queue = asyncio.Queue()
device_connected = asyncio.Event()
calibration_running = asyncio.Event()


async def _ws_ping_task(ws: WebSocket, interval: float = 15.0):
    """Manda ping periodici al device per mantenere la connessione WS viva."""
    try:
        while True:
            await asyncio.sleep(interval)
            await ws.send_json({"type": "ping"})
    except Exception:
        pass  # WS chiuso, task termina silenziosamente


@app.websocket("/ws/audio")
async def ws_audio(ws: WebSocket):
    """Endpoint WS compatibile con protocollo AtomS3R."""
    global audio_queue
    await ws.accept()
    # Non ricreare la queue — svuotala e riusa
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except asyncio.QueueEmpty:
            break
    opus_decoder = OpusDecoder()
    device_id = "unknown"

    logger.info("AtomS3R connesso")
    device_connected.set()

    # Keepalive: ping ogni 15s per evitare timeout del client ESP-IDF
    ping_task = asyncio.create_task(_ws_ping_task(ws))

    try:
        await ws.send_json({"type": "welcome"})

        while True:
            data = await ws.receive()
            if data["type"] == "websocket.receive":
                if "text" in data:
                    msg = json.loads(data["text"])
                    msg_type = msg.get("type", "")
                    if msg_type == "hello":
                        device_id = msg.get("device_id", "unknown")
                        logger.info(f"Device hello: {device_id} fw={msg.get('fw')}")
                    elif msg_type == "audio_start":
                        await ws.send_json({"type": "ready", "session_id": "calib"})
                        logger.info("Audio session started")
                    elif msg_type == "state":
                        logger.info(f"Device state: {msg.get('state')}")
                    elif msg_type == "pong":
                        pass
                elif "bytes" in data:
                    pcm = opus_decoder.decode(data["bytes"])
                    if pcm is not None:
                        await audio_queue.put(pcm)

    except WebSocketDisconnect:
        logger.info(f"Device {device_id} disconnesso")
    except Exception as e:
        logger.error(f"WS error: {e}")
    finally:
        ping_task.cancel()
        device_connected.clear()


async def measure_single(
    phrase: str, vad: SileroVAD, entity_id: str, timeout: float = 90.0
) -> dict | None:
    """Misura singola: trigger TTS, VAD rileva start/end speech."""
    global audio_queue
    if not audio_queue:
        logger.warning("measure_single: audio_queue is None!")
        return None

    # Svuota coda
    drained = 0
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
            drained += 1
        except asyncio.QueueEmpty:
            break
    if drained:
        logger.info(f"  Drained {drained} stale audio chunks from queue")

    vad.reset()
    t_notify = await trigger_alexa_tts(phrase, entity_id)

    speech_started = False
    t_speech_start = None
    t_speech_end = None
    silence_count = 0
    chunks_processed = 0
    speech_chunks = 0
    SILENCE_THRESHOLD = 25  # ~500ms @ ~20ms/chunk
    deadline = time.time() + timeout

    # Accumulator: Opus frames are 320 samples, VAD wants 512
    pcm_buffer = np.array([], dtype=np.int16)

    while time.time() < deadline:
        try:
            pcm_chunk = await asyncio.wait_for(audio_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            if chunks_processed == 0:
                logger.warning("  No audio received (queue timeout)")
            continue

        # Accumula campioni
        pcm_buffer = np.concatenate([pcm_buffer, pcm_chunk])

        # Processa tutti i blocchi da 512 disponibili
        while len(pcm_buffer) >= 512:
            vad_chunk = pcm_buffer[:512]
            pcm_buffer = pcm_buffer[512:]
            chunks_processed += 1

            is_speech = vad.is_speech(vad_chunk, gain=AUDIO_GAIN)

            rms = np.sqrt(np.mean(vad_chunk.astype(np.float32) ** 2))

            if chunks_processed == 1:
                logger.info(f"  First audio chunk: RMS={rms:.1f}, speech={is_speech}")
            elif chunks_processed % 50 == 0:
                logger.info(f"  Chunk #{chunks_processed}: RMS={rms:.1f}, speech={is_speech}, started={speech_started}")

            if is_speech:
                speech_chunks += 1

            if is_speech and not speech_started:
                speech_started = True
                t_speech_start = time.time()
                silence_count = 0
                logger.info(f"  VAD: speech START (after {chunks_processed} chunks)")
            elif is_speech and speech_started:
                silence_count = 0
            elif not is_speech and speech_started:
                silence_count += 1
                if silence_count >= SILENCE_THRESHOLD:
                    t_speech_end = time.time() - (SILENCE_THRESHOLD * 0.032)
                    logger.info(f"  VAD: speech END (total {chunks_processed} chunks, {speech_chunks} speech)")
                    break

        if t_speech_end:
            break

    if not speech_started or not t_speech_end:
        logger.warning(f"  VAD failed: chunks={chunks_processed}, speech_started={speech_started}, speech_chunks={speech_chunks}")
        return None

    speech_duration = t_speech_end - t_speech_start
    latency = t_speech_start - t_notify
    chars = len(phrase)
    words = len(phrase.split())

    return {
        "phrase": phrase,
        "chars": chars,
        "words": words,
        "speech_duration_s": round(speech_duration, 3),
        "notify_to_start_s": round(latency, 3),
        "total_duration_s": round(t_speech_end - t_notify, 3),
        "chars_per_s": round(chars / speech_duration, 2) if speech_duration > 0 else 0,
        "words_per_s": round(words / speech_duration, 2) if speech_duration > 0 else 0,
    }


async def measure_with_repetitions(
    phrase: str, vad: SileroVAD, entity_id: str, reps: int = REPETITIONS
) -> dict | None:
    """
    Ripete la misurazione `reps` volte, prende la mediana,
    scarta outlier (deviazione >30% dalla mediana).
    """
    measurements = []
    for r in range(reps):
        logger.info(f"    Rep {r+1}/{reps}")
        await asyncio.sleep(PAUSE_BETWEEN_PHRASES)
        result = await measure_single(phrase, vad, entity_id)
        if result:
            measurements.append(result)
            logger.info(
                f"    → speech={result['speech_duration_s']:.2f}s, "
                f"latency={result['notify_to_start_s']:.2f}s"
            )
        else:
            logger.warning(f"    → FAILED")

    if not measurements:
        return None

    # Prendi mediana della speech_duration
    durations = [m["speech_duration_s"] for m in measurements]
    median_dur = statistics.median(durations)

    # Scarta outlier (>30% dalla mediana)
    valid = [
        m for m in measurements
        if abs(m["speech_duration_s"] - median_dur) / median_dur <= OUTLIER_THRESHOLD
    ] if median_dur > 0 else measurements

    if not valid:
        valid = measurements  # fallback: tieni tutto

    # Se dopo filtering abbiamo scartato qualcosa, logga
    discarded = len(measurements) - len(valid)
    if discarded:
        logger.info(
            f"    Outlier: scartate {discarded}/{len(measurements)} misurazioni "
            f"(mediana={median_dur:.2f}s)"
        )

    # Calcola medie dei valori validi
    avg_speech = statistics.mean([m["speech_duration_s"] for m in valid])
    avg_latency = statistics.mean([m["notify_to_start_s"] for m in valid])
    chars = valid[0]["chars"]
    words = valid[0]["words"]

    return {
        "phrase": phrase,
        "chars": chars,
        "words": words,
        "speech_duration_s": round(avg_speech, 3),
        "notify_to_start_s": round(avg_latency, 3),
        "total_duration_s": round(avg_speech + avg_latency, 3),
        "chars_per_s": round(chars / avg_speech, 2) if avg_speech > 0 else 0,
        "words_per_s": round(words / avg_speech, 2) if avg_speech > 0 else 0,
        "repetitions": len(measurements),
        "valid_reps": len(valid),
        "median_duration_s": round(median_dur, 3),
    }


# --- API ---

@app.post("/api/calibrate")
async def start_calibration(entity_id: str | None = None):
    """
    Avvia calibrazione completa.
    Query param `entity_id` per override del device (es. media_player.echo_dot_cucina).
    """
    if calibration_running.is_set():
        return {"error": "Calibrazione gia' in corso"}
    if not device_connected.is_set():
        return {"error": "Nessun device connesso"}

    target = entity_id or ALEXA_ENTITY_ID
    calibration_running.set()
    asyncio.create_task(_run_calibration(target))
    return {
        "status": "started",
        "entity_id": target,
        "phrases": len(PHRASES),
        "repetitions": REPETITIONS,
        "total_measurements": len(PHRASES) * REPETITIONS,
        "estimated_duration_min": round(len(PHRASES) * REPETITIONS * (PAUSE_BETWEEN_PHRASES + 8) / 60),
    }


@app.post("/api/calibrate/single")
async def calibrate_single(
    phrase: str = "Ciao, questo è un test del text to speech.",
    entity_id: str | None = None,
):
    """Testa una singola frase (senza ripetizioni)."""
    if not device_connected.is_set():
        return {"error": "Nessun device connesso"}

    target = entity_id or ALEXA_ENTITY_ID
    vad = SileroVAD()
    await asyncio.sleep(1.0)
    result = await measure_single(phrase, vad, target)
    return result or {"error": "Misurazione fallita"}


@app.get("/api/status")
async def get_status():
    return {
        "device_connected": device_connected.is_set(),
        "calibration_running": calibration_running.is_set(),
        "config": {
            "entity_id": ALEXA_ENTITY_ID,
            "ha_url": HA_URL,
            "vad_threshold": VAD_THRESHOLD,
            "repetitions": REPETITIONS,
            "outlier_threshold": OUTLIER_THRESHOLD,
        },
    }


@app.post("/api/stop")
async def stop_calibration():
    """Ferma la calibrazione in corso."""
    calibration_running.clear()
    return {"status": "stopping"}


# --- Calibrazione ---

from phrases import CALIBRATION_PHRASES as PHRASES, VALIDATION_PHRASES


async def _run_calibration(entity_id: str):
    """Esegue calibrazione completa: tutte le frasi × N ripetizioni."""
    logger.info(f"{'='*60}")
    logger.info(f"INIZIO CALIBRAZIONE")
    logger.info(f"  Entity: {entity_id}")
    logger.info(f"  Frasi: {len(PHRASES)}")
    logger.info(f"  Ripetizioni: {REPETITIONS}")
    logger.info(f"  Misurazioni totali: {len(PHRASES) * REPETITIONS}")
    logger.info(f"{'='*60}")

    vad = SileroVAD()
    results = []
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    csv_path = RESULTS_DIR / f"calibration_{timestamp}.csv"

    fieldnames = [
        "phrase", "chars", "words", "speech_duration_s",
        "notify_to_start_s", "total_duration_s", "chars_per_s", "words_per_s",
        "repetitions", "valid_reps", "median_duration_s",
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, phrase in enumerate(PHRASES):
            if not calibration_running.is_set():
                logger.info("Calibrazione interrotta dall'utente")
                break

            logger.info(f"\n--- Frase {i+1}/{len(PHRASES)} ({len(phrase)} chars) ---")
            logger.info(f"  \"{phrase[:80]}{'...' if len(phrase) > 80 else ''}\"")

            result = await measure_with_repetitions(phrase, vad, entity_id)
            if result:
                writer.writerow(result)
                f.flush()
                results.append(result)
                logger.info(
                    f"  RESULT: {result['chars']} chars → {result['speech_duration_s']:.2f}s "
                    f"({result['chars_per_s']} chars/s, {result['valid_reps']}/{result['repetitions']} valid)"
                )
            else:
                logger.warning(f"  SKIP: tutte le misurazioni fallite per frase {i+1}")

    # Regressione + report
    if len(results) >= 10:
        _compute_regression(results, timestamp, entity_id)

        # Validazione
        logger.info(f"\n--- VALIDAZIONE ({len(VALIDATION_PHRASES)} frasi) ---")
        for vp in VALIDATION_PHRASES:
            if not calibration_running.is_set():
                break
            await asyncio.sleep(PAUSE_BETWEEN_PHRASES)
            vr = await measure_single(vp, vad, entity_id)
            if vr:
                logger.info(
                    f"  VALID: {vr['chars']} chars, "
                    f"measured={vr['speech_duration_s']:.2f}s"
                )
    else:
        logger.warning(f"Troppo pochi risultati ({len(results)}) per regressione")

    logger.info(f"\n{'='*60}")
    logger.info(f"CALIBRAZIONE COMPLETA — {len(results)}/{len(PHRASES)} frasi misurate")
    logger.info(f"CSV: {csv_path}")
    logger.info(f"{'='*60}")
    calibration_running.clear()


def _compute_regression(results: list[dict], timestamp: str, entity_id: str):
    """Regressione lineare + report."""
    chars = np.array([r["chars"] for r in results])
    words = np.array([r["words"] for r in results])
    durations = np.array([r["speech_duration_s"] for r in results])

    # Regressione chars: duration = A * chars + B
    M = np.vstack([chars, np.ones(len(chars))]).T
    coeff_a, coeff_b = np.linalg.lstsq(M, durations, rcond=None)[0]

    predicted = coeff_a * chars + coeff_b
    ss_res = np.sum((durations - predicted) ** 2)
    ss_tot = np.sum((durations - np.mean(durations)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Regressione words
    M_w = np.vstack([words, np.ones(len(words))]).T
    coeff_a_w, coeff_b_w = np.linalg.lstsq(M_w, durations, rcond=None)[0]

    # Errore massimo
    errors = np.abs(durations - predicted)
    max_error = np.max(errors)
    p95_error = np.percentile(errors, 95)

    # Statistiche
    avg_chars_per_s = np.mean([r["chars_per_s"] for r in results])
    std_chars_per_s = np.std([r["chars_per_s"] for r in results])
    avg_words_per_s = np.mean([r["words_per_s"] for r in results])
    avg_latency = np.mean([r["notify_to_start_s"] for r in results])
    std_latency = np.std([r["notify_to_start_s"] for r in results])

    report = f"""# TTS Calibration Report — {timestamp}
Entity: `{entity_id}`

## Modello Chars-based (PRIMARIO)
```python
TTS_COEFFICIENT_A = {coeff_a:.6f}   # secondi per carattere
TTS_COEFFICIENT_B = {coeff_b:.3f}          # overhead fisso (s)
# duration_s = {coeff_a:.6f} * chars + {coeff_b:.3f}
```
- R² = {r_squared:.4f}
- Errore massimo = {max_error:.2f}s
- Errore P95 = {p95_error:.2f}s
- Media chars/s = {avg_chars_per_s:.2f} (std={std_chars_per_s:.2f})

## Modello Words-based (ALTERNATIVO)
```python
TTS_COEFFICIENT_A_WORDS = {coeff_a_w:.6f}   # secondi per parola
TTS_COEFFICIENT_B_WORDS = {coeff_b_w:.3f}
# duration_s = {coeff_a_w:.6f} * words + {coeff_b_w:.3f}
```
- Media words/s = {avg_words_per_s:.2f}

## Latenza notify → speech start
- Media = {avg_latency:.3f}s (std={std_latency:.3f}s)

## Campione
- Frasi misurate: {len(results)}/{len(PHRASES)}
- Ripetizioni per frase: {REPETITIONS} (mediana + outlier filtering)
- Range chars: {int(np.min(chars))} — {int(np.max(chars))}

## Costanti per orchestrator (copia-incolla)
```python
# TTS Calibration — {timestamp} — {entity_id}
TTS_COEFFICIENT_A = {coeff_a:.6f}
TTS_COEFFICIENT_B = {coeff_b:.3f}
TTS_SAFETY_MARGIN = 1.10  # +10% buffer
TTS_NOTIFY_LATENCY = {avg_latency:.3f}

def estimate_tts_duration(text: str) -> float:
    chars = len(text)
    return (TTS_COEFFICIENT_A * chars + TTS_COEFFICIENT_B) * TTS_SAFETY_MARGIN
```
"""

    report_path = RESULTS_DIR / f"report_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(report)

    logger.info(f"\n{'='*60}")
    logger.info(f"REGRESSIONE COMPLETATA")
    logger.info(f"  duration = {coeff_a:.6f} * chars + {coeff_b:.3f}")
    logger.info(f"  R² = {r_squared:.4f}")
    logger.info(f"  Errore P95 = {p95_error:.2f}s, Max = {max_error:.2f}s")
    logger.info(f"  Velocita': {avg_chars_per_s:.1f} chars/s, {avg_words_per_s:.1f} words/s")
    logger.info(f"  Latenza: {avg_latency:.3f}s (std={std_latency:.3f}s)")
    logger.info(f"  Report: {report_path}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
