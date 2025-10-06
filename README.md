# Audio-Text Transcriber
Applicazione che permette di trascrivere file audio in file di testo utilizzando Whisper, l'intelligenza
artificiale di OpenAI per la trascrizione audio-testo.

## Motore utilizzato per la trascrizione
**[faster-whisper](https://github.com/SYSTRAN/faster-whisper) by SYSTRAN**\
Un'implementazione di Whisper ma più efficiente.

## Requisiti
- Python 3.9 o superiore

Il modello di faster-whisper è già caricato nel repository, ed è il modello _large-v3_, nella cartella _model_dir_.

## Installazione
Nel repository è presente anche una cartella 'installer', dove al suo interno c'è un file .iss da utilizzare con [InnoSetup](https://jrsoftware.org/isinfo.php) per generare un file .exe.
Anche generando il file .exe, per ora è necessario avere Python sul dispositivo di destinazione.
All'interno è presente un file guida per come creare il .exe, e un README da utilizzare per chi deve usare l'installer.
