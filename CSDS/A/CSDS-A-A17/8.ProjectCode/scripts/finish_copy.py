"""Update fields of one .docx through a scratch copy (use when Word hangs on the original path because a stale instance holds it).

    python scripts/finish_copy.py "<docx name at the batch root>"
"""
import shutil
import sys
from pathlib import Path

import win32com.client as w

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_common import BATCH  # noqa: E402

name = sys.argv[1]
tmp = Path(r"C:\cs17\finish_tmp.docx")
shutil.copy(BATCH / name, tmp)
word = w.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
d = word.Documents.Open(str(tmp))
d.Repaginate(); d.Fields.Update(); d.Repaginate()
print(name, "pages", d.ComputeStatistics(2), "words", d.ComputeStatistics(0))
d.Save(); d.Close(False); word.Quit()
shutil.copy(tmp, BATCH / name)
