"""Indian UPI-scam SMS set (English, Hindi, Telugu) - hand-written templates + seeded expansion.

Every template below was written for UPI Guardian. Slots such as {bank} or {link} are filled
from fictional values (no real bank, company or website names) with a fixed random seed, so
running this script always produces exactly the same CSV.

Output: data/raw/upi_scam_sms/upi_scam_sms.csv
Columns: id, text, label (1 = scam, 0 = legitimate), category, language (en|hi|te),
         script (native|latin), template_id, kind (sms|collect_note)

Run: venv\\Scripts\\python scripts\\generate_scam_sms.py
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 2026
VARIANTS = 6
NOTE_VARIANTS = 4
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "upi_scam_sms" / "upi_scam_sms.csv"

SLOTS = {
    "bank": ["Bharat Union Bank", "Sahyadri Bank", "Kaveri Gramin Bank", "Deccan Co-op Bank", "Narmada Bank", "Godavari Bank"],
    "bnk": ["BUNB", "SAHB", "KAVB", "DCCB", "NRMB", "GODB"],
    "wallet": ["RupeeGo", "SwiftPay", "PayNest"],
    "store": ["ShopKart", "DailyBasket", "MegaMart Online", "StyleHub"],
    "power": ["State Power Distribution", "City Electricity Board", "Power Supply Office"],
    "courier": ["Swift Courier", "FastTrack Parcel", "Express Cargo"],
    "company": ["Global Tasks Pvt Ltd", "StarWork Online", "Digital Hire India"],
    "link": [
        "http://kyc-verify-now.top/a{n}",
        "https://upi-refund-help.xyz/r{n}",
        "http://secure-bank-update.click/{n}",
        "https://reward-claim.online/c{n}",
        "http://acct-help-india.site/{n}",
        "https://bit-link.cc/{n}",
        "http://parcel-track-in.info/t{n}",
    ],
    "good_link": ["https://www.bharatunionbank.example/app", "https://sahyadribank.example/help"],
    "upi": ["kyc.helpdesk@upg", "refund.desk@upg", "luckydraw.winner@upg", "cashback.offer@upg", "support.verify@upg", "claim.reward@upg", "tasks.pay@upg"],
    "name": ["Rahul", "Priya", "Suresh", "Anita", "Kiran", "Ramesh", "Lakshmi", "Arjun", "Divya", "Srinivas", "Fatima", "Imran"],
    "relation_en": ["Mom", "Dad", "Uncle", "Aunty", "Bro"],
    "amount_small": ["1", "10", "49", "99", "199", "499"],
    "amount": ["1,499", "2,999", "4,999", "5,000", "7,500", "9,999", "12,000"],
    "amount_big": ["25,000", "50,000", "1,00,000", "2,50,000", "5,00,000", "10,00,000"],
    "time_en": ["tonight 9:30 PM", "today 10 PM", "within 2 hours", "in 30 minutes"],
    "time_hi": ["आज रात 9:30 बजे", "आज रात 10 बजे", "2 घंटे में", "30 मिनट में"],
    "time_te": ["ఈ రాత్రి 9:30కి", "ఈ రోజు రాత్రి 10 గంటలకు", "2 గంటల్లో", "30 నిమిషాల్లో"],
    "time_lat": ["aaj raat 9:30", "aaj raat 10 baje", "2 ghante mein", "30 min mein"],
    "time_telat": ["ee raatri 9:30 ki", "ee roju raatri 10 ki", "2 gantallo", "30 nimishallo"],
}


def _phone(rng: random.Random) -> str:
    return f"{rng.choice('6789')}{rng.randint(100000000, 999999999)}"


# (category, language, script, text). Scam templates first, then legitimate ones.
SCAM = [
    # ---- fake KYC / account block -------------------------------------------------
    ("kyc_fraud", "en", "native", "Dear customer, your {bank} KYC expires today. Your account will be blocked. Update KYC now: {link}"),
    ("kyc_fraud", "en", "native", "ALERT: Your {bnk} account is SUSPENDED due to pending KYC. Click {link} and verify within 24 hrs to avoid permanent block."),
    ("kyc_fraud", "en", "native", "Your UPI ID will be deactivated today. Complete PAN-KYC update immediately at {link} or call {phone}."),
    ("kyc_fraud", "hi", "native", "प्रिय ग्राहक, आपका {bank} KYC आज समाप्त हो रहा है। खाता बंद कर दिया जाएगा। तुरंत KYC अपडेट करें: {link}"),
    ("kyc_fraud", "hi", "native", "आपका UPI खाता ब्लॉक होने वाला है। KYC सत्यापन के लिए अभी इस लिंक पर क्लिक करें {link} या {phone} पर कॉल करें।"),
    ("kyc_fraud", "hi", "latin", "Aapka {bnk} account aaj band ho jayega. KYC update karne ke liye turant link par click karein {link}"),
    ("kyc_fraud", "te", "native", "ప్రియమైన కస్టమర్, మీ {bank} KYC ఈ రోజు ముగుస్తుంది. మీ ఖాతా బ్లాక్ అవుతుంది. వెంటనే KYC అప్‌డేట్ చేయండి: {link}"),
    ("kyc_fraud", "te", "native", "మీ UPI ఖాతా నిలిపివేయబడుతుంది. KYC ధృవీకరణ కోసం ఈ లింక్ క్లిక్ చేయండి {link} లేదా {phone} కి కాల్ చేయండి."),
    ("kyc_fraud", "te", "latin", "Mee {bnk} account ee roju block avutundi. KYC update cheyyadaniki ventane ee link click cheyandi {link}"),
    # ---- refund / cashback -------------------------------------------------------
    ("refund_scam", "en", "native", "Your refund of Rs {amount} from {store} is ready. Approve the UPI request from {upi} and enter your PIN to receive it."),
    ("refund_scam", "en", "native", "Congrats! Cashback of Rs {amount} credited to your {wallet} wallet. To withdraw, scan the QR at {link} and enter UPI PIN."),
    ("refund_scam", "en", "native", "Order cancelled. Rs {amount} refund pending. Our executive will send a collect request, please accept to get your money back."),
    ("refund_scam", "hi", "native", "{store} से आपका ₹{amount} का रिफंड तैयार है। पैसा पाने के लिए {upi} से आए अनुरोध को स्वीकार करें और PIN डालें।"),
    ("refund_scam", "hi", "native", "बधाई हो! आपके {wallet} वॉलेट में ₹{amount} कैशबैक आया है। पैसे निकालने के लिए {link} पर QR स्कैन करके PIN डालें।"),
    ("refund_scam", "hi", "latin", "Aapka Rs {amount} refund pending hai. Paisa wapas paane ke liye request accept karke UPI PIN daalein. {upi}"),
    ("refund_scam", "te", "native", "{store} నుండి మీ ₹{amount} రీఫండ్ సిద్ధంగా ఉంది. డబ్బు పొందడానికి {upi} నుండి వచ్చిన అభ్యర్థనను ఆమోదించి PIN ఎంటర్ చేయండి."),
    ("refund_scam", "te", "native", "అభినందనలు! మీ {wallet} వాలెట్‌లో ₹{amount} క్యాష్‌బ్యాక్ వచ్చింది. డబ్బు తీసుకోవడానికి {link} లో QR స్కాన్ చేసి PIN ఇవ్వండి."),
    ("refund_scam", "te", "latin", "Mee Rs {amount} refund pending lo undi. Dabbu raavadaniki request accept chesi UPI PIN enter cheyandi {upi}"),
    # ---- lottery / prize --------------------------------------------------------
    ("lottery_prize", "en", "native", "Congratulations! Your number won Rs {amount_big} in the Mega Lucky Draw. Pay processing fee of Rs {amount} to {upi} to claim now."),
    ("lottery_prize", "en", "native", "You are selected for a Rs {amount_big} reward! Claim before {time_en}: {link}"),
    ("lottery_prize", "en", "native", "WINNER! Your mobile number has won a car + Rs {amount_big}. Call {phone} to claim your prize today."),
    ("lottery_prize", "hi", "native", "बधाई हो! आपने मेगा लकी ड्रॉ में ₹{amount_big} जीते हैं। इनाम पाने के लिए ₹{amount} प्रोसेसिंग फीस {upi} पर भेजें।"),
    ("lottery_prize", "hi", "native", "आपका नंबर ₹{amount_big} इनाम के लिए चुना गया है। {time_hi} से पहले दावा करें: {link}"),
    ("lottery_prize", "hi", "latin", "Badhai ho! Aapne Rs {amount_big} ka inaam jeeta hai. Claim karne ke liye {phone} par call karein."),
    ("lottery_prize", "te", "native", "అభినందనలు! మెగా లక్కీ డ్రాలో మీరు ₹{amount_big} గెలుచుకున్నారు. బహుమతి పొందడానికి ₹{amount} ప్రాసెసింగ్ ఫీజు {upi} కి పంపండి."),
    ("lottery_prize", "te", "native", "మీ నంబర్ ₹{amount_big} బహుమతికి ఎంపికైంది. {time_te} లోపు క్లెయిమ్ చేయండి: {link}"),
    ("lottery_prize", "te", "latin", "Congratulations! Meeru Rs {amount_big} lottery gelicharu. Prize kosam {phone} ki call cheyandi."),
    # ---- job / task --------------------------------------------------------------
    ("job_task", "en", "native", "Part-time job: earn Rs 3,000-8,000 daily by liking videos. Join now {link}. Registration fee Rs {amount_small} only."),
    ("job_task", "en", "native", "Hi, I am HR from {company}. Work from home, simple review tasks, daily payment. Pay Rs {amount} deposit to {upi} to unlock tasks."),
    ("job_task", "en", "native", "Your task commission is ready. Complete one prepaid task of Rs {amount} to withdraw Rs {amount_big}."),
    ("job_task", "hi", "native", "पार्ट टाइम नौकरी: वीडियो लाइक करके रोज़ ₹3000-8000 कमाएँ। अभी जुड़ें {link}। रजिस्ट्रेशन फीस केवल ₹{amount_small}।"),
    ("job_task", "hi", "native", "घर बैठे काम, रोज़ भुगतान। टास्क शुरू करने के लिए ₹{amount} जमा राशि {upi} पर भेजें।"),
    ("job_task", "hi", "latin", "Ghar baithe kamaayein Rs 5000 roz. Task unlock karne ke liye Rs {amount} deposit bhejein {upi}"),
    ("job_task", "te", "native", "పార్ట్ టైమ్ ఉద్యోగం: వీడియోలు లైక్ చేసి రోజూ ₹3000-8000 సంపాదించండి. ఇప్పుడే చేరండి {link}. రిజిస్ట్రేషన్ ఫీజు ₹{amount_small} మాత్రమే."),
    ("job_task", "te", "native", "ఇంటి నుండే పని, రోజువారీ చెల్లింపు. టాస్క్‌లు ప్రారంభించడానికి ₹{amount} డిపాజిట్ {upi} కి పంపండి."),
    ("job_task", "te", "latin", "Intlo nunde pani, roju Rs 5000 sampadinchandi. Task kosam Rs {amount} deposit pampandi {upi}"),
    # ---- electricity disconnection -------------------------------------------------
    ("bill_disconnection", "en", "native", "Dear consumer, your electricity power will be disconnected {time_en} because your last month bill was not updated. Call officer {phone} immediately."),
    ("bill_disconnection", "en", "native", "{power}: Bill payment pending. Connection will be cut {time_en}. Pay Rs {amount_small} to {upi} to update your record."),
    ("bill_disconnection", "hi", "native", "प्रिय उपभोक्ता, पिछले महीने का बिल अपडेट नहीं होने के कारण {time_hi} आपकी बिजली काट दी जाएगी। तुरंत अधिकारी को {phone} पर कॉल करें।"),
    ("bill_disconnection", "hi", "latin", "Aapki bijli {time_lat} kaat di jayegi. Bill update ke liye turant {phone} par call karein."),
    ("bill_disconnection", "te", "native", "ప్రియమైన వినియోగదారు, గత నెల బిల్ అప్‌డేట్ కాలేదు కాబట్టి {time_te} మీ కరెంట్ కట్ చేయబడుతుంది. వెంటనే అధికారికి {phone} కాల్ చేయండి."),
    ("bill_disconnection", "te", "latin", "Mee current {time_telat} cut avutundi. Bill update kosam ventane {phone} ki call cheyandi."),
    # ---- collect-request trick ---------------------------------------------------
    ("collect_request", "en", "native", "You have received Rs {amount}. Accept the collect request from {upi} to credit it to your account."),
    ("collect_request", "en", "native", "To receive your payment of Rs {amount}, approve the UPI request and enter PIN. Request sent by {upi}."),
    ("collect_request", "hi", "native", "आपको ₹{amount} मिले हैं। पैसा खाते में लेने के लिए {upi} का कलेक्ट अनुरोध स्वीकार करें और PIN डालें।"),
    ("collect_request", "hi", "latin", "Rs {amount} receive karne ke liye {upi} ki request approve karein aur PIN daalein."),
    ("collect_request", "te", "native", "మీకు ₹{amount} వచ్చాయి. డబ్బు ఖాతాలో జమ కావడానికి {upi} నుండి వచ్చిన కలెక్ట్ అభ్యర్థనను ఆమోదించి PIN ఇవ్వండి."),
    ("collect_request", "te", "latin", "Rs {amount} receive cheyyadaniki {upi} request approve chesi PIN enter cheyandi."),
    # ---- sent by mistake -----------------------------------------------------------
    ("wrong_transfer", "en", "native", "Sorry, I sent Rs {amount} to your number by mistake. Please return it to {upi}, it was my hospital fee."),
    ("wrong_transfer", "en", "native", "Rs {amount} credited to your a/c by mistake. Kindly refund to {upi} urgently or legal action will be taken."),
    ("wrong_transfer", "hi", "native", "माफ़ कीजिए, गलती से आपके नंबर पर ₹{amount} चले गए। कृपया {upi} पर वापस भेज दें, यह अस्पताल की फीस थी।"),
    ("wrong_transfer", "hi", "latin", "Galti se aapko Rs {amount} bhej diye. Please turant {upi} par wapas bhej do."),
    ("wrong_transfer", "te", "native", "క్షమించండి, పొరపాటున మీ నంబర్‌కి ₹{amount} పంపాను. దయచేసి {upi} కి తిరిగి పంపండి, అది ఆసుపత్రి ఫీజు."),
    ("wrong_transfer", "te", "latin", "Porapatuna meeku Rs {amount} pampanu. Please ventane {upi} ki tirigi pampandi."),
    # ---- courier / customs -------------------------------------------------------
    ("courier_customs", "en", "native", "{courier}: Your parcel is held at customs. Pay clearance fee Rs {amount_small} within 24 hours: {link}"),
    ("courier_customs", "en", "native", "Delivery failed due to incomplete address. Update details and pay Rs {amount_small} redelivery charge at {link}"),
    ("courier_customs", "hi", "native", "{courier}: आपका पार्सल कस्टम में रुका है। 24 घंटे में ₹{amount_small} क्लियरेंस फीस भरें: {link}"),
    ("courier_customs", "hi", "latin", "Aapka parcel customs mein ruka hai. Rs {amount_small} fees bharein {link}"),
    ("courier_customs", "te", "native", "{courier}: మీ పార్సెల్ కస్టమ్స్ వద్ద ఆగింది. 24 గంటల్లో ₹{amount_small} క్లియరెన్స్ ఫీజు చెల్లించండి: {link}"),
    ("courier_customs", "te", "latin", "Mee parcel customs lo aagindi. Rs {amount_small} fee kattandi {link}"),
    # ---- loan fee ------------------------------------------------------------------
    ("loan_fee", "en", "native", "Pre-approved instant loan of Rs {amount_big} without documents! Pay file charge Rs {amount} to {upi} and get money in 10 minutes."),
    ("loan_fee", "en", "native", "Your loan is sanctioned. To release Rs {amount_big}, pay insurance fee Rs {amount} today. Call {phone}."),
    ("loan_fee", "hi", "native", "बिना कागज़ात ₹{amount_big} का तुरंत लोन मंज़ूर! फ़ाइल चार्ज ₹{amount} {upi} पर भेजें और 10 मिनट में पैसा पाएँ।"),
    ("loan_fee", "hi", "latin", "Aapka Rs {amount_big} loan approve ho gaya hai. File charge Rs {amount} bhejein {upi}"),
    ("loan_fee", "te", "native", "డాక్యుమెంట్లు లేకుండా ₹{amount_big} తక్షణ లోన్ ఆమోదం! ఫైల్ చార్జ్ ₹{amount} {upi} కి పంపి 10 నిమిషాల్లో డబ్బు పొందండి."),
    ("loan_fee", "te", "latin", "Mee Rs {amount_big} loan approve ayindi. File charge Rs {amount} pampandi {upi}"),
    # ---- OTP / PIN request -------------------------------------------------------
    ("otp_pin_request", "en", "native", "{bank} security team: suspicious login detected. Share the OTP you just received with our officer on {phone} to secure your account."),
    ("otp_pin_request", "en", "native", "To stop the unauthorised debit of Rs {amount}, reply with your UPI PIN and the OTP sent to you."),
    ("otp_pin_request", "hi", "native", "{bank} सुरक्षा टीम: आपके खाते में संदिग्ध लॉगिन हुआ है। खाता सुरक्षित करने के लिए अभी मिला OTP हमारे अधिकारी को {phone} पर बताएँ।"),
    ("otp_pin_request", "hi", "latin", "Aapke account se Rs {amount} katne wale hain. Rokne ke liye apna OTP aur PIN batayein {phone}"),
    ("otp_pin_request", "te", "native", "{bank} భద్రతా బృందం: మీ ఖాతాలో అనుమానాస్పద లాగిన్. ఖాతా రక్షణ కోసం ఇప్పుడు వచ్చిన OTP ని మా అధికారికి {phone} లో చెప్పండి."),
    ("otp_pin_request", "te", "latin", "Mee account nundi Rs {amount} cut avutundi. Aapadaniki mee OTP mariyu PIN cheppandi {phone}"),
    # ---- impersonation ----------------------------------------------------------
    ("impersonation", "en", "native", "Hi {relation_en}, this is my new number. My phone broke. I urgently need Rs {amount}, please send to {upi}, will return tomorrow."),
    ("impersonation", "en", "native", "I am calling from police cyber cell. Your Aadhaar is linked to a crime. Pay Rs {amount} verification to {upi} to avoid arrest."),
    ("impersonation", "hi", "native", "मम्मी, यह मेरा नया नंबर है, पुराना फ़ोन खराब हो गया। बहुत ज़रूरी है, ₹{amount} {upi} पर भेज दो, कल लौटा दूँगा।"),
    ("impersonation", "hi", "latin", "Main police cyber cell se bol raha hoon. Aapka Aadhaar crime mein linked hai. Arrest se bachne ke liye Rs {amount} bhejein {upi}"),
    ("impersonation", "te", "native", "అమ్మా, ఇది నా కొత్త నంబర్, పాత ఫోన్ పాడైంది. చాలా అర్జెంట్, ₹{amount} {upi} కి పంపు, రేపు తిరిగి ఇస్తాను."),
    ("impersonation", "te", "latin", "Nenu police cyber cell nundi. Mee Aadhaar crime lo link ayindi. Arrest avvakunda Rs {amount} pampandi {upi}"),
    # ---- investment -------------------------------------------------------------
    ("investment", "en", "native", "Double your money in 7 days! Invest Rs {amount} in our crypto plan and get Rs {amount_big} guaranteed. Join {link}"),
    ("investment", "en", "native", "VIP stock tips group: 300% returns this week. Pay Rs {amount} membership to {upi} and join now."),
    ("investment", "hi", "native", "7 दिन में पैसा दोगुना! हमारे प्लान में ₹{amount} लगाएँ और ₹{amount_big} पक्का पाएँ। जुड़ें {link}"),
    ("investment", "hi", "latin", "Sirf 7 din mein paisa double! Rs {amount} invest karein {link}"),
    ("investment", "te", "native", "7 రోజుల్లో మీ డబ్బు రెట్టింపు! మా ప్లాన్‌లో ₹{amount} పెట్టి ₹{amount_big} ఖచ్చితంగా పొందండి. చేరండి {link}"),
    ("investment", "te", "latin", "7 rojullo dabbu double! Rs {amount} invest cheyandi {link}"),
]

LEGIT = [
    # ---- bank debit alerts -------------------------------------------------------
    ("bank_debit", "en", "native", "Rs {amount} debited from A/c XX{d4} on {date} to {name} via UPI. Ref {ref}. Not you? Call the number on the back of your card. -{bnk}"),
    ("bank_debit", "en", "native", "{bnk}: Your A/c XX{d4} is debited by Rs {amount_small} for UPI payment to DailyBasket. Avl bal Rs {bal}."),
    ("bank_debit", "hi", "native", "आपके खाते XX{d4} से {date} को UPI द्वारा ₹{amount} {name} को भेजे गए। संदर्भ {ref}। -{bnk}"),
    ("bank_debit", "hi", "latin", "A/c XX{d4} se Rs {amount} debit hue {date} ko UPI se. Ref {ref}. -{bnk}"),
    ("bank_debit", "te", "native", "మీ ఖాతా XX{d4} నుండి {date} న UPI ద్వారా ₹{amount} {name} కి డెబిట్ అయింది. రెఫ్ {ref}. -{bnk}"),
    ("bank_debit", "te", "latin", "Mee A/c XX{d4} nundi Rs {amount} debit ayindi {date} UPI dwara. Ref {ref}. -{bnk}"),
    # ---- bank credit alerts -----------------------------------------------------
    ("bank_credit", "en", "native", "Rs {amount} credited to A/c XX{d4} on {date} from {name} (UPI Ref {ref}). Avl bal Rs {bal}. -{bnk}"),
    ("bank_credit", "en", "native", "Salary of Rs {amount_big} credited to your A/c XX{d4}. -{bnk}"),
    ("bank_credit", "hi", "native", "{date} को {name} से आपके खाते XX{d4} में ₹{amount} जमा हुए। UPI संदर्भ {ref}। -{bnk}"),
    ("bank_credit", "hi", "latin", "Aapke A/c XX{d4} mein Rs {amount} credit hue {name} se. Ref {ref}. -{bnk}"),
    ("bank_credit", "te", "native", "{date} న {name} నుండి మీ ఖాతా XX{d4} లో ₹{amount} జమ అయింది. UPI రెఫ్ {ref}. -{bnk}"),
    ("bank_credit", "te", "latin", "Mee A/c XX{d4} lo Rs {amount} credit ayindi {name} nundi. Ref {ref}. -{bnk}"),
    # ---- genuine OTPs (warn not to share) -------------------------------------
    ("otp_genuine", "en", "native", "{otp} is your OTP to log in to {bank} mobile banking. Valid for 5 minutes. Never share your OTP with anyone, including bank staff."),
    ("otp_genuine", "en", "native", "Use OTP {otp} to confirm your {store} order. Do not share this code."),
    ("otp_genuine", "hi", "native", "{bank} मोबाइल बैंकिंग लॉगिन के लिए आपका OTP {otp} है। यह 5 मिनट के लिए मान्य है। किसी के साथ OTP साझा न करें।"),
    ("otp_genuine", "hi", "latin", "{otp} aapka OTP hai. Ise kisi ke saath share na karein, bank bhi kabhi nahi maangta. -{bnk}"),
    ("otp_genuine", "te", "native", "{bank} మొబైల్ బ్యాంకింగ్ లాగిన్ కోసం మీ OTP {otp}. 5 నిమిషాలు చెల్లుతుంది. OTP ని ఎవరితోనూ పంచుకోవద్దు."),
    ("otp_genuine", "te", "latin", "{otp} mee OTP. Deenni evaritho share cheyyakandi, bank kuda adagadu. -{bnk}"),
    # ---- bill reminders (official, no pressure) ----------------------------------
    ("bill_reminder", "en", "native", "{power}: Your bill of Rs {amount_small} for this month is generated. Due date {date}. Pay through your usual UPI app. Ignore if already paid."),
    ("bill_reminder", "en", "native", "Your mobile bill of Rs {amount_small} is due on {date}. Pay via your bank app or UPI."),
    ("bill_reminder", "hi", "native", "{power}: इस महीने का ₹{amount_small} का बिल बन गया है। अंतिम तिथि {date}। अपने सामान्य UPI ऐप से भुगतान करें।"),
    ("bill_reminder", "hi", "latin", "Aapka is mahine ka bijli bill Rs {amount_small} hai, antim tithi {date}. Pehle bhar diya ho to ignore karein."),
    ("bill_reminder", "te", "native", "{power}: ఈ నెల ₹{amount_small} బిల్ తయారైంది. చివరి తేదీ {date}. మీ సాధారణ UPI యాప్ ద్వారా చెల్లించండి."),
    ("bill_reminder", "te", "latin", "Mee ee nela current bill Rs {amount_small}, chivari tedi {date}. Already kattinattaite ignore cheyandi."),
    # ---- deliveries -------------------------------------------------------------
    ("delivery", "en", "native", "Your {store} order #{ref} has been shipped and will arrive by {date}."),
    ("delivery", "en", "native", "{courier}: Your parcel is out for delivery today. Delivery partner {name} will call before arriving."),
    ("delivery", "hi", "native", "आपका {store} ऑर्डर #{ref} भेज दिया गया है और {date} तक पहुँच जाएगा।"),
    ("delivery", "hi", "latin", "Aapka order #{ref} aaj deliver hoga. Delivery partner {name} call karenge."),
    ("delivery", "te", "native", "మీ {store} ఆర్డర్ #{ref} పంపబడింది, {date} లోపు చేరుతుంది."),
    ("delivery", "te", "latin", "Mee order #{ref} ee roju deliver avutundi. Delivery partner {name} call chestaru."),
    # ---- personal chat ------------------------------------------------------------
    ("personal", "en", "native", "Hey {name}, dinner at 8? I'll book the table."),
    ("personal", "en", "native", "Sent you Rs {amount_small} for the movie tickets. Thanks for booking!"),
    ("personal", "en", "native", "Reached home safely. Call you tomorrow morning."),
    ("personal", "hi", "native", "{name}, कल सुबह 7 बजे मंदिर चलेंगे? बता देना।"),
    ("personal", "hi", "latin", "Bhai kal cricket khelne chalega? 6 baje ground pe milte hain."),
    ("personal", "hi", "latin", "Maine tumhe Rs {amount_small} bhej diye chai ke, check kar lo."),
    ("personal", "te", "native", "{name}, రేపు సాయంత్రం సినిమాకి వెళదామా? టికెట్లు నేను బుక్ చేస్తా."),
    ("personal", "te", "latin", "Nenu intiki cherukunnanu. Repu call chesta."),
    ("personal", "te", "latin", "Neeku Rs {amount_small} pampanu tiffin ki, check chesko."),
    # ---- legitimate promotions -------------------------------------------------
    ("promotion", "en", "native", "{store} festive sale: up to 40% off on home essentials this weekend. Shop in the app. T&C apply. To stop, reply STOP."),
    ("promotion", "en", "native", "Your {wallet} monthly statement is ready in the app."),
    ("promotion", "hi", "native", "{store} त्योहार सेल: इस हफ्ते घरेलू सामान पर 40% तक की छूट। ऐप में खरीदें। शर्तें लागू।"),
    ("promotion", "hi", "latin", "{store} weekend sale shuru, app mein 40% tak off. Shartein laagu."),
    ("promotion", "te", "native", "{store} పండుగ సేల్: ఈ వారం ఇంటి వస్తువులపై 40% వరకు తగ్గింపు. యాప్‌లో కొనండి. షరతులు వర్తిస్తాయి."),
    ("promotion", "te", "latin", "{store} weekend sale, app lo 40% varaku discount. Sharathulu vartistayi."),
    # ---- UPI money received (genuine: no action asked) ---------------------------
    ("upi_received", "en", "native", "{name} has sent you Rs {amount} via UPI. It is already in your account - no action needed."),
    ("upi_received", "hi", "native", "{name} ने आपको UPI से ₹{amount} भेजे हैं। पैसा आपके खाते में आ चुका है।"),
    ("upi_received", "hi", "latin", "{name} ne aapko Rs {amount} bheje hain UPI se. Paisa account mein aa gaya hai."),
    ("upi_received", "te", "native", "{name} మీకు UPI ద్వారా ₹{amount} పంపారు. డబ్బు ఇప్పటికే మీ ఖాతాలో ఉంది."),
    ("upi_received", "te", "latin", "{name} meeku Rs {amount} pamparu UPI lo. Dabbu mee account lo undi."),
]

# Short notes attached to collect requests (F9 guard) - deceptive vs ordinary.
NOTES_SCAM = [
    ("collect_request", "en", "native", "Refund for order #{ref} - approve to receive Rs {amount}"),
    ("collect_request", "en", "native", "Cashback reward Rs {amount} - accept to get credited"),
    ("collect_request", "en", "native", "Prize money release - enter PIN to receive"),
    ("collect_request", "en", "native", "KYC verification charge"),
    ("collect_request", "en", "native", "Approve to receive your refund"),
    ("collect_request", "en", "native", "Lucky draw winning amount credit"),
    ("collect_request", "hi", "native", "रिफंड पाने के लिए स्वीकार करें ₹{amount}"),
    ("collect_request", "hi", "latin", "Cashback paane ke liye approve karein"),
    ("collect_request", "hi", "latin", "Inaam ki raashi receive karein"),
    ("collect_request", "te", "native", "రీఫండ్ పొందడానికి ఆమోదించండి ₹{amount}"),
    ("collect_request", "te", "latin", "Cashback kosam approve cheyandi"),
    ("collect_request", "te", "latin", "Bahumati dabbu receive cheyyandi"),
]
NOTES_LEGIT = [
    ("collect_note", "en", "native", "Dinner split"),
    ("collect_note", "en", "native", "Movie tickets"),
    ("collect_note", "en", "native", "Rent share for this month"),
    ("collect_note", "en", "native", "Electricity bill share"),
    ("collect_note", "en", "native", "Trip expenses"),
    ("collect_note", "en", "native", "Grocery bill #{ref}"),
    ("collect_note", "en", "native", "Birthday gift contribution"),
    ("collect_note", "hi", "native", "खाने का बिल बाँटना"),
    ("collect_note", "hi", "latin", "Chai aur nashta"),
    ("collect_note", "hi", "latin", "Kiraya ka hissa"),
    ("collect_note", "te", "native", "భోజనం బిల్ పంపకం"),
    ("collect_note", "te", "latin", "Tiffin dabbulu"),
    ("collect_note", "te", "latin", "Room rent share"),
]


def fill(text: str, rng: random.Random) -> str:
    values = {k: rng.choice(v) for k, v in SLOTS.items()}
    values["link"] = values["link"].format(n=rng.randint(1000, 99999))
    values["phone"] = _phone(rng)
    values["d4"] = f"{rng.randint(0, 9999):04d}"
    values["ref"] = str(rng.randint(10**9, 10**10 - 1))
    values["otp"] = f"{rng.randint(0, 999999):06d}"
    values["bal"] = f"{rng.randint(500, 150000):,}"
    values["date"] = f"{rng.randint(1, 28):02d}-{rng.choice(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}"
    return text.format(**values)


def build() -> list[dict]:
    rng = random.Random(SEED)
    rows: list[dict] = []
    groups = [
        (SCAM, 1, "sms", VARIANTS),
        (LEGIT, 0, "sms", VARIANTS),
        (NOTES_SCAM, 1, "collect_note", NOTE_VARIANTS),
        (NOTES_LEGIT, 0, "collect_note", NOTE_VARIANTS),
    ]
    for templates, label, kind, variants in groups:
        for i, (category, language, script, template) in enumerate(templates):
            template_id = f"{kind[:1]}{label}-{category}-{language}{script[0]}-{i:03d}"
            seen: set[str] = set()
            for _ in range(variants * 3):
                text = fill(template, rng)
                if text in seen:
                    continue
                seen.add(text)
                rows.append(
                    {
                        "text": text,
                        "label": label,
                        "category": category,
                        "language": language,
                        "script": script,
                        "template_id": template_id,
                        "kind": kind,
                    }
                )
                if len(seen) >= variants:
                    break
    for n, row in enumerate(rows, start=1):
        row["id"] = f"upg-sms-{n:05d}"
    return rows


def main() -> None:
    rows = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "label", "category", "language", "script", "template_id", "kind"])
        writer.writeheader()
        writer.writerows(rows)
    scams = sum(r["label"] for r in rows)
    print(f"wrote {len(rows)} messages ({scams} scam, {len(rows) - scams} legitimate) to {OUT}")


if __name__ == "__main__":
    main()
