"""Tkinter desktop application. All widget access stays on the main thread."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from core import Settings, Observation, Decision, RiskEngine, Calibration, simulate, UNKNOWN, WARNING
from storage import Store
from vision import CameraWorker

ROOT=Path(__file__).resolve().parent
SCENARIOS=['Normal','Prolonged eye closure','Missing face','Poor lighting']

class Application:
    def __init__(self, root, data_dir=None):
        self.root=root
        root.title('Smart Rider Impairment Warning System for Two-Wheelers')
        root.geometry('1180x810'); root.minsize(960,720)
        self.store=Store(data_dir or ROOT/'data')
        self.settings, note=self.store.load_settings()
        self.engine=RiskEngine(self.settings)
        self.worker=None; self.simulation=False; self.monitoring=False; self.calibration=None
        self.scenario=tk.StringVar(value=SCENARIOS[0]); self.sound=tk.BooleanVar(value=False)
        self.camera_index=tk.IntVar(value=0)
        self.sim_start=0; self.last_sample=0; self.last_log=0; self.last_key=None
        self.stopping=False; self.closing=False; self.research_busy=False; self.pending_simulation=False; self.research_thread=None
        self.research_results=queue.Queue()
        self.state=tk.StringVar(value=UNKNOWN); self.status=tk.StringVar(value=note)
        self.quality=tk.StringVar(value='No source'); self.features=tk.StringVar(value='No measurements')
        self.reason=tk.StringVar(value='Start camera or select Simulation Mode.')
        self.alert=tk.StringVar(value='Monitoring stopped')
        self.source=tk.StringVar(value='SOURCE: NONE | Rule-based baseline | Model not trained')
        self._build()
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.timer=root.after(50,self.tick)

    def _build(self):
        style=ttk.Style(); style.theme_use('clam')
        style.configure('TButton',padding=7); style.configure('Title.TLabel',font=('Segoe UI',17,'bold'))
        base=ttk.Frame(self.root,padding=14); base.pack(fill='both',expand=True)
        ttk.Label(base,text='Smart Rider | Stationary demonstration',style='Title.TLabel').pack(anchor='w')
        ttk.Label(base,textvariable=self.source).pack(anchor='w',pady=(4,10))
        controls=ttk.Frame(base); controls.pack(fill='x')
        self.buttons={}
        for text,command in [('Start Camera',self.start_camera),('Stop Camera',self.stop_camera),('Calibrate',self.calibrate),
                             ('Start Monitoring',self.start_monitoring),('Stop Monitoring',self.stop_monitoring),
                             ('Simulation Mode',self.start_simulation)]:
            b=ttk.Button(controls,text=text,command=command); b.pack(side='left',padx=2); self.buttons[text]=b
        options=ttk.Frame(base); options.pack(fill='x',pady=7)
        ttk.Label(options,text='Scenario:').pack(side='left')
        combo=ttk.Combobox(options,textvariable=self.scenario,values=SCENARIOS,state='readonly',width=25)
        combo.pack(side='left',padx=5); combo.bind('<<ComboboxSelected>>',self.change_scenario)
        ttk.Checkbutton(options,text='Optional alert sound',variable=self.sound).pack(side='left',padx=10)
        ttk.Label(options,text='Camera index:').pack(side='left')
        ttk.Spinbox(options,from_=0,to=9,textvariable=self.camera_index,width=3).pack(side='left',padx=5)
        for text,command in [('History',self.history),('Export CSV',self.export_csv),('Thresholds',self.thresholds),('Research / Evaluation',self.research)]:
            ttk.Button(options,text=text,command=command).pack(side='left',padx=2)
        body=ttk.Frame(base); body.pack(fill='both',expand=True)
        self.preview=tk.Label(body,text='Camera stopped\nNo video or face images are saved.',bg='#152637',fg='white',font=('Segoe UI',14))
        self.preview.pack(side='left',fill='both',expand=True,padx=(0,14))
        panel=ttk.Frame(body,width=355); panel.pack(side='right',fill='y'); panel.pack_propagate(False)
        ttk.Label(panel,text='Current state',font=('Segoe UI',12,'bold')).pack(anchor='w')
        self.state_label=tk.Label(panel,textvariable=self.state,fg='#825500',font=('Segoe UI',17,'bold'),wraplength=335,justify='left')
        self.state_label.pack(anchor='w',pady=8)
        ttk.Label(panel,textvariable=self.quality,wraplength=335).pack(anchor='w')
        ttk.Label(panel,textvariable=self.features,wraplength=335,justify='left',font=('Consolas',11)).pack(anchor='w',pady=14)
        ttk.Label(panel,textvariable=self.reason,wraplength=335,justify='left').pack(anchor='w',pady=10)
        tk.Label(panel,textvariable=self.alert,wraplength=330,fg='#b42318',justify='left',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=12)
        self.progress=ttk.Progressbar(panel,maximum=100); self.progress.pack(fill='x',pady=10)
        ttk.Label(base,textvariable=self.status,wraplength=1120).pack(anchor='w',pady=8)
        ttk.Label(base,text='Camera cannot confirm alcohol consumption. Normal does not certify fitness to ride.\nMount the camera firmly facing the rider with eyes visible; never obstruct vision or controls.\nWindows laptop prototype: demonstrate while stationary. Not road-ready. Never controls vehicle power, ignition or brakes.',
                  foreground='#5c3a18',justify='left').pack(anchor='w')

    def source_name(self):
        return 'SIMULATION: '+self.scenario.get() if self.simulation else 'LIVE CAMERA'

    def reset_engine(self):
        self.engine=RiskEngine(self.settings); self.last_key=None

    def start_camera(self):
        if self.worker is not None:
            self.status.set('Camera is already active or stopping.'); return
        try:
            index=self.camera_index.get()
            if not 0<=index<=9: raise ValueError()
        except (tk.TclError,ValueError):
            messagebox.showerror('Camera','Camera index must be 0 through 9.'); return
        self.stop_monitoring(); self.simulation=False; self.calibration=None; self.reset_engine()
        self.worker=CameraWorker(index); self.worker.start(); self.last_sample=time.monotonic()
        self.source.set('SOURCE: LIVE CAMERA | Rule-based baseline')
        self.status.set('Opening webcam and landmark model...')

    def stop_camera(self):
        self.stop_monitoring(); self.calibration=None; self.simulation=False
        if self.worker:
            self.worker.stop(); self.stopping=True
            self.status.set('Releasing camera...')
        else:
            self.clear_preview()

    def clear_preview(self):
        self.preview.configure(image='',text='Camera stopped\nNo video or face images are saved.')
        self.preview.image=None
        self.source.set('SOURCE: NONE | Rule-based baseline')
        self.quality.set('No source'); self.features.set('No measurements'); self.progress['value']=0

    def start_simulation(self):
        if self.worker:
            self.stop_camera()
            self.pending_simulation=True
            self.status.set('Releasing webcam and switching to simulation...'); return
        self.stop_monitoring(); self.calibration=None; self.simulation=True
        self.sim_start=time.monotonic(); self.reset_engine()
        self.source.set('SOURCE: SIMULATION | Scripted behavior, not model validation')
        self.preview.configure(image='',text='SIMULATION\n'+self.scenario.get()+'\nScripted measurements; not a camera prediction.')
        self.preview.image=None
        self.status.set('Simulation ready. Select Start Monitoring to record labeled demonstration events.')

    def change_scenario(self,event=None):
        if self.simulation:
            was_monitoring=self.monitoring
            self.start_simulation()
            if was_monitoring: self.start_monitoring()

    def start_monitoring(self):
        if self.calibration:
            self.status.set('Finish calibration before monitoring.'); return
        if self.stopping or not (self.simulation or (self.worker and self.worker.is_alive())):
            self.status.set('Start a camera or Simulation Mode first.'); return
        self.monitoring=True; self.reset_engine(); self.sim_start=time.monotonic()
        self.alert.set('Monitoring active'); self.status.set('Monitoring with explainable rules. No trained research model is used.')

    def stop_monitoring(self):
        if self.monitoring:
            self.store.add(self.source_name(),Decision(UNKNOWN,'Monitoring stopped','Not assessed'))
        self.monitoring=False; self.reset_engine(); self.state.set(UNKNOWN)
        self.reason.set('Monitoring stopped'); self.alert.set('Monitoring stopped')
        self.state_label.configure(fg='#825500')

    def calibrate(self):
        if self.simulation:
            self.status.set('Calibration uses real rider measurements only. Start Camera first.'); return
        if not self.worker or not self.worker.is_alive() or self.stopping:
            self.status.set('Start Camera before calibration.'); return
        self.stop_monitoring(); self.calibration=Calibration(time.monotonic())
        self.progress['value']=0
        self.status.set('Calibration: remain stationary, look forward with eyes naturally open for 8-15 seconds.')

    def consume(self,o,frame=None):
        self.last_sample=time.monotonic()
        self.quality.set(f'Signal quality: {o.quality} | Light {o.brightness:.0f}/255')
        if frame is not None:
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            rgb=cv2.resize(rgb,(600,450))
            data=b'P6\n600 450\n255\n'+rgb.tobytes()
            picture=tk.PhotoImage(data=data,format='PPM')
            self.preview.configure(image=picture,text=''); self.preview.image=picture
            if self.status.get()=='Opening webcam and landmark model...':
                self.status.set('Camera ready. Calibrate while stationary, then Start Monitoring.')
        if self.calibration:
            self.progress['value']=min(100,(o.t-self.calibration.start)/8*100)
            try:
                threshold=self.calibration.add(o)
                self.status.set(f'Calibration: {len(self.calibration.values)} usable / {self.calibration.attempts} frames. Keep eyes open.')
                if threshold is not None:
                    candidate=Settings(**{**asdict(self.settings),'ear_threshold':threshold,'calibrated':True})
                    self.store.save_settings(candidate); self.settings=candidate; self.calibration=None; self.reset_engine()
                    self.status.set(f'Calibration saved: EAR threshold {threshold:.3f}. Start Monitoring when ready.')
            except (ValueError,OSError) as exc:
                self.calibration=None; self.status.set(str(exc))
        if self.monitoring:
            d=self.engine.update(o); self.display_decision(d)
            key=(d.state,d.quality)
            if key!=self.last_key or o.t-self.last_log>=5 or d.alert:
                self.store.add(self.source_name(),d); self.last_key=key; self.last_log=o.t
        else:
            self.features.set(f'EAR: {o.ear:.3f}\nHead roll: {o.roll:.1f} degrees\nThreshold: {self.settings.ear_threshold:.3f}\nMonitoring stopped')

    def display_decision(self,d):
        self.state.set(d.state); self.reason.set(d.reason)
        self.state_label.configure(fg='#b42318' if d.state==WARNING else '#17653a' if d.state=='Normal' else '#825500')
        self.features.set(f'EAR (smoothed): {d.ear:.3f}\nClosure: {d.closure:.1f} s\nBlink rate: {d.blink_rate:.1f}/min*\nClosed fraction: {d.closed_fraction:.0%}\nHead roll: {d.roll:.1f} degrees\nThreshold: {self.settings.ear_threshold:.3f}\n*Rate is unstable in short windows')
        self.alert.set(('SIMULATION: ' if self.simulation else '')+'Warning: stop somewhere safe.\nPossible impairment or drowsiness.' if d.state==WARNING else 'Assessment unavailable: check signal.' if d.state==UNKNOWN else 'No sustained warning. This does not certify safety.')
        if d.alert and self.sound.get():
            self.root.bell()

    def tick(self):
        if self.closing: return
        try:
            now=time.monotonic()
            if self.worker:
                latest=None
                while True:
                    try: latest=self.worker.results.get_nowait()
                    except queue.Empty: break
                if latest and not self.stopping:
                    o,frame,error=latest
                    if error:
                        self.consume(Observation(now,quality=error)); self.stop_camera(); self.status.set(error)
                    else:
                        if now-o.t>.5: o.quality='Stale video'
                        self.consume(o,frame)
                if self.stopping and not self.worker.is_alive():
                    self.worker.join(); self.worker=None; self.stopping=False; self.clear_preview()
                    if self.pending_simulation:
                        self.pending_simulation=False; self.start_simulation()
                elif not self.stopping and now-self.last_sample>1:
                    self.consume(Observation(now,quality='Camera stalled or warming up'))
            elif self.simulation:
                self.consume(simulate(self.scenario.get(),now-self.sim_start,now))
            if self.calibration and now-self.calibration.start>16:
                self.calibration=None; self.status.set('Calibration timed out; previous threshold retained.')
            try:
                result,error=self.research_results.get_nowait()
                self.research_busy=False
                if error: messagebox.showerror('Model not trained',error)
                else: messagebox.showinfo('Offline research evaluation',json.dumps(result,indent=2))
            except queue.Empty: pass
        except Exception as exc:
            self.monitoring=False; self.state.set(UNKNOWN); self.alert.set('Monitoring stopped due to an error')
            self.status.set(f'Application error: {exc}')
        self.timer=self.root.after(80,self.tick)

    def history(self):
        win=tk.Toplevel(self.root); win.title('Event history - UTC timestamps; simulations labeled'); win.geometry('1120x650')
        rows=self.store.recent()
        table=ttk.Treeview(win,columns=('time','source','state','quality','reason'),show='headings',height=10)
        for col,width in [('time',180),('source',150),('state',230),('quality',150),('reason',350)]:
            table.heading(col,text=col.title()); table.column(col,width=width)
        table.pack(fill='x')
        vertical=ttk.Scrollbar(win,orient='vertical',command=table.yview); vertical.pack(side='right',fill='y'); table.configure(yscrollcommand=vertical.set)
        scroll=ttk.Scrollbar(win,orient='horizontal',command=table.xview); scroll.pack(fill='x'); table.configure(xscrollcommand=scroll.set)
        for row in rows: table.insert('', 'end', values=row[1:6])
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        fig=Figure(figsize=(9,3),dpi=100); ax=fig.add_subplot()
        for simulation,color in [(False,'#147d92'),(True,'#be6c14')]:
            subset=[r for r in reversed(rows) if r[2].startswith('SIMULATION')==simulation and r[4]=='Good']
            ax.plot([r[0] for r in subset],[r[6] for r in subset],'.',color=color,label='Simulation' if simulation else 'Live')
        ax.set(xlabel='Logged event ID (transitions and 5-second snapshots)',ylabel='EAR',title='Recent event measurements; not a continuous recording')
        ax.legend(); fig.tight_layout()
        canvas=FigureCanvasTkAgg(fig,master=win); canvas.draw(); canvas.get_tk_widget().pack(fill='both',expand=True)
        win.canvas=canvas

    def export_csv(self):
        path=filedialog.asksaveasfilename(title='Export numeric event history',defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if path:
            try: self.store.export(path); self.status.set(f'Exported history to {path}')
            except OSError as exc: messagebox.showerror('Export failed',str(exc))

    def thresholds(self):
        win=tk.Toplevel(self.root); win.title('Rule thresholds (experimental; see README)')
        entries={}
        for i,(key,value) in enumerate(asdict(self.settings).items()):
            if key=='calibrated': continue
            ttk.Label(win,text=key.replace('_',' ')).grid(row=i,column=0,padx=10,pady=6,sticky='w')
            variable=tk.StringVar(value=str(value)); entries[key]=variable
            ttk.Entry(win,textvariable=variable).grid(row=i,column=1,padx=10)
        def save():
            try:
                settings=Settings(**{k:float(v.get()) for k,v in entries.items()},calibrated=False).validate()
                self.store.save_settings(settings); self.stop_monitoring(); self.calibration=None
                self.settings=settings; self.reset_engine(); win.destroy()
                self.status.set('Thresholds saved. Monitoring stopped; restart to use the new settings.')
            except (ValueError,OSError) as exc: messagebox.showerror('Invalid settings',str(exc),parent=win)
        ttk.Button(win,text='Save thresholds',command=save).grid(row=7,columnspan=2,pady=12)

    def research(self):
        win=tk.Toplevel(self.root); win.title('Research and Model Evaluation'); win.geometry('710x490')
        report=ROOT/'research_results'/'report.json'
        text='Model not trained' if not report.exists() else 'Offline evaluation report available (live app still uses rules).'
        ttk.Label(win,text=text,font=('Segoe UI',14,'bold')).pack(anchor='w',padx=15,pady=15)
        ttk.Label(win,text='Use only consented, genuinely labeled frame measurements. No dataset is bundled.\nCSV columns:\nsubject_id,session_id,timestamp_s,ear,roll_deg,quality,label,consent\n\nLabels: normal or possible_impairment. Consent: yes. Quality: Good.\n5-second windows with at least 20 samples; maximum gap 0.5 s.\nMixed-label or unreliable windows are excluded. Both splits need both classes.\nHeld-out subject IDs must never appear in training. Read README for details.\nThis research model is never used to decide live warnings.',wraplength=670,justify='left').pack(anchor='w',padx=15)
        ttk.Label(win,text='Held-out subject IDs (comma-separated):').pack(anchor='w',padx=15,pady=(15,2))
        subjects=ttk.Entry(win,width=60); subjects.pack(anchor='w',padx=15)
        def run():
            if self.research_busy: messagebox.showinfo('Research','Evaluation already running.'); return
            ids=[v.strip() for v in subjects.get().split(',') if v.strip()]
            if not ids: messagebox.showerror('Research','Enter held-out subject IDs first.'); return
            path=filedialog.askopenfilename(title='Select consented frame-measurement CSV',filetypes=[('CSV','*.csv')])
            if not path: return
            self.research_busy=True
            def work():
                try:
                    from research import evaluate
                    self.research_results.put((evaluate(path,ROOT/'research_results',ids),None))
                except Exception as exc: self.research_results.put((None,str(exc)))
            self.research_thread=threading.Thread(target=work,daemon=True); self.research_thread.start()
            self.status.set('Offline evaluation running. Live warning rules remain active.'); win.destroy()
        ttk.Button(win,text='Choose CSV and train/evaluate offline',command=run).pack(anchor='w',padx=15,pady=15)
        if report.exists():
            def show_report():
                try: messagebox.showinfo('Saved research report',report.read_text(encoding='utf-8'))
                except OSError as exc: messagebox.showerror('Report',str(exc))
            ttk.Button(win,text='View saved report',command=show_report).pack(anchor='w',padx=15)

    def close(self):
        if self.closing: return
        self.stop_monitoring(); self.closing=True
        self.root.after_cancel(self.timer)
        if self.worker: self.worker.stop()
        self.status.set('Closing: waiting for webcam release...')
        self._finish_close()

    def _finish_close(self):
        if self.worker and self.worker.is_alive():
            self.root.after(100,self._finish_close); return
        if self.research_thread and self.research_thread.is_alive():
            self.root.after(100,self._finish_close); return
        if self.worker: self.worker.join()
        self.store.close(); self.root.destroy()


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--simulation',action='store_true')
    args=parser.parse_args()
    root=tk.Tk(); app=Application(root)
    if args.simulation: app.start_simulation(); app.start_monitoring()
    root.mainloop()

if __name__=='__main__':
    main()
