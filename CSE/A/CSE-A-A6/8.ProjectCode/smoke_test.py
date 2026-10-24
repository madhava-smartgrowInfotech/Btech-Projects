"""Tk integration checks with temporary storage; does not validate rider detection."""
from pathlib import Path
import tempfile
import time
import tkinter as tk
from unittest.mock import patch
import numpy as np
from app import Application
from core import Observation, WARNING

def run():
    with tempfile.TemporaryDirectory() as directory:
        root=tk.Tk(); root.withdraw(); app=Application(root,directory)
        app.start_monitoring(); assert not app.monitoring
        app.buttons['Simulation Mode'].invoke(); app.buttons['Start Monitoring'].invoke()
        assert app.monitoring and app.simulation
        start=time.monotonic()
        for i in range(90):
            app.consume(Observation(start+i*.1,.10,0,'Good',100,200))
        assert app.state.get()==WARNING
        app.consume(Observation(start+9,quality='No face'))
        assert app.state.get()=='Unable to assess'
        app.consume(Observation(start+9.1,.3,0,'Good'),np.zeros((480,640,3),dtype=np.uint8))
        assert app.preview.image is not None
        app.calibrate(); assert app.calibration is None
        app.history(); app.thresholds(); app.research(); root.update()
        for window in root.winfo_children():
            if isinstance(window,tk.Toplevel):
                for widget in window.winfo_children():
                    if widget.winfo_class()=='TButton' and widget.cget('text')=='Save thresholds':
                        widget.invoke()
                        break
        assert (Path(directory)/'settings.json').exists()
        target=Path(directory)/'export.csv'
        with patch('app.filedialog.asksaveasfilename',return_value=str(target)):
            app.export_csv()
        assert target.exists()
        app.buttons['Stop Monitoring'].invoke(); assert not app.monitoring
        app.buttons['Stop Camera'].invoke(); assert not app.simulation
        app.close()
    print('PASS: Tk preview, simulation, warnings, history/chart, thresholds, research, export, stop and clean exit')

if __name__=='__main__': run()
