"""Server-side texts in English, Hindi and Telugu: risk reasons, scam advice and spoken phrases.

The API returns every reason in all three languages so the app can switch language instantly,
and the voice assistant speaks exactly what the screen shows.
"""
from __future__ import annotations

LANGS = ("en", "hi", "te")

REASONS: dict[str, dict[str, str]] = {
    # ---- risk-raising reasons (SHAP positive) ------------------------------------
    "NEW_PAYEE": {
        "en": "You have never paid {payee} before.",
        "hi": "आपने {payee} को पहले कभी भुगतान नहीं किया है।",
        "te": "మీరు {payee} కి ఇంతకు ముందు ఎప్పుడూ చెల్లించలేదు.",
    },
    "NOT_SAVED": {
        "en": "{payee} is not in your saved contacts.",
        "hi": "{payee} आपके सेव किए गए संपर्कों में नहीं हैं।",
        "te": "{payee} మీ సేవ్ చేసిన పరిచయాల్లో లేరు.",
    },
    "AMOUNT_UNUSUAL": {
        "en": "This is {ratio} times more than you usually pay.",
        "hi": "यह आपके आम भुगतान से {ratio} गुना ज़्यादा है।",
        "te": "ఇది మీరు సాధారణంగా చెల్లించే దానికంటే {ratio} రెట్లు ఎక్కువ.",
    },
    "AMOUNT_HIGHEST": {
        "en": "This is more than any payment you made in the last 3 months.",
        "hi": "यह पिछले 3 महीनों के आपके किसी भी भुगतान से ज़्यादा है।",
        "te": "ఇది గత 3 నెలల్లో మీరు చేసిన ఏ చెల్లింపు కంటే ఎక్కువ.",
    },
    "AMOUNT_LARGE": {
        "en": "{amount} is a large amount.",
        "hi": "{amount} एक बड़ी रकम है।",
        "te": "{amount} పెద్ద మొత్తం.",
    },
    "NIGHT": {
        "en": "It is {time} - late-night payments are common in scams.",
        "hi": "अभी {time} बजे हैं - देर रात के भुगतान अक्सर धोखाधड़ी में होते हैं।",
        "te": "ఇప్పుడు సమయం {time} - అర్ధరాత్రి చెల్లింపులు మోసాల్లో ఎక్కువగా ఉంటాయి.",
    },
    "UNUSUAL_TIME": {
        "en": "You rarely pay at this time of day.",
        "hi": "आप इस समय बहुत कम भुगतान करते हैं।",
        "te": "మీరు ఈ సమయంలో చాలా అరుదుగా చెల్లిస్తారు.",
    },
    "RAPID_PAYMENTS": {
        "en": "{n} payments in the last hour - scammers often push for quick repeated payments.",
        "hi": "पिछले एक घंटे में {n} भुगतान - धोखेबाज़ अक्सर जल्दी-जल्दी भुगतान करवाते हैं।",
        "te": "గత గంటలో {n} చెల్లింపులు - మోసగాళ్లు తరచూ వెంటవెంటనే చెల్లింపులు చేయిస్తారు.",
    },
    "MANY_PAYMENTS": {
        "en": "You have made {n} payments in the last 24 hours.",
        "hi": "पिछले 24 घंटों में आपने {n} भुगतान किए हैं।",
        "te": "గత 24 గంటల్లో మీరు {n} చెల్లింపులు చేశారు.",
    },
    "FAILED_ATTEMPTS": {
        "en": "{n} failed attempts in the last 24 hours.",
        "hi": "पिछले 24 घंटों में {n} असफल प्रयास हुए।",
        "te": "గత 24 గంటల్లో {n} విఫల ప్రయత్నాలు జరిగాయి.",
    },
    "NEW_ACCOUNT": {
        "en": "{payee}'s account is only {days} days old.",
        "hi": "{payee} का खाता सिर्फ़ {days} दिन पुराना है।",
        "te": "{payee} ఖాతా కేవలం {days} రోజుల పాతది.",
    },
    "REPORTED": {
        "en": "{n} people reported this UPI ID as a scam.",
        "hi": "{n} लोगों ने इस UPI ID की धोखाधड़ी के रूप में शिकायत की है।",
        "te": "{n} మంది ఈ UPI IDని మోసంగా నివేదించారు.",
    },
    "MANY_NEW_PAYERS": {
        "en": "This receiver is suddenly getting money from many new people.",
        "hi": "इस प्राप्तकर्ता को अचानक कई नए लोगों से पैसा मिल रहा है।",
        "te": "ఈ గ్రహీతకు అకస్మాత్తుగా చాలా మంది కొత్తవారి నుండి డబ్బు వస్తోంది.",
    },
    "MASS_COLLECT": {
        "en": "This receiver sent payment requests to {n} people this week.",
        "hi": "इस प्राप्तकर्ता ने इस हफ़्ते {n} लोगों को भुगतान अनुरोध भेजे।",
        "te": "ఈ గ్రహీత ఈ వారం {n} మందికి చెల్లింపు అభ్యర్థనలు పంపారు.",
    },
    "SCAM_SMS_LINKED": {
        "en": "A message you checked that mentions this receiver looks like a scam.",
        "hi": "आपने जो संदेश जाँचा, उसमें यही प्राप्तकर्ता है और वह धोखाधड़ी लगता है।",
        "te": "మీరు తనిఖీ చేసిన సందేశంలో ఇదే గ్రహీత ఉన్నారు, అది మోసంలా ఉంది.",
    },
    "RECENT_SCAM_SMS": {
        "en": "You checked a scam message today. Scammers often follow up with a payment request.",
        "hi": "आपने आज एक धोखाधड़ी वाला संदेश जाँचा। धोखेबाज़ अक्सर इसके बाद भुगतान माँगते हैं।",
        "te": "మీరు ఈ రోజు ఒక మోసపు సందేశాన్ని తనిఖీ చేశారు. మోసగాళ్లు తరచూ తర్వాత చెల్లింపు అడుగుతారు.",
    },
    "COLLECT_DEBIT": {
        "en": "This is a request to PAY {amount}, not to receive money.",
        "hi": "यह {amount} भुगतान करने का अनुरोध है, पैसा पाने का नहीं।",
        "te": "ఇది {amount} చెల్లించే అభ్యర్థన, డబ్బు పొందేది కాదు.",
    },
    "DECEPTIVE_NOTE": {
        "en": "The request note promises you money - a common refund trick.",
        "hi": "अनुरोध के नोट में आपको पैसे का वादा है - यह रिफंड वाली आम चाल है।",
        "te": "అభ్యర్థన నోట్‌లో మీకు డబ్బు వస్తుందని ఉంది - ఇది సాధారణ రీఫండ్ మోసం.",
    },
    "QR_TRICK": {
        "en": "This QR code looks like a 'scan to receive money' trick.",
        "hi": "यह QR कोड 'पैसा पाने के लिए स्कैन करें' वाली चाल लगता है।",
        "te": "ఈ QR కోడ్ 'డబ్బు పొందడానికి స్కాన్ చేయండి' మోసంలా ఉంది.",
    },
    "BEHAVIOUR_VELOCITY": {
        "en": "Your account shows an unusual burst of payments today.",
        "hi": "आज आपके खाते में असामान्य रूप से ज़्यादा भुगतान हुए हैं।",
        "te": "ఈ రోజు మీ ఖాతాలో అసాధారణంగా ఎక్కువ చెల్లింపులు జరిగాయి.",
    },
    "BEHAVIOUR_FAILED": {
        "en": "Repeated failed attempts look like someone is pressuring you.",
        "hi": "बार-बार असफल प्रयास दिखाते हैं कि कोई आप पर दबाव डाल रहा हो सकता है।",
        "te": "మళ్లీ మళ్లీ విఫల ప్రయత్నాలు ఎవరో మీపై ఒత్తిడి చేస్తున్నట్లు సూచిస్తున్నాయి.",
    },
    "BEHAVIOUR_RECEIVER": {
        "en": "Payments like this to receivers like this are often fraud.",
        "hi": "ऐसे प्राप्तकर्ताओं को ऐसे भुगतान अक्सर धोखाधड़ी होते हैं।",
        "te": "ఇలాంటి గ్రహీతలకు ఇలాంటి చెల్లింపులు తరచూ మోసమే.",
    },
    "BEHAVIOUR_AMOUNT": {
        "en": "The amount does not match your normal spending.",
        "hi": "यह रकम आपके सामान्य खर्च से मेल नहीं खाती।",
        "te": "ఈ మొత్తం మీ సాధారణ ఖర్చుకు సరిపోలడం లేదు.",
    },
    "BEHAVIOUR_GENERAL": {
        "en": "Your payment pattern right now looks unusual.",
        "hi": "अभी आपके भुगतान का तरीका असामान्य लग रहा है।",
        "te": "ప్రస్తుతం మీ చెల్లింపు తీరు అసాధారణంగా ఉంది.",
    },
    "NEW_USER": {
        "en": "Your account is new, so we are being extra careful.",
        "hi": "आपका खाता नया है, इसलिए हम ज़्यादा सावधानी बरत रहे हैं।",
        "te": "మీ ఖాతా కొత్తది, అందుకే మేము మరింత జాగ్రత్తగా ఉన్నాము.",
    },
    # ---- reassuring reasons (SHAP negative) --------------------------------------
    "KNOWN_PAYEE": {
        "en": "You have paid {payee} {n} times before.",
        "hi": "आप {payee} को पहले {n} बार भुगतान कर चुके हैं।",
        "te": "మీరు {payee} కి ఇంతకు ముందు {n} సార్లు చెల్లించారు.",
    },
    "SAVED_CONTACT": {
        "en": "{payee} is in your saved contacts.",
        "hi": "{payee} आपके सेव किए गए संपर्कों में हैं।",
        "te": "{payee} మీ సేవ్ చేసిన పరిచయాల్లో ఉన్నారు.",
    },
    "TRUSTED_PAYEE": {
        "en": "{payee} has a long, clean payment history.",
        "hi": "{payee} का भुगतान इतिहास लंबा और साफ़ है।",
        "te": "{payee} కి సుదీర్ఘమైన, శుభ్రమైన చెల్లింపు చరిత్ర ఉంది.",
    },
    "USUAL_AMOUNT": {
        "en": "The amount is normal for you.",
        "hi": "यह रकम आपके लिए सामान्य है।",
        "te": "ఈ మొత్తం మీకు సాధారణమే.",
    },
    "USUAL_TIME": {
        "en": "You often pay at this time of day.",
        "hi": "आप अक्सर इस समय भुगतान करते हैं।",
        "te": "మీరు తరచూ ఈ సమయంలో చెల్లిస్తారు.",
    },
}

SCAM_TYPES: dict[str, dict[str, str]] = {
    "kyc_fraud": {"en": "fake KYC / account block", "hi": "नकली KYC / खाता बंद", "te": "నకిలీ KYC / ఖాతా బ్లాక్"},
    "refund_scam": {"en": "fake refund or cashback", "hi": "नकली रिफंड या कैशबैक", "te": "నకిలీ రీఫండ్ లేదా క్యాష్‌బ్యాక్"},
    "collect_request": {"en": "collect-request trick", "hi": "कलेक्ट अनुरोध की चाल", "te": "కలెక్ట్ అభ్యర్థన మోసం"},
    "lottery_prize": {"en": "lottery or prize", "hi": "लॉटरी या इनाम", "te": "లాటరీ లేదా బహుమతి"},
    "job_task": {"en": "job or task", "hi": "नौकरी या टास्क", "te": "ఉద్యోగం లేదా టాస్క్"},
    "bill_disconnection": {"en": "electricity disconnection", "hi": "बिजली कटने की धमकी", "te": "కరెంట్ కట్ బెదిరింపు"},
    "wrong_transfer": {"en": "'sent by mistake'", "hi": "'गलती से भेजा'", "te": "'పొరపాటున పంపాను'"},
    "courier_customs": {"en": "courier or customs fee", "hi": "कूरियर या कस्टम फीस", "te": "కొరియర్ లేదా కస్టమ్స్ ఫీజు"},
    "loan_fee": {"en": "loan fee", "hi": "लोन फीस", "te": "లోన్ ఫీజు"},
    "otp_pin_request": {"en": "OTP / PIN theft", "hi": "OTP / PIN चोरी", "te": "OTP / PIN దొంగతనం"},
    "impersonation": {"en": "impersonation", "hi": "किसी और के नाम से ठगी", "te": "వేరొకరిలా నటించి మోసం"},
    "investment": {"en": "investment doubling", "hi": "पैसा दोगुना करने की ठगी", "te": "డబ్బు రెట్టింపు మోసం"},
    "qr_scam": {"en": "QR code", "hi": "QR कोड", "te": "QR కోడ్"},
    "account_takeover": {"en": "misused contact account", "hi": "संपर्क के खाते का दुरुपयोग", "te": "పరిచయం ఖాతా దుర్వినియోగం"},
}

ADVICE: dict[str, dict[str, str]] = {
    "kyc_fraud": {
        "en": "Banks never ask you to update KYC through a link or by paying anyone. Use your bank's official app or branch.",
        "hi": "बैंक कभी लिंक से या किसी को पैसे देकर KYC अपडेट करने को नहीं कहते। बैंक का आधिकारिक ऐप या शाखा ही इस्तेमाल करें।",
        "te": "బ్యాంకులు ఎప్పుడూ లింక్ ద్వారా లేదా ఎవరికైనా చెల్లించి KYC అప్‌డేట్ చేయమని అడగవు. బ్యాంక్ అధికారిక యాప్ లేదా శాఖనే ఉపయోగించండి.",
    },
    "refund_scam": {
        "en": "You never need to pay, scan a QR code or enter your PIN to receive a refund.",
        "hi": "रिफंड पाने के लिए कभी भुगतान करने, QR स्कैन करने या PIN डालने की ज़रूरत नहीं होती।",
        "te": "రీఫండ్ పొందడానికి ఎప్పుడూ చెల్లించాల్సిన, QR స్కాన్ చేయాల్సిన లేదా PIN ఇవ్వాల్సిన అవసరం లేదు.",
    },
    "collect_request": {
        "en": "Approving a collect request always takes money OUT of your account.",
        "hi": "कलेक्ट अनुरोध मंज़ूर करने पर हमेशा आपके खाते से पैसा कटता है।",
        "te": "కలెక్ట్ అభ్యర్థనను ఆమోదిస్తే ఎప్పుడూ మీ ఖాతా నుండే డబ్బు వెళ్తుంది.",
    },
    "lottery_prize": {
        "en": "Real prizes never ask for a fee. You have not won anything.",
        "hi": "असली इनाम के लिए कभी फीस नहीं माँगी जाती। आपने कुछ नहीं जीता है।",
        "te": "నిజమైన బహుమతులకు ఎప్పుడూ ఫీజు అడగరు. మీరు ఏమీ గెలవలేదు.",
    },
    "job_task": {
        "en": "Real jobs never ask you to pay a deposit or to 'unlock' tasks.",
        "hi": "असली नौकरी में कभी जमा राशि या टास्क 'अनलॉक' करने के पैसे नहीं माँगे जाते।",
        "te": "నిజమైన ఉద్యోగాలు ఎప్పుడూ డిపాజిట్ లేదా టాస్క్ 'అన్‌లాక్' కోసం డబ్బు అడగవు.",
    },
    "bill_disconnection": {
        "en": "Power companies do not cut your supply through an SMS with a personal number. Pay only in your usual official app.",
        "hi": "बिजली कंपनियाँ किसी निजी नंबर वाले SMS से बिजली नहीं काटतीं। बिल सिर्फ़ अपने सामान्य आधिकारिक ऐप से भरें।",
        "te": "విద్యుత్ సంస్థలు వ్యక్తిగత నంబర్ ఉన్న SMS ద్వారా కరెంట్ కట్ చేయవు. బిల్ మీ సాధారణ అధికారిక యాప్‌లోనే కట్టండి.",
    },
    "wrong_transfer": {
        "en": "If someone says they sent money by mistake, check your balance in your bank app first. Never 'return' money to a different UPI ID.",
        "hi": "कोई कहे कि गलती से पैसा भेजा, तो पहले अपने बैंक ऐप में बैलेंस देखें। किसी दूसरी UPI ID पर पैसा 'वापस' कभी न भेजें।",
        "te": "పొరపాటున డబ్బు పంపామని ఎవరైనా చెబితే ముందు మీ బ్యాంక్ యాప్‌లో బ్యాలెన్స్ చూడండి. వేరే UPI IDకి డబ్బు 'తిరిగి' ఎప్పుడూ పంపకండి.",
    },
    "courier_customs": {
        "en": "Couriers do not collect customs fees through UPI links.",
        "hi": "कूरियर कंपनियाँ UPI लिंक से कस्टम फीस नहीं लेतीं।",
        "te": "కొరియర్ సంస్థలు UPI లింక్‌ల ద్వారా కస్టమ్స్ ఫీజు తీసుకోవు.",
    },
    "loan_fee": {
        "en": "Genuine lenders never ask for a fee before giving a loan.",
        "hi": "असली लोन देने वाले लोन से पहले कभी फीस नहीं माँगते।",
        "te": "నిజమైన రుణదాతలు లోన్ ఇచ్చే ముందు ఎప్పుడూ ఫీజు అడగరు.",
    },
    "otp_pin_request": {
        "en": "Never share your OTP or UPI PIN with anyone - not even bank staff.",
        "hi": "अपना OTP या UPI PIN कभी किसी को न बताएँ - बैंक कर्मचारी को भी नहीं।",
        "te": "మీ OTP లేదా UPI PINను ఎవరికీ చెప్పకండి - బ్యాంక్ సిబ్బందికి కూడా.",
    },
    "impersonation": {
        "en": "Call the person on the number you already have before sending money. Police never ask for money over UPI.",
        "hi": "पैसा भेजने से पहले उस व्यक्ति को उसके पुराने नंबर पर फ़ोन करें। पुलिस कभी UPI पर पैसा नहीं माँगती।",
        "te": "డబ్బు పంపే ముందు ఆ వ్యక్తికి మీ దగ్గర ఉన్న పాత నంబర్‌కే ఫోన్ చేయండి. పోలీసులు ఎప్పుడూ UPIలో డబ్బు అడగరు.",
    },
    "investment": {
        "en": "Guaranteed high returns are always a scam.",
        "hi": "पक्के और बहुत ज़्यादा मुनाफ़े का वादा हमेशा धोखा होता है।",
        "te": "ఖచ్చితమైన అధిక లాభాల వాగ్దానం ఎప్పుడూ మోసమే.",
    },
    "qr_scam": {
        "en": "You scan a QR code only to PAY, never to receive money.",
        "hi": "QR कोड सिर्फ़ भुगतान करने के लिए स्कैन होता है, पैसा पाने के लिए कभी नहीं।",
        "te": "QR కోడ్‌ను చెల్లించడానికే స్కాన్ చేస్తారు, డబ్బు పొందడానికి ఎప్పుడూ కాదు.",
    },
    "account_takeover": {
        "en": "Your contact's account may be misused. Confirm with them by phone before paying.",
        "hi": "आपके संपर्क के खाते का गलत इस्तेमाल हो सकता है। भुगतान से पहले उनसे फ़ोन पर पुष्टि करें।",
        "te": "మీ పరిచయం ఖాతా దుర్వినియోగం అయి ఉండొచ్చు. చెల్లించే ముందు వారితో ఫోన్‌లో నిర్ధారించుకోండి.",
    },
    "general": {
        "en": "If anyone is rushing you, stop. A real person or company will wait while you check.",
        "hi": "अगर कोई आपको जल्दी करने को कह रहा है, तो रुकिए। असली व्यक्ति या कंपनी आपके जाँचने तक इंतज़ार करेगी।",
        "te": "ఎవరైనా మిమ్మల్ని తొందరపెడుతుంటే ఆగండి. నిజమైన వ్యక్తి లేదా సంస్థ మీరు తనిఖీ చేసే వరకు వేచి ఉంటారు.",
    },
}

VOICE: dict[str, dict[str, str]] = {
    "payment_high": {
        "en": "{name}, please stop and think. This payment of {amount} to {payee} looks risky. {reasons} {advice}",
        "hi": "{name}, कृपया रुकिए और सोचिए। {payee} को {amount} का यह भुगतान जोखिम भरा लगता है। {reasons} {advice}",
        "te": "{name}, దయచేసి ఆగి ఆలోచించండి. {payee} కి {amount} ఈ చెల్లింపు ప్రమాదకరంగా ఉంది. {reasons} {advice}",
    },
    "payment_medium": {
        "en": "{name}, please check before you pay {amount} to {payee}. {reasons}",
        "hi": "{name}, {payee} को {amount} भेजने से पहले कृपया जाँच लें। {reasons}",
        "te": "{name}, {payee} కి {amount} పంపే ముందు దయచేసి సరిచూసుకోండి. {reasons}",
    },
    "payment_low": {
        "en": "This payment of {amount} to {payee} looks safe.",
        "hi": "{payee} को {amount} का यह भुगतान सुरक्षित लगता है।",
        "te": "{payee} కి {amount} ఈ చెల్లింపు సురక్షితంగా ఉంది.",
    },
    "payment_blocked": {
        "en": "{name}, we stopped this payment. {payee} has been reported as a scam by several people.",
        "hi": "{name}, हमने यह भुगतान रोक दिया है। कई लोगों ने {payee} की धोखाधड़ी के रूप में शिकायत की है।",
        "te": "{name}, మేము ఈ చెల్లింపును ఆపాము. చాలా మంది {payee} ని మోసంగా నివేదించారు.",
    },
    "hold_started": {
        "en": "Your payment is on hold for {minutes} minutes. You can cancel it any time before then.",
        "hi": "आपका भुगतान {minutes} मिनट के लिए रोका गया है। तब तक आप इसे कभी भी रद्द कर सकते हैं।",
        "te": "మీ చెల్లింపు {minutes} నిమిషాల పాటు ఆపబడింది. అప్పటిలోగా ఎప్పుడైనా రద్దు చేయవచ్చు.",
    },
    "sms_scam": {
        "en": "{name}, be careful. This message looks like a scam: {type}. {advice} Do not click the link or pay anyone.",
        "hi": "{name}, सावधान रहिए। यह संदेश {type} वाली धोखाधड़ी लगता है। {advice} लिंक पर क्लिक न करें और किसी को भुगतान न करें।",
        "te": "{name}, జాగ్రత్త. ఈ సందేశం {type} మోసంలా ఉంది. {advice} లింక్‌పై క్లిక్ చేయకండి, ఎవరికీ చెల్లించకండి.",
    },
    "sms_suspicious": {
        "en": "{name}, this message has warning signs. Check with the sender through an official number before you act.",
        "hi": "{name}, इस संदेश में खतरे के संकेत हैं। कुछ भी करने से पहले आधिकारिक नंबर पर भेजने वाले से पुष्टि करें।",
        "te": "{name}, ఈ సందేశంలో హెచ్చరిక సంకేతాలు ఉన్నాయి. ఏదైనా చేసే ముందు అధికారిక నంబర్ ద్వారా పంపినవారితో నిర్ధారించుకోండి.",
    },
    "sms_safe": {
        "en": "This message looks safe. Still, never share your OTP or PIN.",
        "hi": "यह संदेश सुरक्षित लगता है। फिर भी अपना OTP या PIN कभी साझा न करें।",
        "te": "ఈ సందేశం సురక్షితంగా ఉంది. అయినా మీ OTP లేదా PINను ఎప్పుడూ పంచుకోకండి.",
    },
    "collect_debit": {
        "en": "{name}, careful. Approving this request will take {amount} out of your account. You never approve a request to receive money.",
        "hi": "{name}, सावधान। यह अनुरोध मंज़ूर करने पर आपके खाते से {amount} कट जाएँगे। पैसा पाने के लिए कभी अनुरोध मंज़ूर नहीं करना पड़ता।",
        "te": "{name}, జాగ్రత్త. ఈ అభ్యర్థనను ఆమోదిస్తే మీ ఖాతా నుండి {amount} వెళ్లిపోతాయి. డబ్బు పొందడానికి ఎప్పుడూ అభ్యర్థనను ఆమోదించాల్సిన అవసరం లేదు.",
    },
    "qr_trick": {
        "en": "{name}, this QR code will take money from you. You never scan a QR code to receive money.",
        "hi": "{name}, यह QR कोड आपसे पैसा लेगा। पैसा पाने के लिए कभी QR कोड स्कैन नहीं करना पड़ता।",
        "te": "{name}, ఈ QR కోడ్ మీ నుండి డబ్బు తీసుకుంటుంది. డబ్బు పొందడానికి ఎప్పుడూ QR కోడ్ స్కాన్ చేయాల్సిన అవసరం లేదు.",
    },
}

GUIDES: dict[str, dict[str, str]] = {
    "home": {
        "en": "This is your sandbox wallet. You can send money, scan a QR code, check a suspicious SMS, or see requests waiting for you. No real money moves here.",
        "hi": "यह आपका सैंडबॉक्स वॉलेट है। आप पैसे भेज सकते हैं, QR कोड स्कैन कर सकते हैं, संदिग्ध SMS जाँच सकते हैं या आपके लिए आए अनुरोध देख सकते हैं। यहाँ कोई असली पैसा नहीं जाता।",
        "te": "ఇది మీ శాండ్‌బాక్స్ వాలెట్. మీరు డబ్బు పంపవచ్చు, QR కోడ్ స్కాన్ చేయవచ్చు, అనుమానాస్పద SMS తనిఖీ చేయవచ్చు లేదా మీ కోసం వచ్చిన అభ్యర్థనలు చూడవచ్చు. ఇక్కడ నిజమైన డబ్బు కదలదు.",
    },
    "send": {
        "en": "Enter the UPI ID or pick a saved contact, then the amount. Before you confirm, UPI Guardian checks the payment and tells you if anything looks wrong.",
        "hi": "UPI ID डालें या सेव किया गया संपर्क चुनें, फिर रकम डालें। पुष्टि से पहले UPI Guardian भुगतान की जाँच करता है और कुछ गलत लगे तो बताता है।",
        "te": "UPI ID ఇవ్వండి లేదా సేవ్ చేసిన పరిచయాన్ని ఎంచుకోండి, తర్వాత మొత్తం ఇవ్వండి. మీరు నిర్ధారించే ముందు UPI Guardian చెల్లింపును తనిఖీ చేసి ఏదైనా తప్పుగా ఉంటే చెబుతుంది.",
    },
    "scan": {
        "en": "Point the camera at a QR code, or upload a photo of it. Remember: scanning a QR code is only for paying, never for receiving money.",
        "hi": "कैमरा QR कोड की ओर करें या उसकी फ़ोटो अपलोड करें। याद रखें: QR स्कैन सिर्फ़ भुगतान के लिए है, पैसा पाने के लिए कभी नहीं।",
        "te": "కెమెరాను QR కోడ్ వైపు చూపండి లేదా దాని ఫోటోను అప్‌లోడ్ చేయండి. గుర్తుంచుకోండి: QR స్కాన్ చెల్లించడానికే, డబ్బు పొందడానికి ఎప్పుడూ కాదు.",
    },
    "collect": {
        "en": "These are requests asking you to pay. Approving a request always takes money out of your account. Decline anything you do not recognise.",
        "hi": "ये आपसे भुगतान माँगने वाले अनुरोध हैं। अनुरोध मंज़ूर करने पर हमेशा आपके खाते से पैसा कटता है। जो न पहचानें, उसे अस्वीकार करें।",
        "te": "ఇవి మిమ్మల్ని చెల్లించమని అడిగే అభ్యర్థనలు. అభ్యర్థనను ఆమోదిస్తే ఎప్పుడూ మీ ఖాతా నుండే డబ్బు వెళ్తుంది. మీకు తెలియనిదాన్ని తిరస్కరించండి.",
    },
    "sms": {
        "en": "Paste a message you received. UPI Guardian tells you if it is a scam and highlights the dangerous words.",
        "hi": "आपको मिला संदेश यहाँ चिपकाएँ। UPI Guardian बताएगा कि यह धोखाधड़ी है या नहीं और खतरनाक शब्दों को चिह्नित करेगा।",
        "te": "మీకు వచ్చిన సందేశాన్ని ఇక్కడ అతికించండి. అది మోసమో కాదో UPI Guardian చెబుతుంది, ప్రమాదకరమైన పదాలను గుర్తిస్తుంది.",
    },
    "history": {
        "en": "Here are all your payments. Open one to see its risk level and the reasons behind it.",
        "hi": "यहाँ आपके सभी भुगतान हैं। किसी एक को खोलकर उसका जोखिम स्तर और उसके कारण देखें।",
        "te": "ఇక్కడ మీ అన్ని చెల్లింపులు ఉన్నాయి. దేనినైనా తెరిచి దాని ప్రమాద స్థాయి, కారణాలు చూడండి.",
    },
    "trusted": {
        "en": "Add a family member you trust. When approval is on, they must approve risky payments before the money goes.",
        "hi": "अपने भरोसेमंद परिवार के सदस्य को जोड़ें। मंज़ूरी चालू होने पर, जोखिम वाले भुगतान से पहले उन्हें मंज़ूरी देनी होगी।",
        "te": "మీరు నమ్మే కుటుంబ సభ్యుడిని జోడించండి. ఆమోదం ఆన్‌లో ఉంటే, ప్రమాదకర చెల్లింపులకు డబ్బు వెళ్లే ముందు వారు ఆమోదించాలి.",
    },
    "settings": {
        "en": "Choose your language, turn spoken warnings on or off, and set how long risky payments are held.",
        "hi": "अपनी भाषा चुनें, बोलकर दी जाने वाली चेतावनियाँ चालू या बंद करें और तय करें कि जोखिम वाले भुगतान कितनी देर रुकें।",
        "te": "మీ భాషను ఎంచుకోండి, మాట్లాడే హెచ్చరికలను ఆన్ లేదా ఆఫ్ చేయండి, ప్రమాదకర చెల్లింపులు ఎంతసేపు ఆగాలో నిర్ణయించండి.",
    },
    "hold": {
        "en": "This payment is waiting. Take a moment, call someone you trust, and cancel it if anything feels wrong. Your money comes straight back.",
        "hi": "यह भुगतान रुका हुआ है। थोड़ा समय लें, किसी भरोसेमंद व्यक्ति को फ़ोन करें और कुछ भी गलत लगे तो रद्द कर दें। पैसा तुरंत वापस आ जाएगा।",
        "te": "ఈ చెల్లింపు వేచి ఉంది. కొంచెం సమయం తీసుకోండి, మీరు నమ్మేవారికి ఫోన్ చేయండి, ఏదైనా తప్పుగా అనిపిస్తే రద్దు చేయండి. మీ డబ్బు వెంటనే తిరిగి వస్తుంది.",
    },
    "intent": {
        "en": "Tell us what this payment is for. Your answer helps us warn you about the exact trick scammers use.",
        "hi": "बताइए यह भुगतान किसलिए है। आपका जवाब हमें धोखेबाज़ों की सही चाल के बारे में चेतावनी देने में मदद करता है।",
        "te": "ఈ చెల్లింపు దేనికోసమో చెప్పండి. మోసగాళ్లు వాడే సరైన మోసం గురించి హెచ్చరించడానికి మీ సమాధానం సహాయపడుతుంది.",
    },
}

HONORIFIC = {"en": "{name}", "hi": "{name} जी", "te": "{name} గారు"}
RUPEES = {"en": "{amount} rupees", "hi": "{amount} रुपये", "te": "{amount} రూపాయలు"}


def render(template: str, params: dict) -> str:
    class _Safe(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    return template.format_map(_Safe(params))


def reason_texts(code: str, params: dict) -> dict[str, str]:
    catalog = REASONS.get(code)
    if not catalog:
        return {lang: code for lang in LANGS}
    out = {}
    for lang in LANGS:
        p = dict(params)
        if "amount_value" in p:
            p["amount"] = format_amount(p["amount_value"], lang)
        out[lang] = render(catalog[lang], p)
    return out


def format_amount(value: float, lang: str) -> str:
    whole = int(round(value))
    s = str(whole)
    if len(s) > 3:  # Indian digit grouping: 1,23,456
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups + [tail])
    return "₹" + s if lang == "en" else "₹" + s


def spoken_amount(value: float, lang: str) -> str:
    return render(RUPEES[lang], {"amount": format_amount(value, lang).lstrip("₹")})


def scam_type_name(code: str | None, lang: str) -> str:
    if not code:
        return ""
    return SCAM_TYPES.get(code, {}).get(lang, code.replace("_", " "))


def advice(code: str | None, lang: str) -> str:
    return ADVICE.get(code or "general", ADVICE["general"])[lang]
