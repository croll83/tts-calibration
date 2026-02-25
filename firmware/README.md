# Firmware AtomS3R per Calibrazione TTS

## Approccio

Invece di riscrivere il firmware da zero, modifichiamo l'esistente con cambiamenti
minimi per metterlo in modalita' "calibrazione":

1. **Streaming audio continuo** (no session timeout)
2. **Auto-start** (invia audio_start appena connesso)
3. **Server URL** punta al calibration server
4. **No wakeword, no button handling** (disabilitati)

## Modifiche necessarie

### 1. `main/jarvis_config.h`

Cambiare l'host del server per puntare al calibration server:

```c
// Prima:
// #define JARVIS_SERVER_HOST  "jarvis.local"
// #define JARVIS_SERVER_PORT  5000

// Calibrazione:
#define JARVIS_SERVER_HOST  "<IP_LXC_CALIBRAZIONE>"
#define JARVIS_SERVER_PORT  8200
```

Oppure cambiare nel `sdkconfig`:
```
CONFIG_JARVIS_SERVER_HOST="<IP_LXC_CALIBRAZIONE>"
CONFIG_JARVIS_SERVER_PORT=8200
```

### 2. `components/jarvis_ws_audio/jarvis_ws_audio.c`

#### a) Disabilitare session timeout

Cercare `SESSION_TIMEOUT_MS` (riga ~54):
```c
// Prima:
#define SESSION_TIMEOUT_MS  30000

// Calibrazione: 10 minuti
#define SESSION_TIMEOUT_MS  600000
```

#### b) Auto-start streaming dopo connessione

Nel handler del messaggio `welcome`, aggiungere auto-start:
```c
// Dopo aver ricevuto "welcome" dal server:
if (strcmp(type, "welcome") == 0) {
    // ... codice esistente ...

    // AUTO-START per calibrazione: invia audio_start subito
    const char *start_msg = "{\"type\":\"audio_start\"}";
    esp_websocket_client_send_text(ws_client, start_msg, strlen(start_msg), portMAX_DELAY);
    ESP_LOGI(TAG, "Auto-sent audio_start (calibration mode)");
}
```

#### c) Re-start automatico dopo speech_end

Quando il server manda `speech_end`, ri-inviare `audio_start` dopo 1 secondo:
```c
if (strcmp(type, "speech_end") == 0) {
    // ... codice esistente ...

    // In calibrazione: ri-avvia dopo pausa
    vTaskDelay(pdMS_TO_TICKS(1000));
    const char *start_msg = "{\"type\":\"audio_start\"}";
    esp_websocket_client_send_text(ws_client, start_msg, strlen(start_msg), portMAX_DELAY);
    ESP_LOGI(TAG, "Auto-restarted audio session (calibration mode)");
}
```

Oppure aggiungere handler per `trigger_listen`:
```c
if (strcmp(type, "trigger_listen") == 0) {
    const char *start_msg = "{\"type\":\"audio_start\"}";
    esp_websocket_client_send_text(ws_client, start_msg, strlen(start_msg), portMAX_DELAY);
    ESP_LOGI(TAG, "Triggered listen → audio_start");
}
```

### 3. `main/main.cpp`

Disabilitare (commentare) la logica del button handler e del display update
per ridurre complessita' e consumo risorse. Il firmware deve solo:
- Connettersi al WiFi
- Connettersi al WS del calibration server
- Streamare audio continuamente

## Build e Flash

```bash
cd /home/jarvis/sviluppo/jarvis/atoms3r-jarvis
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

## Protocollo con il Calibration Server

Il server di calibrazione implementa lo stesso protocollo WS del wakeword server:

1. Device connette a `ws://server:8200/ws/audio?device_id=MAC`
2. Device manda `{"type": "hello", "device_id": "...", "fw": "1.0-calib"}`
3. Server risponde `{"type": "welcome"}`
4. Device manda `{"type": "audio_start"}`
5. Server risponde `{"type": "ready", "session_id": "calib"}`
6. Device streama frame Opus binari (20ms, 16kHz mono)
7. Il server processa audio con VAD, in parallelo triggera HA TTS
8. Loop continuo fino a fine calibrazione

## Note

- Posizionare l'AtomS3R vicino all'Echo (30-50cm) per cattura audio pulita
- L'AtomS3R NON deve essere lo stesso usato per Jarvis (serve dedicato)
- Il microfono dell'AtomS3R cattura l'audio dell'Echo via aria
- La calibrazione dura circa 1-2 ore (40+ frasi con pause di 8s tra una e l'altra)
