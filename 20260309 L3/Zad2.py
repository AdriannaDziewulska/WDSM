import threading
from cProfile import label
from dataclasses import fields
from tkinter import ttk

import numpy as np
from PIL._tkinter_finder import tk
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class BaseStationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Stacja bazowa")
#Parametry
        self.S=10
        self.LAMBDA=1.0
        self.N_AVG=20
        self.SIGMA=5
        self.MIN_LENGTH=10
        self.MAX_LENGTH=30
        self.SIM_TIME_LIMIT=30
        self.Q_LIMIT=10

        self.running=False
        self.channels=[0]*self.S
        self.history={'rho':[], 'Q':[], 'W':[]}
        self.queue=[]
        self.total_served=0
        self.waiting_times=[]

        self.setup_ui()

def setup_ui(self):
    param_frame=ttk.LabelFrame(self.root,text="Parametry")
    param_frame.grid(row=0,column=0,padx=10,pady=10,sticky="ns")

    fields=[
        ("Liczba kanałów: ", "S"),
        ("Długość kolejki: ", "Q_LIMIT"),
        ("Natężenie - Lambda: ", "LAMBDA"),
        ("Średnia rozmowa - N: ", "N_AVG"),
        ("Odchylenie - Sigma: ", "SIGMA"),
        ("Min długość: ", "MIN_LENGTH"),
        ("Max długość: ", "MAX_LENGTH"),
        ("Czas symulacji: ", "SIM_TIME_LIMIT")
    ]

    self.entries={}
    for i, (label, var) in enumerate(fields):
        ttk.Label(param_frame,text=label).grid(row=i,column=0,sticky="w")
        entry=ttk.Entry(param_frame,width=10)
        entry.insert(0, str(getattr(self, var)))
        entry.grid(row=i,column=1,pady=2)
        self.entries[var]=entry

    self.start_btn=ttk.Button(param_frame,text="Start",command=self.start_simulation)
    self.start_btn.grid(row=0,columnspan=2,pady=10)

    mid_frame=ttk.Frame(self.root)
    mid_frame.grid(row=0,column=1,padx=10,pady=10)

    self.channel_btns=[]
    for i in range(self.S):
        btn=tk.Button(mid_frame, text="Wolny", bg="green", fg="white", width=10, height=2)
        btn.grid(row=i//2,column=i%2,padx=2,pady=2)
        self.channel_btns.append(btn)

    self.stats_lbl=ttk.Label(mid_frame,text="Kolejka: 0\nObsłużone: 0\nCzas: 0", justify="left")
    self.stats_lbl.grid(row=6,column=0,columnspan=2,pady=10)

    self.fig, self.axs=plt.subplots(3,1,figsize=(4,6))
    self.canvas=FigureCanvasTkAgg(self.fig, master=self.root)
    self.canvas.get_tk_widget().grid(row=0, column=2, padx=10)

def update_ui(self, t):
    for i in  range(len(self.channels)):
        val=self.channels[i]
        if val>0:
            self.channel_btns[i].config(text="Zajęty: {val}s", bg="red")
        else:
            self.channel_btns[i].config(text="Wolny: ", bg="green")

    self.stats_lbl.config(
        text=f"Kolejka: {len(self.queue)}/{self.Q_LIMIT}\nObsłużone: {self.total_served}\nCzas symulacji: {t} / {self.SIM_TIME_LIMIT}")

    for ax in self.axs: ax.clear()
    self.axs[0].plot(self.history['rho'],color='blue')
    self.axs[0].set_ylabel('Ro')
    self.axs[1].plot(self.history['Q'],color='red')
    self.axs[1].set_ylabel('Q')
    self.axs[2].plot(self.history['W'],color='green')
    self.axs[2].set_ylabel('W')
    self.fig.tight_layout()
    self.canvas.draw()

def start_simulation(self):
    if not self.running:
        self.running = True
        self.S=int(self.entries['S'].get())
        self.LAMBDA=float(self.entries['LAMBDA'].get())
        self.SIM_TIME_LIMIT=int(self.entries['SIM_TIME_LIMIT'].get())

        self.channels=[0]*self.S
        self.history={'rho':[], 'Q':[], 'W':[]}
        self.queue=[]
        self.waiting_times=[]

        thread=threading.Thread(target=self.run_logic)
        thread.daemon=True
        thread.start()

def run_logic(self):
    arrivals=[]
    curr=0
    while curr<self.SIM_TIME_LIMIT:
        curr+=np.random.exponential(1/self.LAMBDA)
        if curr<self.SIM_TIME_LIMIT:
            dur=np.clip(np.random.normal(self.N_AVG, self.SIGMA), self.MIN_LENGHT, self.MAX_LENGHT)
            arrivals.append((curr, int(dur)))
    arr_idx=0
    for t in range(self.SIM_TIME_LIMIT+1):
        if not self.running: break
        self.channels=[max(0,c-1) for c in self.channels]
        while arr_idx<len(arrivals) and int(arrivals[arr_idx][0])==t:
            duration=arrivals[arr_idx][1]
            if 0 in self.channels:
                self.channels[self.channels.index(0)]=duration
                self.total_served+=1
                self.waiting_times.append(0)
            elif len(self.queue)<self.Q_LIMIT:
                self.queue.append({'d': duration, 't': t})
            arr_idx+=1
        while 0 in self.channels and self.queue:
            call=self.queue.pop(0)
            self.channels[self.channels.index(0)]=call['d']
            self.total_served+=1
            self.waiting_times.append(t-call['t'])

        rho=sum(1 for c in self.channels if c>0)/self.S
        self.history['rho'].append(rho)