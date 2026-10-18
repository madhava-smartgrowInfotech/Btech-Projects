from streamlit.testing.v1 import AppTest
at = AppTest.from_file("../app.py", default_timeout=180)
at.run()
print("overview exc:", [e.value for e in at.exception])
for p in ["🔍 PR Review","💬 Codebase Assistant","🧪 Model Lab","🕘 History","ℹ️ About"]:
    at.session_state["nav"]=p
    at.run()
    print(p.encode('ascii','ignore').decode(), "exc:", [e.value for e in at.exception][:2], "err:", [e.value for e in at.error][:2])
# run demo review
at.session_state["nav"]="🔍 PR Review"; at.run()
btn=[b for b in at.button if "Run multi-agent" in b.label][0]
btn.click(); at.run()
print("review exc:", [e.value for e in at.exception][:3], "err:", [e.value for e in at.error][:3])
print("verdict:", at.session_state["review"]["verdict"], at.session_state["review"]["score"])
# codebase
at.session_state["nav"]="💬 Codebase Assistant"; at.run()
[b for b in at.button if "Index repository" in b.label][0].click(); at.run()
print("index exc:", [e.value for e in at.exception][:3], at.session_state["index"] is not None)
