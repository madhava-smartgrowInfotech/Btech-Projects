import requests
s = requests.Session()
r = s.post('http://localhost:8000/api/auth/register', json={'name':'Demo Learner','email':'demo_verify2@example.com','password':'secret123','confirm_password':'secret123'})
print('register:', r.status_code)
r = s.put('http://localhost:8000/api/profile', json={'education':"Bachelor Degree",'skill_level':'Beginner','interests':'python, data science','preferred_topics':'Machine Learning','learning_style':'Self-paced','goals':'get a data job','course_preferences':'hands-on','weekly_hours':6,'age_band':'25-34','gender':'F'})
print('profile:', r.status_code)
r = s.get('http://localhost:8000/api/recommendations', params={'top_n':5})
d = r.json()
print('recs:', [x['course']['id'] for x in d['recommendations']])
first = d['recommendations'][0]['course']['id']
s.post('http://localhost:8000/api/interactions', json={'course_id':first,'event_type':'quiz','value':1.0})
s.post('http://localhost:8000/api/interactions', json={'course_id':first,'event_type':'complete','value':1.0})
r2 = s.get('http://localhost:8000/api/recommendations', params={'top_n':5})
print('recs_after:', [x['course']['id'] for x in r2.json()['recommendations']])
print('score_before:', d['recommendations'][0]['score'], 'after:', r2.json()['recommendations'][0]['score'])
for ep in ['/api/learning-path','/api/insights','/api/metrics','/api/fairness','/']:
    rr = s.get('http://localhost:8000'+ep)
    print(ep, rr.status_code, len(rr.text))
