"""
Progetto Trascrittore Audio-Testo
Author: Cristian Palestrini
Ver. 1.0.0

Applicazione che permette di trascrivere file audio in file di testo utilizzando Whisper, l'intelligenza
artificiale di OpenAI per la trascrizione audio-testo.
"""


# import whisper
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog as fd
from multiprocessing.pool import ThreadPool
from faster_whisper import WhisperModel
import time
import gc
import os
import threading

# resolve blur
from ctypes import windll

windll.shcore.SetProcessDpiAwareness(1)

# Set icon in taskbar
try:
    from ctypes import windll  # Only exists on Windows.

    myappid = "pale.transcriber.v1"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


pool = ThreadPool(processes=1)
stop_flag = threading.Event()

file_path = ""
file_name = ""
save_file_path = None
text_result = ""

chunk_duration = 30

model_size = "large-v3"
modal_text = """Funzionamento:
    1. Selezionare il file audio da trascrivere;
    2. (Opzionale) Scegliere dove salvare la trascrizione: non impostandola verrà salvata nella stessa cartella dell'audio;
    3. Cliccare su Trascrivi;
    4. Attendere il completamento: la barra dei progressi diventerà bianca e si caricherà col tempo;
    5. Alla fine viene salvato un file con il testo, che verrà salvato dove è stato specificato precedentemente (vedi punto 2).\n
    
Barra dei menù: funzionalità disponibili
    1. Utility
      - Anteprima Trascrizione
      Visualizza una nuova finestra con l'anteprima della trascrizione. Non è editabile (funzione futura), ma è possibile copiare la trascrizione
      con il pulsante 'Copia testo'.
    
Note:
    - Il programma richiede parecchia memoria, quindi potrebbe rallentare di molto il pc.
    - Il tasto 'Interrompi' non mette in pausa, ma interromperà il processo e salverà un file con quanto trascritto fino a quel punto.
    Farlo ripartire lo farà ricominciare da capo.
    - Se ci sono errori durante la trascrizione, riprovare eseguendo il programma in modalità amministratore
    (tasto destro, 'Apri percorso file', tasto destro sul file .exe e 'Esegui come amministratore')
    """


def main():
    """Main application loop"""
    print("\n--Start Main--")
    # apri finestra
    window.mainloop()

    print("--End Main--\n")
    pool.close()
    pool.join()


def load_file():
    """Gestisce la finestra di selezione file"""
    global file_path
    global file_name
    file_path = fd.askopenfilename(
        filetypes=(("Audio Files", ".wav .m4a .mp3"), ("All Files", "*.*"))
    )
    if file_path.__len__() > 0:
        if Path(file_path).suffix in [".wav", ".m4a", ".mp3"]:
            file_name = Path(file_path).stem
            path_label["text"] = f"File caricato: {file_name}"
            start_button.configure(state="normal")
            print("File caricato")
        else:
            file_name = ""
            print("Errore: formato file non valido")
            messagebox.showerror(
                "Errore: file non valido",
                "File non valido: deve essere un file audio con estensione .wav, .m4a o .mp3",
            )
    else:
        print("Cliccato su Annulla al caricamento del file")
        file_name = ""
        path_label["text"] = f"File caricato: "


def save_file():
    """Gestisce la finestra di selezione file"""
    global file_name
    file_to_save_path = fd.asksaveasfilename(
        filetypes=(("Text File", ".txt"), ("All Files", "*.*")),
        defaultextension=".txt",
        initialfile=f"Trascrizione-{file_name}.txt",
    )
    if file_to_save_path.__len__() > 0:
        global save_file_path
        save_file_path = Path(file_to_save_path)
        save_path_label["text"] = f"Il file verrà salvato qui:\n {save_file_path}"


def start_async_process():
    """Avvia il processo asincrono"""

    log_text.delete("1.0", tk.END)
    global stop_flag
    stop_flag.clear()

    log_text.insert(tk.END, "Prendo il file path...\n")

    progressbar.start()

    if file_path.__len__() > 0:
        # return file name (without extension)
        log_text.insert(tk.END, f"File path preso: {file_path}\n")

        log_text.insert(tk.END, "Avvio processo...\n")

        start_button.configure(state="disabled")

        # avvio un processo separato per la trascrizione
        global pool

        # scommentare per utilizzare la versione classica di OpenAI Whisper
        # pool.apply_async(
        #     transcribe_whisper_standard,
        #     args=(file_path,),
        #     callback=save_to_text,
        # )

        # processo asincrono utilizzando Faster-Whisper
        pool.apply_async(
            transcribe_faster_whisper,
            args=(file_path,),
            callback=save_to_text,
        )

        # trascrivi audio in testo
        # text = transcribe(insert_path_input.get())0
    else:
        log_text.insert(tk.END, "Errore: file non caricato\n")
        progressbar.stop()


# Trascrizione del testo utilizzando la versione classica di OpenAI Whisper
# def transcribe_whisper_standard(file_path):
#     log_text.insert(tk.END, "Loading Whisper model (turbo)...\n")
#     # load model of whisper (turbo)
#     model = whisper.load_model("turbo")
#     # start transcribe
#     log_text.insert(tk.END, "Starting transcribe...\n")
#     progressbar.stop()
#     progressbar.configure(mode="determinate")
#     result = model.transcribe(
#         file_path, verbose=False, language="it", fp16=False, without_timestamps=True
#     )
#     # get file name by path
#     log_text.insert(tk.END, "End transcribe: return text.\n")
#     return result["text"]


def transcribe_faster_whisper(file_path):
    """Trascrizione del testo utilizzando la versione ottimizzata di Whisper, Faster-Whisper (SYSTRAN)"""
    global text_result
    insert_file_button.configure(state="disabled")
    save_file_button.configure(state="disabled")
    start_button.configure(state="disabled")

    # carico il modello di faster-whisper
    try:
        log_text.insert(tk.END, f"Carico Faster-Whisper (modello {model_size})...\n")
        model_path = os.path.join(os.path.dirname(__file__), "model_dir")
        model = WhisperModel(
            model_size_or_path=model_path,
            device="cpu",
            compute_type="int8",
            local_files_only=True,
        )
        log_text.insert(tk.END, "Modello caricato. Inizio trascrizione...\n")

        try:
            # starto progressbar
            text_result = ""
            timestamps = 0.0
            progressbar.stop()
            progressbar.configure(mode="determinate")

            segments, info = model.transcribe(
                audio=file_path,
                language="it",
                without_timestamps=True,
                vad_filter=True,  # Enables voice activity detection for better chunking
                vad_parameters={"threshold": 0.5},  # Adjust sensitivity
                chunk_length=chunk_duration,  # Transcribe in small chunks
            )

            progressbar.configure(maximum=info.duration)
            stop_button.configure(state="normal")

            # tecnicamente è qui che inizia la trascrizione
            # segments diventa un generator
            for s in segments:
                if stop_flag.is_set():
                    print(f"Stop flag is {stop_flag.is_set()}")
                    return text_result
                print(
                    f"[{time.strftime('%H:%M:%S', time.gmtime(s.start))} -> {time.strftime('%H:%M:%S', time.gmtime(s.end))}]: {s.text}"
                )

                new_line = s.text.replace(". ", ".\n")
                text_result = text_result + new_line
                try:
                    text_log_box.insert(tk.END, new_line)
                except:
                    None
                # Update progress bar based on segment duration
                progressbar.step(s.end - timestamps)
                timestamps = s.end

            # Handle silence at the end of the audio
            if timestamps < info.duration:
                progressbar.step(info.duration - timestamps)

            gc.collect()  # Free memory

            log_text.insert(tk.END, "Fine trascrizione: OK\n")

            return text_result

        except Exception as e:
            log_text.insert(tk.END, "Errore durante la trascrizione\n")
            log_text.insert(tk.END, f"{e}\n")
            enable_buttons()
            return None
    except Exception as e:
        log_text.insert(tk.END, "Errore durante il caricamento del modello\n")
        log_text.insert(tk.END, f"{e}\n")
        enable_buttons()
        return None


def save_to_text(result):
    """Saves transcribed text to a file"""
    if result != None:
        if stop_flag.is_set():
            log_text.insert(tk.END, "Trascrizione interrotta.\n")
            enable_buttons()
        else:
            log_text.insert(
                tk.END, "Processo completato: inizio scrittura su file...\n"
            )

        progressbar.stop()
        progressbar.configure(mode="indeterminate", maximum=100)
        progressbar.start()

        global file_path
        global save_file_path

        final_save_path = f"{os.path.dirname(file_path)}/Trascrizione-{file_name}.txt"
        if save_file_path is not None:
            final_save_path = save_file_path

        try:
            # create and open text file for writing
            with open(final_save_path, "w", encoding="utf-8") as text_file:
                # write in file
                text_file.write(result)
                log_text.insert(tk.END, "Fine scrittura su file: OK\n")
                log_text.insert(
                    tk.END, f"Nome file salvato: {Path(final_save_path).stem}\n"
                )
        except Exception as e:
            print(e)
            log_text.insert(tk.END, f"Errore durante la scrittura del file:")
            log_text.insert(tk.END, f"{e}\n")

        enable_buttons()
        progressbar.stop()
        path_label["text"] = "File caricato: "
        save_path_label["text"] = ""
        file_path = ""
        global text_result
        text_result = ""


def stop_async_process():
    """Stops the transcription by setting the stop flag"""
    global stop_flag
    log_text.insert(tk.END, "Interrompo trascrizione...\n")
    stop_button.configure(state="disabled")
    stop_flag.set()


def show_help_modal():
    # Modal Window
    modal_window = tk.Toplevel(window)
    modal_window.title("Tutorial - Come usare l'app")
    modal_window.iconbitmap(os.path.join(os.path.dirname(__file__), "icon.ico"))
    modal_message = tk.Message(modal_window, text=modal_text)
    modal_message.pack(padx=4, pady=4)


def show_text_log_modal():
    # Modal Window
    global text_result
    text_log_window = tk.Toplevel(window)
    text_log_window.title("Anteprima trascrizione")
    text_log_window.iconbitmap(os.path.join(os.path.dirname(__file__), "icon.ico"))

    copy_button = tk.Button(
        text_log_window, text="Copia testo", command=copy_transcription
    )
    copy_button.pack(side="top", anchor="nw", padx=4, pady=4)

    global text_log_box
    text_log_box = tk.Text(text_log_window)
    text_log_box.insert(tk.INSERT, text_result)
    text_log_box.pack(side="left", padx=4, pady=4, fill="both", expand=1)
    text_log_box.bind("<Key>", lambda e: "break")

    scrollb = tk.Scrollbar(text_log_window, command=text_log_box.yview)
    scrollb.pack(side="right", fill="y")
    text_log_box["yscrollcommand"] = scrollb.set


def copy_transcription():
    """Copia la trascrizione fino a quel punto negli appunti del pc"""
    global text_result
    copy_func = tk.Tk()
    copy_func.withdraw()
    copy_func.clipboard_clear()
    copy_func.clipboard_append(text_result)
    copy_func.update()


def enable_buttons():
    insert_file_button.configure(state="normal")
    save_file_button.configure(state="normal")
    start_button.configure(state="normal")
    stop_button.configure(state="disabled")
    progressbar.configure(mode="indeterminate", maximum=100)
    progressbar.stop()


def disable_buttons():
    insert_file_button.configure(state="disabled")
    save_file_button.configure(state="disabled")
    start_button.configure(state="disabled")
    stop_button.configure(state="normal")
    progressbar.start()


###########################################
# TKINTER SETTINGS
###########################################

# window creation
window = tk.Tk()
window.geometry("650x600")
window.title("Trascrittore Audio-Testo")
window.iconbitmap(os.path.join(os.path.dirname(__file__), "icon.ico"))
# window.iconphoto(False, tk.PhotoImage(file='voice-recognition_2604329.png'))

###########################################

# Menu bar
menubar = tk.Menu(window)

# About section
aboutMenu = tk.Menu(menubar, tearoff=0)
aboutMenu.add_command(label="Come usare l'app", command=show_help_modal)
menubar.add_cascade(label="Tutorial", menu=aboutMenu)

logMenu = tk.Menu(menubar, tearoff=0)
logMenu.add_command(label="Anteprima trascrizione", command=show_text_log_modal)
menubar.add_cascade(label="Utility", menu=logMenu)

# Configure menu bar
window.configure(menu=menubar)

###########################################

# Frame to center elements
frame = tk.Frame(window)
frame.pack(pady=20, fill="both")

###########################################

# File selection label
insert_file_label = tk.Label(frame, text="Inserisci file (solo file audio)")
insert_file_label.pack()

button_file_frame = tk.Frame(frame)
button_file_frame.pack(pady=10)

# Load file button
insert_file_button = tk.Button(button_file_frame, text="Carica file", command=load_file)
insert_file_button.pack(side="left", padx=5, pady=10)

# Load file button
save_file_button = tk.Button(
    button_file_frame, text="Scegli dove salvare la trascrizione", command=save_file
)
save_file_button.pack(side="left", padx=5, pady=10)

###########################################

# File path label
save_path_label = tk.Label(frame, justify="center", wraplength=700)
save_path_label.pack(pady=10)

# File path label
path_label = tk.Label(frame, text=f"File caricato: {file_path}", justify="center")
path_label.pack(pady=10)

###########################################

# Frame for start & stop buttons (placed next to each other)
button_frame = tk.Frame(frame)
button_frame.pack(pady=10)

start_button = tk.Button(
    button_frame, text="Trascrivi", command=start_async_process, state="disabled"
)
start_button.pack(side="left", padx=5, pady=10)

stop_button = tk.Button(
    button_frame, text="Interrompi", command=stop_async_process, state="disabled"
)
stop_button.pack(side="left", padx=5, pady=10)

###########################################

# Progress bar
progressbar = ttk.Progressbar(frame, mode="indeterminate")
progressbar.pack(fill="x", padx=10, pady=10)

# Log output text box
log_text_label = tk.Label(frame, text="Log di testo")
log_text_label.pack(pady=5, anchor="w", padx=10)

log_text = tk.Text(frame, height=15)
log_text.pack(padx=10, pady=10, fill="both", expand=1)
log_text.bind("<Key>", lambda e: "break")  # Prevent text editing

###########################################


if __name__ == "__main__":
    main()
