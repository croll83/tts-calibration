# Firmware AtomS3R per Calibrazione TTS

Firmware derivato da `atoms3r-jarvis` con modifiche minime per la modalita' calibrazione.

## Modifiche rispetto al firmware originale

1. **`components/jarvis_ws_audio/jarvis_ws_audio.c`**:
   - `SESSION_TIMEOUT_MS` aumentato a 600000 (10 minuti)
   - Auto-request audio session dopo `welcome` dal server
   - Log di auto-restart dopo `speech_end`

2. **`main/main.cpp`**:
   - `FIRMWARE_VERSION` = `5.0.0-calib`
   - `on_session_done()` semplificato: torna a IDLE senza logica BUSY/wake word

3. **Comportamento**:
   - Alla connessione WS, il firmware richiede automaticamente una audio session
   - Quando il server manda `speech_end`, la sessione termina e ne viene riavviata una nuova
   - Loop continuo: connetti -> streama audio -> speech_end -> riavvia
   - No wake word, no button handling necessario (ma funzionano ancora)

## Quick Start

```bash
# 1. Copia il template e personalizza
cp sdkconfig.local.example sdkconfig.local
# Edita sdkconfig.local con il tuo WiFi e l'IP del calibration server

# 2. Build + Flash + Monitor
./build.sh flash monitor
```

## Configurazione (sdkconfig.local)

| Variabile | Descrizione |
|-----------|-------------|
| `CONFIG_WIFI_SSID` | SSID della rete WiFi |
| `CONFIG_WIFI_PASSWORD` | Password WiFi |
| `CONFIG_JARVIS_SERVER_HOST` | IP del calibration server LXC |
| `CONFIG_JARVIS_SERVER_PORT` | Porta del calibration server (default: 8200) |
| `CONFIG_JARVIS_WS_URL` | Override URL WebSocket (opzionale) |
| `CONFIG_JARVIS_API_TOKEN` | Token API (non necessario per calibrazione) |

## Protocollo con il Calibration Server

Il server di calibrazione implementa lo stesso protocollo WS del wakeword server:

1. Device connette a `ws://server:8200/ws/audio?device_id=MAC`
2. Device manda `{"type": "hello", "device_id": "...", "fw": "5.0.0-calib"}`
3. Server risponde `{"type": "welcome"}`
4. Device auto-requests `{"type": "audio_start"}`
5. Server risponde `{"type": "ready", "session_id": "calib"}`
6. Device streama frame Opus binari (20ms, 16kHz mono)
7. Il server processa audio con VAD, in parallelo triggera HA TTS
8. Server manda `speech_end` -> device riavvia sessione
9. Loop continuo fino a fine calibrazione

## Note

- Posizionare l'AtomS3R vicino all'Echo (30-50cm) per cattura audio pulita
- L'AtomS3R NON deve essere lo stesso usato per Jarvis (serve dedicato)
- Il microfono dell'AtomS3R cattura l'audio dell'Echo via aria
- La calibrazione dura circa 1 ora (78 frasi x 3 ripetizioni)
