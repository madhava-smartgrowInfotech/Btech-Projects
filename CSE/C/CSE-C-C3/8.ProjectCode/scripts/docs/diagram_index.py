"""Index of the ParkSure design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs/make_diagrams.py into docs/diagrams/ (matplotlib, 150 dpi).
Used by the block-diagram document (11), the full report, the decks and the paper.
Every box mirrors a real module, route, table or function of the product (app/*.py, frontend/src/pages/*).
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Layered architecture of ParkSure: React console, Vite proxy, FastAPI application with 22 routes, the engine and auth modules, SQLite database, and the Stripe and scheduler side services.",
     "The presentation tier is the React console (landing page, login, find parking, my bookings, trust score and five admin pages) served by the Vite development server on port 5403, which proxies every /api request to the FastAPI "
     "application on port 8403. The original vanilla pages in static/ are still served by the same backend. The application tier holds the 22 routes in app/main.py, the JWT and role guards of app/auth.py, the pydantic schemas, "
     "and the Smart Availability Engine in app/engine.py, which owns admission, the hold-back buffer, the haversine nearest-alternate search, the Trust Score and the fee multiplier. SQLAlchemy maps five tables to one SQLite file, parksure.db. "
     "An APScheduler job inside the backend process resets buffers every 30 minutes, and app/stripe_pay.py talks to Stripe Checkout in test mode or falls back to an offline demo checkout."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "End-to-end workflow: search, reserve, pay, arrive, check in (alternate or fail if full), park, check out, trust update and buffer update.",
     "A driver searches a time window and sees, for every location, how many bays can still be reserved. A reservation is admitted only if overlapping bookings plus the buffer stay below capacity, otherwise it is declined with a reason. "
     "The fee is quoted from hours, rate and the driver's trust multiplier, account credit is applied, and payment is confirmed through Stripe or the demo checkout. On arrival the driver checks in. If the lot is physically full the engine "
     "moves the driver to exactly one nearest alternate that has forecast space, or marks the booking failed and credits the fee. At check-out the booking is judged on time or late (ten minutes of grace): the buffer grows and the Trust "
     "Score streak or warning count is updated, which in turn changes the next fee."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0): ParkSure as one process with the driver, the administrator and the payment provider as external entities.",
     "At level 0 the whole product is one process. The driver sends registration and login details, search windows, reservation requests, check-in and check-out actions and receives availability, quotes, booking status, payment links, "
     "messages and the Trust Score. The administrator sends location definitions and reset commands and receives overview figures, the user list, all bookings and the Strategy Insights replay. The payment provider (Stripe, or the built-in demo checkout) "
     "receives the amount and returns the payment confirmation."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: six processes (authentication, availability search, reservation and payment, check-in and arrival handling, check-out and trust, administration and insights) and the data stores.",
     "Level 1 splits the product into six processes. Process 1.0 registers and authenticates users and issues tokens (D1 users). Process 2.0 answers availability searches from locations (D2) and reservations (D3). Process 3.0 admits or declines a reservation, "
     "quotes the fee and creates the payment record (D4). Process 4.0 handles check-in, including the nearest-alternate move and the failed-and-credited outcome. Process 5.0 handles check-out, the buffer update and the trust events (D5). "
     "Process 6.0 serves the administrator: location management, overview, bookings, users and the deterministic Strategy Insights replay over the stored bookings."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: the reservation and payment process 3.0 expanded into suspension check, forecast admission, fee quote, credit application, payment creation and checkout link.",
     "Process 3.1 loads the location and refuses the request when the driver is suspended (stored as a declined booking with the reason). Process 3.2 counts overlapping reserved and active bookings and applies the admission rule overlapping + buffer < capacity; "
     "a failed rule stores a declined booking and returns a conflict. Process 3.3 computes the fee as hours (minimum 0.25) x hourly rate x trust multiplier. Process 3.4 applies any account credit. Process 3.5 stores the reservation and the payment (paid when nothing is due, pending otherwise). "
     "Process 3.6 asks Stripe for a Checkout session or returns the demo confirmation link."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram of the five persisted entities (User, ParkingLocation, Reservation, Payment, TrustEvent) and the engine and API modules that operate on them.",
     "The five SQLAlchemy models carry the data: User (role, trust score, benefit streak, warning count, account credit, suspension time), ParkingLocation (coordinates, capacity, buffer size, hourly price, last buffer reset), "
     "Reservation (window, status, fee, multiplier, check-in and check-out times, decline reason, parent id for alternates), Payment (amount, provider, Stripe identifiers, status) and TrustEvent (kind and detail). "
     "The engine module is shown as a class-like box with its operations (forecast_free, nearest_alternate, record_checkout_trust, suspension_block, quote_fee, reset_buffers_if_due, haversine_km), next to the auth module and the scheduler job. "
     "A user owns many reservations and trust events, a location has many reservations, and a reservation has at most one payment."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_diagram.png",
     "Sequence diagram: reserve, pay, check in, check out and the trust and buffer updates between the driver, the React console, the API, the engine, the database and the payment provider.",
     "The sequence follows one booking. The driver searches, the API returns bookable bays per location, and the reservation request passes the token check, the suspension check and the admission rule before the reservation and payment rows are written and a checkout link is returned. "
     "Payment is confirmed through Stripe or the demo checkout (the API does not make check-in wait for it). When the driver checks in, the engine compares the physically parked count with the capacity and either activates the booking or runs the nearest-alternate search. At check-out the API stamps the time, decides on time or late, grows the buffer on an on-time departure, "
     "and records the benefit or warning in the trust events."),
    ("usecase", "Use-case diagram", "08_use_case.png",
     "Use-case diagram for the driver, the administrator and the payment provider.",
     "The driver can register, log in, search availability, reserve, pay, cancel, check in, check out, view bookings and view the Trust Score. The administrator can additionally manage locations, reset buffers, view the overview, all bookings, the users and Strategy Insights. "
     "The payment provider takes part in the pay use case. The include and extend relations show that reserving includes the availability and suspension checks and that check-in extends to the alternate move when the lot is full."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram of the SQLite database: users, parking_locations, reservations, payments and trust_events with keys and cardinalities.",
     "The database has five tables. users 1-N reservations and 1-N trust_events; parking_locations 1-N reservations; reservations 1-1 payments (unique reservation_id); payments also reference the paying user. "
     "Reservations carry a status (reserved, active, completed, cancelled, failed, declined) and an optional parent_id that links an automatically created alternate booking to the booking it replaced; that link is stored as a plain integer, not a foreign key. "
     "Indexes exist on the user, location, start and end columns that the overlap query uses."),
    ("algo", "Flowchart of the core algorithm", "10_flowchart_algorithm.png",
     "Flowchart of the Smart Availability Engine: suspension check, admission rule, fee quote, arrival check, nearest-alternate search, departure check, buffer growth and trust update.",
     "The flowchart combines the two decisions the engine makes. At request time: suspended? then refuse; overlapping + buffer < capacity? otherwise decline; else quote and book. At arrival time: parked >= capacity? then search the nearest other location with forecast space by haversine distance, "
     "book it as an active alternate, or mark the booking failed and credit the fee. At departure time: end + 10 minutes passed? A late departure records a warning and resets the benefit streak; an on-time departure grows the buffer (up to 5) and records a benefit, and three benefits raise the trust score."),
    ("state", "Reservation state diagram", "11_reservation_state.png",
     "State diagram of a reservation: reserved, active, completed, cancelled, failed and declined, with the events that cause each transition.",
     "A request that fails the suspension or admission checks is stored directly as declined. An admitted request starts as reserved. Cancel moves it to cancelled and refunds a paid fee to account credit. Check-in moves it to active, or to failed when the lot is full "
     "and either an alternate booking is created (which starts as active) or no alternate exists. Check-out moves an active booking to completed. Completed, cancelled, failed and declined are final."),
    ("reward", "Trust Score and buffer policy", "12_trust_buffer_policy.png",
     "Trust Score state machine (benefit streak, warning count, score 0-5, fee multiplier, suspension rule) and the per-location buffer policy (initial value, growth, cap and daily reset).",
     "The left half shows a driver's score between 0 and 5, starting at 3. An on-time checkout adds a benefit; three consecutive benefits add one point (cap 5). A late checkout resets the streak and adds a warning; two warnings subtract one point (floor 0). "
     "The score selects the fee multiplier from 1.75 (score 0) to 0.90 (score 5), and a score below 1.5 with a warning in the last 14 days suspends booking for 24 hours at a time. "
     "The right half shows a location's buffer: it starts at 1, grows by one on every on-time checkout up to 5, and a scheduler job running every 30 minutes resets it to 1 once 24 hours have passed since the last reset."),
]
