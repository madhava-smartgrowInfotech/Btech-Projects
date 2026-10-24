"""Synthetic unit fixtures verify software behavior, never research accuracy."""
import csv
import math
from pathlib import Path
import tempfile
import unittest
import numpy as np
from core import *
from storage import Store
from research import extract_windows, evaluate, metrics, FIELDS

class Features(unittest.TestCase):
    def test_ear_known_geometry(self):
        eye=[[0,0],[1,1],[3,1],[4,0],[3,-1],[1,-1]]
        self.assertAlmostEqual(eye_aspect_ratio(eye),.5)
        self.assertAlmostEqual(eye_aspect_ratio(np.asarray(eye)*7),.5)

    def test_degenerate_eye_rejected(self):
        with self.assertRaises(ValueError): eye_aspect_ratio(np.zeros((6,2)))
        with self.assertRaises(ValueError): eye_aspect_ratio(np.full((6,2),np.nan))

    def test_roll_units(self):
        self.assertAlmostEqual(head_roll([0,0],[1,1]),45)
        self.assertAlmostEqual(head_roll([0,0],[1,0]),0)

class Rules(unittest.TestCase):
    def stream(self, engine, ear=.30, start=0, seconds=5, quality='Good', roll=0):
        return [engine.update(Observation(round(start+i*.1,6),ear,roll,quality)) for i in range(int(seconds*10))]

    def test_normal_and_warmup(self):
        d=self.stream(RiskEngine())
        self.assertEqual(d[0].state,UNKNOWN); self.assertEqual(d[-1].state,NORMAL)

    def test_bad_frame_cannot_warn(self):
        e=RiskEngine(); self.stream(e)
        d=e.update(Observation(5,.01,0,'Good'))
        self.assertEqual(d.state,NORMAL)

    def test_sustained_closure_and_cooldown(self):
        e=RiskEngine(); self.stream(e)
        d=self.stream(e,.1,5,6)
        self.assertEqual(d[5].state,NORMAL)
        self.assertEqual(d[-1].state,WARNING)
        self.assertEqual(sum(x.alert for x in d),1)

    def test_unreliable_conditions(self):
        for quality in ['No face','Poor lighting','Hidden eyes','Unstable video']:
            e=RiskEngine(); self.stream(e,.1)
            self.assertEqual(e.update(Observation(5,.1,0,quality)).state,UNKNOWN)
            self.assertEqual(e.update(Observation(5.1,.3,0,'Good')).state,UNKNOWN)

    def test_timing_gap_and_nan(self):
        e=RiskEngine(); self.stream(e)
        self.assertEqual(e.update(Observation(8,.1,0,'Good')).state,UNKNOWN)
        self.assertEqual(e.update(Observation(8.1,math.nan,0,'Good')).state,UNKNOWN)

    def test_blink_rate_sixty_second_denominator(self):
        e=RiskEngine()
        for i in range(601):
            t=i/10; ear=.1 if 2<t%5<2.4 else .3
            d=e.update(Observation(t,ear,0,'Good'))
        self.assertAlmostEqual(d.blink_rate,12,delta=1)
        self.assertEqual(d.state,NORMAL)

    def test_head_tilt_requires_low_ear(self):
        e=RiskEngine(); d=self.stream(e,roll=35)
        self.assertEqual(d[-1].state,NORMAL)
        d=self.stream(e,.19,5,4,roll=35)
        self.assertEqual(d[-1].state,WARNING)

    def test_cooldown_survives_signal_loss(self):
        e=RiskEngine(); d=self.stream(e,.1,0,4)
        self.assertTrue(any(x.alert for x in d))
        e.update(Observation(4,quality='No face'))
        d=self.stream(e,.1,4.1,4)
        self.assertFalse(any(x.alert for x in d))

    def test_simulation_scenarios(self):
        for scenario,expected in [('Normal',NORMAL),('Prolonged eye closure',WARNING),('Missing face',UNKNOWN),('Poor lighting',UNKNOWN)]:
            e=RiskEngine()
            for i in range(100): d=e.update(simulate(scenario,i*.1,i*.1))
            self.assertEqual(d.state,expected)

    def test_settings_bounds(self):
        with self.assertRaises(ValueError): Settings(ear_threshold=math.nan).validate()
        with self.assertRaises(ValueError): Settings(cooldown_seconds=0).validate()

class CalibrationTests(unittest.TestCase):
    def test_calibration_success(self):
        c=Calibration(0); value=None
        for i in range(82):
            value=c.add(Observation(i*.1,.3,0,'Good'))
            if value is not None: break
        self.assertAlmostEqual(value,.216)

    def test_calibration_rejects_bad_quality(self):
        c=Calibration(0)
        with self.assertRaises(ValueError):
            for i in range(152): c.add(Observation(i*.1,.3,0,'Poor lighting'))

class Persistence(unittest.TestCase):
    def test_history_export_and_settings(self):
        with tempfile.TemporaryDirectory() as path:
            store=Store(path)
            store.add('SIMULATION: Normal',Decision(NORMAL,'fixture','Good',ear=.3))
            target=Path(path)/'events.csv'; store.export(target)
            with target.open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
            self.assertEqual(rows[0]['source'],'SIMULATION: Normal')
            store.save_settings(Settings(ear_threshold=.22))
            self.assertEqual(store.load_settings()[0].ear_threshold,.22)
            (Path(path)/'settings.json').write_text('{broken')
            self.assertEqual(store.load_settings()[0].ear_threshold,.21)
            store.close()

class ResearchTests(unittest.TestCase):
    def fixture(self,path,consent='yes'):
        # Software-only fixture. Temporary, explicitly not a research dataset.
        with Path(path).open('w',newline='') as f:
            w=csv.writer(f); w.writerow(FIELDS)
            for subject in ['train_person','test_person']:
                for label,ear in [('normal',.3),('possible_impairment',.1)]:
                    for i in range(50): w.writerow([subject,label,i*.1,ear,0,'Good',label,consent])

    def test_subject_separation_and_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.csv'; self.fixture(path)
            report=evaluate(path,Path(directory)/'out',['test_person'])
            self.assertFalse(set(report['train_subjects']) & set(report['test_subjects']))
            self.assertEqual(report['train_windows'],2)
            self.assertTrue((Path(directory)/'out'/'confusion_matrix.png').exists())

    def test_consent_and_empty_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.csv'; self.fixture(path,'no')
            with self.assertRaises(ValueError): extract_windows(path)
            path.write_text(','.join(FIELDS)+'\n')
            with self.assertRaises(ValueError): extract_windows(path)

    def test_metrics_known_counts(self):
        m=metrics([0,0,1,1],[0,1,1,1])
        self.assertEqual(m['confusion_matrix'],[[1,1],[0,2]])
        self.assertAlmostEqual(m['precision'],2/3)
        self.assertEqual(m['false_alarm_rate'],.5)
        self.assertIsNone(metrics([1],[1])['false_alarm_rate'])

    def test_split_rejects_missing_subject(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.csv'; self.fixture(path)
            with self.assertRaises(ValueError): evaluate(path,directory,['unknown'])

if __name__=='__main__': unittest.main()
