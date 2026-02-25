"""
Frasi italiane di test per calibrazione TTS Alexa.
~80 frasi da ~10 a ~500 caratteri, distribuite uniformemente.
Ogni frase verra' ripetuta 3 volte per mediana + outlier detection.
"""

CALIBRATION_PHRASES = [
    # === CORTE (10-30 chars) — 16 frasi ===
    "Ciao, come stai?",
    "Buongiorno a tutti.",
    "Sì, certo.",
    "No, grazie mille.",
    "Fatto, luce accesa.",
    "Sono le tre e mezza.",
    "Ok, nessun problema.",
    "Ecco fatto.",
    "Un momento per favore.",
    "Va bene, ci penso io.",
    "Buonanotte, dormi bene.",
    "Temperatura impostata.",
    "Perfetto, grazie.",
    "Ci vediamo domani.",
    "A che ora è?",
    "Non lo so ancora.",

    # === MEDIE-CORTE (30-60 chars) — 16 frasi ===
    "La temperatura in salotto è di ventidue gradi.",
    "Ho acceso la luce del corridoio come richiesto.",
    "Domani il tempo sarà sereno con temperature miti.",
    "Il timer è stato impostato per quindici minuti.",
    "La sveglia è programmata per le sette di mattina.",
    "Ho abbassato il volume della televisione al trenta.",
    "La lavatrice finirà il ciclo tra circa un'ora.",
    "Non ci sono eventi nel tuo calendario per domani.",
    "Il condizionatore è stato spento come richiesto.",
    "Hai tre messaggi non letti nella tua casella email.",
    "La porta del garage risulta chiusa correttamente.",
    "Ho aggiunto latte e pane alla lista della spesa.",
    "Il riscaldamento è attivo in modalità automatica.",
    "La connessione internet funziona correttamente.",
    "Sono le quattordici e quarantacinque di martedì.",
    "Nessuna notifica importante nelle ultime due ore.",

    # === MEDIE (60-120 chars) — 16 frasi ===
    "Buongiorno! Oggi è martedì venticinque febbraio. La temperatura esterna è di dodici gradi con cielo parzialmente nuvoloso.",
    "Ho trovato tre ristoranti italiani nelle vicinanze. Il più vicino si trova a circa cinquecento metri da qui.",
    "La riunione di domani alle dieci è stata confermata con quattro partecipanti. Ti mando un promemoria mezz'ora prima.",
    "Il consumo energetico di oggi è stato di dodici kilowattora, il quindici percento in meno rispetto a ieri.",
    "Secondo le previsioni, domani pioverà nel pomeriggio con temperature tra i dieci e i quindici gradi.",
    "Ho impostato la scena cinema: luci soffuse in salotto, televisione accesa e tapparelle abbassate.",
    "Il pacco che aspetti risulta in consegna oggi. L'ultimo aggiornamento indica che è nel centro di smistamento locale.",
    "La batteria dell'auto elettrica è carica all'ottanta percento. L'autonomia stimata è di circa trecento chilometri.",
    "Ho programmato il robot aspirapolvere per le due del pomeriggio quando non ci sarà nessuno in casa.",
    "Il filtro dell'aria condizionata necessita di manutenzione. Sono passati novanta giorni dall'ultima pulizia.",
    "Nella tua libreria ci sono attualmente centoventi libri catalogati. L'ultimo aggiunto è stato tre giorni fa.",
    "Il sensore del giardino rileva un'umidità del terreno al quaranta percento. Forse è il caso di innaffiare.",
    "La videocamera del cancello ha registrato un movimento alle tre di notte. Vuoi vedere la registrazione?",
    "Il frigorifero segnala che stai esaurendo il latte. Lo aggiungo alla lista della spesa automaticamente?",
    "Le tapparelle del soggiorno sono state abbassate al settanta percento come da programmazione serale.",
    "La qualità dell'aria interna è buona. I livelli di anidride carbonica sono nella norma in tutte le stanze.",

    # === MEDIE-LUNGHE (120-200 chars) — 12 frasi ===
    "Ecco il riepilogo della giornata. Hai due riunioni: una alle dieci con il team di sviluppo e una alle quindici con il cliente. Nel pomeriggio c'è anche la consegna del pacco che aspetti da giovedì.",
    "Ho analizzato i consumi della settimana. Il riscaldamento ha usato il sessanta percento dell'energia totale. Ti consiglio di abbassare la temperatura di un grado per risparmiare circa il dieci percento.",
    "Buonasera! La cena è quasi pronta secondo il timer che hai impostato. Mancano ancora cinque minuti. Nel frattempo ho preriscaldato il forno a centottanta gradi come indicato nella ricetta.",
    "Ho controllato tutti i sensori di casa. Tutto è nella norma tranne il sensore di umidità del bagno che segna settantacinque percento. Ti consiglio di accendere la ventola per qualche minuto.",
    "La playlist che hai chiesto contiene venticinque brani per un totale di un'ora e quaranta minuti. Includo artisti italiani contemporanei come hai specificato nelle tue preferenze musicali.",
    "Il tuo volo per Roma di venerdì risulta confermato. Partenza alle otto e trenta da Milano Malpensa, arrivo alle nove e quarantacinque a Roma Fiumicino. Ti conviene partire da casa entro le sei.",
    "Ti informo che il sistema di irrigazione automatica si è attivato stamattina alle sei come programmato. Ha funzionato per venti minuti nella zona anteriore e quindici nella zona posteriore del giardino.",
    "I risultati del monitoraggio notturno indicano che la temperatura in camera è rimasta stabile a venti gradi. L'umidità media è stata del cinquanta percento. La qualità del sonno sembra essere stata buona.",
    "Ho ricevuto una notifica dal sistema di sicurezza. Il sensore della finestra del bagno al piano superiore segnala che è rimasta aperta. Vuoi che te la ricordi quando vai al piano di sopra?",
    "Il report mensile dei consumi è pronto. Hai consumato trecentoventi kilowattora questo mese, in linea con la media degli ultimi tre mesi. Il costo stimato in bolletta sarà di circa settantacinque euro.",
    "La manutenzione programmata della caldaia è prevista per il prossimo mercoledì alle dieci. Ho già confermato l'appuntamento con il tecnico. Ti ricordo di lasciare accesso libero al locale caldaia.",
    "Il tuo ordine online è stato spedito ieri sera e dovrebbe arrivare entro domani. Il corriere è già in possesso del pacco. Ti mando una notifica appena risulta in consegna nella tua zona.",

    # === LUNGHE (200-350 chars) — 10 frasi ===
    "Ecco il rapporto completo sulla qualità dell'aria in casa. Il livello di anidride carbonica in salotto è di quattrocento parti per milione, nella norma. L'umidità è al cinquantacinque percento, ottimale. La temperatura media è di ventuno gradi. Ti segnalo che in camera da letto il livello di CO2 sale a settecento durante la notte. Consiglio di aprire la finestra per dieci minuti prima di dormire.",
    "Ho preparato il piano per la settimana. Lunedì hai il dentista alle undici. Martedì nessun impegno. Mercoledì riunione con il commercialista alle sedici. Giovedì la macchina deve andare in officina per il tagliando. Venerdì sera cena con Marco e Sara. Nel weekend il tempo sarà bello, perfetto per la gita che avevi pianificato al lago.",
    "Riguardo alla tua domanda sulle ricette, ecco cosa posso suggerirti per una cena con ospiti. Come antipasto potresti preparare una bruschetta con pomodorini e basilico. Per primo, una pasta alla norma che è sempre apprezzata. Come secondo, un branzino al forno con patate. Per dolce, una panna cotta ai frutti di bosco. Vuoi che ti legga le dosi per quattro persone?",
    "Le statistiche della tua attività fisica di questa settimana mostrano un netto miglioramento. Hai camminato in media ottomila passi al giorno, superando il tuo obiettivo di settemila. Le calorie bruciate sono state circa duemilaquattrocento. Il sonno medio è stato di sette ore e venti minuti, leggermente sotto le otto ore raccomandate. Il battito cardiaco a riposo è stabile a sessantadue battiti.",
    "Ti faccio un riepilogo delle spese di questo mese. Le bollette ammontano a centocinquanta euro tra luce e gas. La spesa alimentare è stata di quattrocentoventi euro. I trasporti, incluso il carburante e l'abbonamento dei mezzi, sono costati centottanta euro. Le spese per il tempo libero sono state di centotrenta euro. Il totale mensile è di circa ottocentottanta euro.",
    "Il sistema domotico ha rilevato un pattern interessante nei tuoi consumi. Nei giorni feriali il consumo medio è di undici kilowattora, mentre nel weekend sale a quindici. Il picco di consumo si verifica tra le diciannove e le ventuno, corrispondente alla preparazione della cena e all'uso contemporaneo di televisione e lavastoviglie. Ottimizzando questi orari potresti risparmiare il dodici percento.",
    "Ecco il meteo dettagliato per il fine settimana. Sabato mattina cielo sereno con temperatura minima di otto gradi. Nel pomeriggio nuvole sparse e massima di sedici gradi. Domenica prevista pioggia dalla tarda mattinata con accumuli di circa dieci millimetri. Temperature in calo con massima di dodici gradi. Vento da nord moderato. Ti consiglio di pianificare le attività all'aperto per sabato.",
    "Ho completato il backup settimanale di tutti i dispositivi. Il computer principale ha trasferito centoventi gigabyte di nuovi dati. Lo smartphone ha sincronizzato tremila foto e duecento video. Il tablet ha aggiornato i documenti di lavoro. Lo spazio totale utilizzato sul server è di due terabyte su quattro disponibili. Il prossimo backup automatico è programmato per domenica alle tre di notte.",
    "La diagnosi dell'impianto elettrico è completata. Tutti i circuiti sono nella norma tranne quello della cucina che mostra un consumo anomalo. Il frigorifero assorbe il venti percento in più rispetto alle specifiche del produttore. Potrebbe essere necessaria una manutenzione del compressore. Ti consiglio di prenotare un intervento tecnico entro le prossime due settimane per evitare guasti.",
    "Buonasera e benvenuto al riepilogo serale. Oggi hai completato otto dei dieci obiettivi giornalieri. L'attività fisica è stata di seimilacinquecento passi su diecimila previsti. Hai bevuto sei bicchieri d'acqua su otto raccomandati. Il tempo trascorso davanti agli schermi è stato di sette ore. La produttività lavorativa è stata classificata come alta dal tuo calendario. Domani hai tre riunioni.",

    # === MOLTO LUNGHE (350-500 chars) — 8 frasi ===
    "Ecco un riepilogo completo della situazione della casa. Tutte le luci sono spente tranne quella del corridoio che è impostata al dieci percento come luce notturna. Il riscaldamento è in modalità notte con temperatura target di diciotto gradi. Il sistema di allarme è attivato in modalità perimetrale. Le tapparelle sono tutte abbassate. Il frigorifero segnala che la temperatura interna è di quattro gradi, nella norma. La lavastoviglie ha completato il ciclo alle ventidue e trenta. Il consumo energetico totale di oggi è stato di quattordici kilowattora. Il sistema fotovoltaico ha prodotto otto kilowattora durante il giorno. Non ci sono anomalie rilevate dai sensori di fumo e allagamento.",
    "Buongiorno e benvenuto al briefing mattutino. Oggi è martedì venticinque febbraio duemilaventisei. Il meteo prevede una giornata soleggiata con temperature tra i dieci e i diciotto gradi. Nessuna pioggia prevista. La qualità dell'aria esterna è buona con un indice di quarantadue su cento. Per quanto riguarda il traffico, al momento ci sono rallentamenti sulla tangenziale est in direzione centro. Il tragitto verso l'ufficio richiede circa trentacinque minuti, dieci minuti in più del solito. Ti consiglio di partire entro le otto per evitare il picco. Nel tuo calendario di oggi hai tre appuntamenti. Vuoi che te li elenchi nel dettaglio?",
    "Ecco il report completo della settimana per la gestione della casa. Lunedì il consumo è stato di dieci kilowattora, martedì dodici, mercoledì undici, giovedì tredici per via della lavatrice extra, venerdì dieci, sabato quindici e domenica quattordici. Il totale settimanale è di ottantacinque kilowattora. Rispetto alla settimana precedente c'è un aumento del cinque percento, principalmente dovuto alle temperature più basse che hanno richiesto più riscaldamento. Il costo stimato è di circa ventidue euro. Il fotovoltaico ha coperto il trentacinque percento del fabbisogno totale.",
    "Ti presento l'analisi completa del comfort abitativo di questo mese. La temperatura media interna è stata di ventuno virgola tre gradi, perfettamente in linea con il target impostato. L'umidità media si è mantenuta al cinquantadue percento. La qualità dell'aria è stata classificata come buona per il novanta percento del tempo. I momenti critici si sono verificati principalmente durante la cottura dei cibi, quando i livelli di particolato sono saliti temporaneamente. Il sistema di ventilazione meccanica controllata ha funzionato correttamente per tutto il periodo, garantendo un ricambio d'aria adeguato.",
    "Ecco la lista completa della spesa basata su quello che manca in dispensa e in frigorifero. Prodotti freschi: latte, uova, insalata, pomodori, mozzarella, petto di pollo e salmone fresco. Frutta: mele, banane e arance. Dispensa: pasta, riso, olio extravergine, passata di pomodoro, tonno in scatola e biscotti per la colazione. Prodotti per la casa: detersivo per la lavastoviglie, carta igienica e sacchetti per la spazzatura. Ho verificato i prezzi e il totale stimato è di circa settantacinque euro. Vuoi che ordini tutto online con consegna a domicilio per domani mattina?",
    "Ho preparato il piano di viaggio completo per il weekend lungo a Firenze. Venerdì partenza in treno alle otto da Milano Centrale, arrivo a Firenze Santa Maria Novella alle nove e cinquanta. Hotel prenotato in centro, a dieci minuti a piedi dal Duomo. Venerdì pomeriggio visita alla Galleria degli Uffizi, biglietti già acquistati per le quindici. Sabato mattina Ponte Vecchio e Palazzo Pitti, pomeriggio libero per shopping e relax. Domenica mattina visita al Giardino di Boboli, poi pranzo e rientro con il treno delle sedici. Il costo totale del viaggio è stimato in quattrocentocinquanta euro per due persone.",
    "Il sistema di monitoraggio ha generato il report mensile sulla sicurezza della casa. Durante il mese sono stati registrati ventitré eventi di movimento nell'area esterna, tutti classificati come normali: corrieri, vicini di passaggio e animali. Non ci sono stati tentativi di intrusione. Il sistema di allarme è stato attivato correttamente tutte le sere alle ventidue e disattivato alle sette di mattina. La videocamera del cancello ha funzionato senza interruzioni con una disponibilità del cento percento. Le batterie dei sensori wireless sono tutte sopra il sessanta percento. Il prossimo sensore che necessiterà di sostituzione batteria è quello del garage, stimato tra circa due mesi.",
    "Ti leggo il riepilogo completo dell'assemblea di condominio di ieri sera. Erano presenti dodici condomini su diciotto totali, raggiunto il quorum. Primo punto all'ordine del giorno: approvato il bilancio consuntivo dell'anno precedente con un avanzo di milleduecento euro. Secondo punto: deliberata la sostituzione dell'ascensore con un costo di quarantacinquemila euro, da ripartire per millesimi. Terzo punto: confermato l'amministratore per un altro anno con compenso di tremila euro. Quarto punto: approvata la manutenzione straordinaria del tetto per infiltrazioni, preventivo di dodicimila euro. La prossima assemblea è prevista per giugno.",
]

# Frasi di validazione (NON usate nella calibrazione, solo per verifica finale)
VALIDATION_PHRASES = [
    "Tutto bene, grazie.",
    "Ho spento tutte le luci al piano terra e attivato il sistema di allarme notturno.",
    "Ecco le ultime notizie. Il governo ha approvato la nuova legge sul lavoro agile. In borsa, il mercato italiano ha chiuso in rialzo dello zero virgola otto percento. Nello sport, la nazionale di calcio ha vinto due a zero nell'amichevole di ieri sera.",
    "Per la ricetta della carbonara per quattro persone ti servono: trecentoventi grammi di spaghetti, centocinquanta grammi di guanciale, quattro tuorli d'uovo, ottanta grammi di pecorino romano grattugiato e pepe nero macinato al momento. La cottura degli spaghetti richiede circa undici minuti in abbondante acqua salata. Vuoi che ti spieghi il procedimento passo per passo?",
]
