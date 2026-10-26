"""Hand-written probe set for the expense categoriser (198 descriptions, 11 categories x 18).

Written by the project team BEFORE any score was computed, and never used for training. It is not an
independent benchmark: the descriptions are realistic Indian bank/UPI/card narrations that we composed.
Each category has three tiers of six:

  A  "seed-like"  wording close to the bundled training vocabulary (a light re-wording)
  B  "statement"  upper-case UPI / POS / NEFT style strings that still contain a seed keyword
  C  "unseen"     real merchants or phrases with no token in the training data
"""
from __future__ import annotations

PROBE: dict[str, dict[str, list[str]]] = {
    "Food": {
        "A": ["Swiggy dinner order", "Zomato lunch", "Restaurant lunch with friends", "Coffee shop snacks",
              "McDonalds meal", "Grocery store vegetables"],
        "B": ["UPI-SWIGGY-8842110@axl", "POS 4421 RESTAURANT HYDERABAD", "UPI/ZOMATO/ORDER 55231",
              "GROCERY STORE KPHB UPI", "POS COFFEE SHOP MADHAPUR", "UPI-MCDONALDS-INDIA"],
        "C": ["BigBasket delivery", "Dominos pizza", "Blinkit groceries", "Chaayos tea", "Haldirams snacks",
              "Biryani Blues"],
    },
    "Transport": {
        "A": ["Uber ride to office", "Ola cab airport", "Petrol pump fuel", "Metro card top up",
              "Bus ticket TSRTC", "Parking fee mall"],
        "B": ["UPI-UBER-INDIA-7731", "POS PETROL PUMP HPCL", "OLA CABS UPI 22891", "UPI/METRO CARD RECHARGE",
              "PARKING FEE SECUNDERABAD", "BUS TICKET ONLINE"],
        "C": ["Rapido bike taxi", "FASTag recharge", "Indian Oil fuel", "Namma Yatri auto", "BluSmart ride",
              "Shell fuel station"],
    },
    "Entertainment": {
        "A": ["Netflix subscription renewal", "Movie tickets weekend", "Spotify premium plan",
              "Amazon Prime Video", "Gaming purchase Steam", "Concert tickets"],
        "B": ["UPI-NETFLIX-COM", "POS PVR MOVIE TICKETS", "SPOTIFY INDIA CARD", "MOVIE TICKETS BOOKING UPI",
              "AMAZON PRIME VIDEO ANNUAL", "CONCERT TICKETS ONLINE"],
        "C": ["BookMyShow", "Disney Hotstar", "PlayStation store", "Inox", "YouTube Premium",
              "Bowling alley outing"],
    },
    "Bills": {
        "A": ["Electricity bill payment", "Water bill", "Internet bill broadband", "Mobile recharge prepaid",
              "Gas bill", "Electricity bill TSSPDCL"],
        "B": ["UPI-BESCOM-ELECTRICITY BILL", "BILLDESK WATER BILL", "AIRTEL MOBILE RECHARGE",
              "INTERNET BILL ACT UPI", "GAS BILL INDANE UPI", "MOBILE RECHARGE JIO"],
        "C": ["Jio 599 plan", "Airtel postpaid", "ACT Fibernet", "Tata Power", "Piped gas Mahanagar",
              "Tata Play DTH"],
    },
    "Shopping": {
        "A": ["Amazon purchase headphones", "Flipkart order shoes", "Clothing store jeans", "Myntra order kurta",
              "Electronics store charger", "Amazon purchase kitchen items"],
        "B": ["UPI-AMAZON-PAY-8821", "FLIPKART INTERNET PVT POS", "MYNTRA DESIGNS ONLINE",
              "CLOTHING STORE POS 7712", "ELECTRONICS STORE BILL", "AMAZON PURCHASE UPI"],
        "C": ["Ajio order", "Nykaa cosmetics", "Decathlon sports shoes", "Croma laptop bag", "Reliance Trends",
              "IKEA lamp"],
    },
    "Education": {
        "A": ["Tuition fee installment", "Online course enrollment", "Textbooks for semester", "School fee term 2",
              "Udemy course python", "Tuition fee"],
        "B": ["UPI-UDEMY-ONLINE COURSE", "SCHOOL FEE NEFT PAYMENT", "TUITION FEE UPI COACHING",
              "TEXTBOOKS POS BOOKSTORE", "ONLINE COURSE COURSERA CARD", "SCHOOL FEE ONLINE"],
        "C": ["Coursera subscription", "College exam fee", "NPTEL certification fee", "Byjus plan",
              "Notebook and stationery", "GATE coaching"],
    },
    "Healthcare": {
        "A": ["Hospital visit", "Pharmacy medicines", "Doctor consultation fee", "Medical insurance premium",
              "Dental checkup", "Pharmacy order"],
        "B": ["POS PHARMACY JUBILEE HILLS", "UPI-HOSPITAL-BILL", "DOCTOR CONSULTATION UPI",
              "MEDICAL INSURANCE PREMIUM ECS", "DENTAL CHECKUP CLINIC", "PHARMACY UPI 3321"],
        "C": ["Apollo Pharmacy", "MedPlus", "Lab blood test", "Practo consult", "Physiotherapy session",
              "1mg medicines"],
    },
    "Rent": {
        "A": ["Monthly rent", "House rent October", "Apartment rent", "Rent payment to landlord", "Flat rent",
              "Monthly house rent"],
        "B": ["UPI-RENT-LANDLORD", "NEFT HOUSE RENT", "RENT PAYMENT NEFT", "APARTMENT RENT TRANSFER",
              "MONTHLY RENT UPI", "HOUSE RENT IMPS"],
        "C": ["PG accommodation charges", "NoBroker payment", "Hostel room charges", "Paying guest fee",
              "Room rental advance", "Lease payment"],
    },
    "Travel": {
        "A": ["Flight tickets Delhi", "Hotel booking Goa", "Holiday package Kerala", "Train tickets Chennai",
              "Flight tickets return", "Hotel booking weekend"],
        "B": ["UPI-MAKEMYTRIP-FLIGHT TICKETS", "POS HOTEL BOOKING", "IRCTC TRAIN TICKETS",
              "HOLIDAY PACKAGE ONLINE", "FLIGHT TICKETS CARD", "HOTEL BOOKING OYO UPI"],
        "C": ["IRCTC booking", "Goibibo", "Airbnb stay", "Visa fee", "Cleartrip", "Thomas Cook tour"],
    },
    "Investments": {
        "A": ["Mutual fund SIP", "Stock purchase", "Fixed deposit", "Mutual fund SIP monthly",
              "Stock purchase Infosys", "Fixed deposit renewal"],
        "B": ["UPI-ZERODHA-STOCK PURCHASE", "SIP MUTUAL FUND ECS", "FIXED DEPOSIT BOOKING",
              "MUTUAL FUND SIP NACH", "STOCK PURCHASE GROWW", "FIXED DEPOSIT HDFC"],
        "C": ["Zerodha funds added", "PPF deposit", "Groww investment", "NPS contribution",
              "Sovereign gold bond", "Gold ETF units"],
    },
    "Salary": {
        "A": ["Salary credited", "Monthly salary", "Freelance payment", "Salary credited October",
              "Monthly salary Q3", "Freelance payment website"],
        "B": ["NEFT SALARY CREDITED", "SALARY CREDIT ECS", "NEFT-SALARY CREDITED OCT", "FREELANCE PAYMENT UPI",
              "IMPS MONTHLY SALARY", "SALARY CREDITED NACH"],
        "C": ["Payroll credit", "Stipend", "Consulting fee received", "Bonus credited", "Wages transfer",
              "Pay slip credit"],
    },
}

# Questions for the rule-based assistant (answerable = a figure can be computed from the user's own data).
ASSISTANT_QUESTIONS: list[tuple[str, bool]] = [
    ("Where am I spending the most money?", True),
    ("Where is my spending going?", True),
    ("How much did I spend on Food?", True),
    ("how much did i spend on transport", True),
    ("What did I spend on Entertainment?", True),
    ("Can I save 5000 this month?", True),
    ("Can I save ₹10000 this month?", True),
    ("How can I reduce my expenses?", True),
    ("How do I reduce expenses?", True),
    ("What is my financial health?", True),
    ("What's my health score?", True),
    ("Show my score", True),
    ("How much did I spend on groceries?", True),
    ("What is my biggest expense?", True),
    ("Am I overspending on shopping?", True),
    ("How much have I spent on Rent?", True),
    ("How much do I spend on eating out?", True),
    ("What was my largest purchase this month?", True),
    ("Will I run out of money this month?", True),
    ("Which category should I cut first?", True),
    ("Tell me a joke", False),
    ("What is the weather in Hyderabad today?", False),
    ("Who won the cricket match?", False),
    ("What is the capital of France?", False),
    ("Translate hello to Telugu", False),
    ("Write a poem about money", False),
]
