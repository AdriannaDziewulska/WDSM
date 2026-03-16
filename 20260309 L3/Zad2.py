import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import os


# --- MAIN CLASS
class BaseStationSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Symulator Stacji Bazowej - Zadanie 2")

        #PARAMETRY
        self.S = 10
        self.LAMBDA = 1.0
        self.N = 20
        self.SIGMA = 5
        self.MIN = 10
        self.MAX = 100
        self.Q_LIMIT = 5
        self.SIM_TIME = 30
        self.running = False

        # Inicjalizacja interfejsu
        self.setup_ui()

# --- USER INTERFACE
    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        #FORMULARZ Z PARAMETRAMI
        left = ttk.LabelFrame(main_frame, text="Parametry")
        left.grid(row=0, column=0, sticky="nw", padx=5)

        params = [("Liczba kanałów:", "S"), ("Lambda (Poisson):", "LAMBDA"), ("N (Gauss śr.):", "N"),
                  ("Sigma (Gauss odch.):", "SIGMA"), ("Min dł. rozmowy:", "MIN"), ("Maks dł. rozmowy:", "MAX"),
                  ("Długość kolejki:", "Q_LIMIT"), ("Czas symulacji:", "SIM_TIME")]

        self.entries = {}
        for i, (label, var) in enumerate(params):
            ttk.Label(left, text=label).grid(row=i, column=0, sticky="w", padx=5)
            e = ttk.Entry(left, width=10)
            e.insert(0, str(getattr(self, var)))
            e.grid(row=i, column=1, pady=2, padx=5)
            self.entries[var] = e

        self.start_btn = ttk.Button(left, text="START", command=self.start_sim)
        self.start_btn.grid(row=len(params), columnspan=2, pady=10)

        #STATUS KANAŁÓW
        mid = ttk.Frame(main_frame)
        mid.grid(row=0, column=1, padx=10, sticky="n")

        ttk.Label(mid, text="Kanały (Czas obsługi)", font=('Arial', 10, 'bold')).pack()

        self.chan_frame = ttk.Frame(mid)
        self.chan_frame.pack()
        self.chan_widgets = []

        self.stats_lbl = ttk.Label(mid, text="", justify="left")
        self.stats_lbl.pack(pady=10)

        self.time_lbl = ttk.Label(mid, text="Czas symulacji: 0", font=('Arial', 12, 'bold'))
        self.time_lbl.pack()

        #WYKRESY
        right = ttk.Frame(main_frame)
        right.grid(row=0, column=2, padx=10)

        self.fig, self.axs = plt.subplots(3, 1, figsize=(4, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack()

# --- START SIMULATION
    def start_sim(self):
        if not self.running:
            self.running = True

            # Pobranie danych
            self.S = int(self.entries['S'].get())
            self.LAMBDA = float(self.entries['LAMBDA'].get())
            self.N = float(self.entries['N'].get())
            self.SIGMA = float(self.entries['SIGMA'].get())
            self.MIN = float(self.entries['MIN'].get())
            self.MAX = float(self.entries['MAX'].get())
            self.Q_LIMIT = int(self.entries['Q_LIMIT'].get())
            self.SIM_TIME = int(self.entries['SIM_TIME'].get())

            # Reset wizualizacji kanałów
            for w in self.chan_widgets: w.destroy()
            self.chan_widgets = [tk.Label(self.chan_frame, text="Wolny", bg="green", fg="white",
                                          width=12, relief="sunken") for _ in range(self.S)]
            for i, w in enumerate(self.chan_widgets):
                w.grid(row=i // 2, column=i % 2, padx=2, pady=2)

            threading.Thread(target=self.run_logic, daemon=True).start()

# --- OBLICZENIA
    def run_logic(self):
        # 1. Generowanie listy przybyć (Poisson)
        lambdas = []
        sum_l = 0
        while sum_l < self.SIM_TIME * 2:
            li = np.random.exponential(1 / self.LAMBDA)
            lambdas.append(li)
            sum_l += li

        # 2. Tworzenie par (lambda, długość rozmowy mu)
        pairs = []
        for li in lambdas:
            mi = np.clip(np.random.normal(self.N, self.SIGMA), self.MIN, self.MAX)
            pairs.append({'l': li, 'm': int(mi)})

        # Zmienne robocze symulacji
        channels = [0] * self.S
        queue = []
        history = {'rho': [], 'Q': [], 'W': []}
        waiting_times = []
        served = 0

        # Przygotowanie pliku wynikowego
        file_path = os.path.join(os.path.dirname(__file__), "wyniki.txt")

        with open(file_path, "w") as f:
            f.write(f"Parametry symulacji:\nS: {self.S}\nLambda: {self.LAMBDA}\nN: {self.N}\n"
                    f"Sigma: {self.SIGMA}\nMin: {self.MIN}\nMaks: {self.MAX}\n"
                    f"Kolejka: {self.Q_LIMIT}\nCzas: {self.SIM_TIME}\n\n")
            f.write("rho\tQ\tW\n")

            #SYMULACJA
            for t in range(1, self.SIM_TIME + 1):
                # Zwolnienie kanałów
                channels = [max(0, c - 1) for c in channels]

                # Sprawdzenie ile zgłoszeń wpada w tej sekundzie (Krok 3a)
                k = 0
                temp_sum = 0
                while k < len(pairs) and temp_sum + pairs[k]['l'] <= 1:
                    temp_sum += pairs[k]['l']
                    k += 1

                if k == 0 and len(pairs) > 0:
                    pairs[0]['l'] -= 1

                current_arrivals = pairs[:k]
                pairs = pairs[k:]  # Usunięcie obsłużonych z listy

                # Obsługa nowych połączeń
                for p in current_arrivals:
                    if 0 in channels:
                        channels[channels.index(0)] = p['m']
                        served += 1
                        waiting_times.append(0)
                    elif len(queue) < self.Q_LIMIT:
                        queue.append({'m': p['m'], 't': t})

                # Obsługa kolejki
                while 0 in channels and queue:
                    q_item = queue.pop(0)
                    channels[channels.index(0)] = q_item['m']
                    served += 1
                    waiting_times.append(t - q_item['t'])

                # Obliczanie statystyk (rho, Q, W)
                rho = sum(1 for c in channels if c > 0) / self.S
                avg_q = len(queue)
                avg_w = np.mean(waiting_times) if waiting_times else 0

                history['rho'].append(rho)
                history['Q'].append(avg_q)
                history['W'].append(avg_w)

                # Zapis do pliku i odświeżenie UI
                f.write(f"{rho:.4f}\t{avg_q}\t{avg_w:.4f}\n")
                self.root.after(0, self.update_ui, t, channels, served, len(queue), history)

                time.sleep(1.0)  # Czekaj 1 sekundę

        self.running = False

# --- AKTUALIZACJA WYKRESÓW
    def update_ui(self, t, chans, serv, q_len, hist):
        # Aktualizacja czasu i kafelków kanałów
        self.time_lbl.config(text=f"Czas symulacji: {t}")
        for i, val in enumerate(chans):
            if val > 0:
                self.chan_widgets[i].config(text=f"Zajęty: {val}s", bg="red")
            else:
                self.chan_widgets[i].config(text="Wolny", bg="green")

        self.stats_lbl.config(text=f"Obsłużone: {serv}\nKolejka: {q_len}")

        # Odświeżanie wykresów
        for ax in self.axs: ax.clear()
        self.axs[0].plot(hist['rho'], color='b');
        self.axs[0].set_ylabel('rho')
        self.axs[1].plot(hist['Q'], color='r');
        self.axs[1].set_ylabel('Q')
        self.axs[2].plot(hist['W'], color='g');
        self.axs[2].set_ylabel('W')

        self.fig.tight_layout()
        self.canvas.draw()


# --- MAIN
if __name__ == '__main__':
    root = tk.Tk()
    app = BaseStationSimulator(root)
    root.mainloop()