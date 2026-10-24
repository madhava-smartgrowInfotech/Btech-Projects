"""Offline, subject-separated research only. Never changes the live rule engine."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np

FIELDS = ['subject_id','session_id','timestamp_s','ear','roll_deg','quality','label','consent']
FEATURES = ['ear_mean','ear_std','ear_min','closed_fraction','absolute_roll_mean','roll_std']


def extract_windows(path, window_seconds=5.0):
    groups = defaultdict(list)
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError('Required CSV columns: '+','.join(FIELDS))
        for line, row in enumerate(reader, 2):
            if row['consent'].lower() != 'yes':
                raise ValueError(f'Row {line}: explicit consent=yes required')
            if not row['subject_id'].strip() or not row['session_id'].strip():
                raise ValueError(f'Row {line}: subject and session IDs required')
            if row['label'] not in ('normal','possible_impairment'):
                raise ValueError(f'Row {line}: unsupported label')
            try:
                t,ear,roll = (float(row[k]) for k in ('timestamp_s','ear','roll_deg'))
            except ValueError as exc:
                raise ValueError(f'Row {line}: nonnumeric measurement') from exc
            if not np.isfinite([t,ear,roll]).all() or t < 0 or not 0 <= ear <= .65 or abs(roll) > 90:
                raise ValueError(f'Row {line}: invalid measurement range')
            groups[(row['subject_id'],row['session_id'])].append((t,ear,roll,row['quality'],row['label']))
    windows, rejected = [], 0
    for (subject,session), rows in groups.items():
        rows.sort()
        if any(b[0] <= a[0] for a,b in zip(rows,rows[1:])):
            raise ValueError('Duplicate timestamps in a subject/session')
        bins = defaultdict(list)
        for row in rows:
            bins[int((row[0]-rows[0][0])/window_seconds)].append(row)
        for index, segment in bins.items():
            times = np.array([r[0] for r in segment])
            if (len(segment)<20 or times[-1]-times[0] < window_seconds-.5
                    or np.max(np.diff(times)) > .5 or any(r[3]!='Good' for r in segment)
                    or len({r[4] for r in segment}) != 1):
                rejected += 1
                continue
            ear=np.array([r[1] for r in segment]); roll=np.array([r[2] for r in segment])
            dt=np.diff(times)
            x=[float(ear.mean()),float(ear.std()),float(ear.min()),
               float(np.sum(dt*(ear[:-1]<.21))/dt.sum()),float(np.abs(roll).mean()),float(roll.std())]
            windows.append((subject, session, index, x, int(segment[0][4]=='possible_impairment')))
    if not windows:
        raise ValueError('No suitable complete 5-second windows; model not trained')
    return windows, rejected


def metrics(truth, predicted):
    matrix=np.zeros((2,2),dtype=int)
    for a,b in zip(truth,predicted):
        matrix[int(a),int(b)] += 1
    tn,fp,fn,tp=map(int,matrix.ravel())
    ratio=lambda a,b: a/b if b else None
    return {'confusion_matrix':matrix.tolist(), 'precision':ratio(tp,tp+fp),
            'recall':ratio(tp,tp+fn), 'f1':ratio(2*tp,2*tp+fp+fn),
            'false_alarm_rate':ratio(fp,fp+tn),
            'matrix_order':'rows=true, columns=predicted; [normal, possible_impairment]'}


def evaluate(path, output, test_subjects):
    windows, rejected=extract_windows(path)
    subjects={w[0] for w in windows}
    test_subjects=set(test_subjects)
    if not test_subjects or not test_subjects < subjects:
        raise ValueError('Choose existing held-out subjects and leave at least one training subject')
    train=[w for w in windows if w[0] not in test_subjects]
    test=[w for w in windows if w[0] in test_subjects]
    if {w[4] for w in train}!={0,1} or {w[4] for w in test}!={0,1}:
        raise ValueError('Both training and held-out subjects must supply both classes in total')
    x=np.asarray([w[3] for w in train]); y=np.asarray([w[4] for w in train])
    mean=x.mean(axis=0); scale=x.std(axis=0); scale[scale<1e-8]=1
    z=(x-mean)/scale
    centers=np.asarray([z[y==label].mean(axis=0) for label in (0,1)])
    xt=(np.asarray([w[3] for w in test])-mean)/scale
    predicted=((xt[:,None,:]-centers[None,:,:])**2).sum(axis=2).argmin(axis=1)
    report=metrics([w[4] for w in test],predicted)
    report.update({'status':'Offline model trained; live application still uses rules',
                   'classifier':'Standardized nearest centroid (NumPy)', 'features':FEATURES,
                   'train_subjects':sorted(subjects-test_subjects),'test_subjects':sorted(test_subjects),
                   'train_windows':len(train),'test_windows':len(test),'rejected_windows':rejected,
                   'dataset_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                   'limitation':'Exploratory held-out-window metrics, not road-safety validation or an alcohol test.'})
    out=Path(output); out.mkdir(parents=True,exist_ok=True)
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    np.savez(out/'centroid_model.npz',mean=mean,scale=scale,centers=centers)
    with (out/'window_features.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['subject_id','session_id','window_index',*FEATURES,'label','split'])
        for subject,session,index,features,label in windows:
            writer.writerow([subject,session,index,*features,label,'test' if subject in test_subjects else 'train'])
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig=Figure(figsize=(5,4)); FigureCanvasAgg(fig)
    ax=fig.add_subplot(); ax.imshow(report['confusion_matrix'],cmap='Blues')
    for i in range(2):
        for j in range(2):
            ax.text(j,i,str(report['confusion_matrix'][i][j]),ha='center',va='center')
    ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['Normal','Possible'],yticklabels=['Normal','Possible'],
           xlabel='Predicted',ylabel='True',title='Held-out subjects (research only)')
    fig.tight_layout(); fig.savefig(out/'confusion_matrix.png')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv',nargs='?'); parser.add_argument('--test-subjects',nargs='+')
    parser.add_argument('--output',default='research_results')
    args=parser.parse_args()
    if not args.csv:
        print('Model not trained. Supply a consented labeled CSV; see README.md.'); return
    try:
        print(json.dumps(evaluate(args.csv,args.output,args.test_subjects or []),indent=2))
    except (ValueError,OSError) as exc:
        parser.exit(2,f'Model not trained: {exc}\n')

if __name__=='__main__':
    main()
