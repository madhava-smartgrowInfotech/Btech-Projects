"""Build data/question_bank.json from the Kaggle aptitude CSVs plus original technical MCQs.

- Topic tags come from keyword rules, difficulty from a deterministic length/number heuristic
  (terciles within each source file), explanations from a per-topic method hint + the answer key.
- Deterministic - no randomness:  python scripts/build_question_bank.py
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APT = ROOT / "data" / "aptitude"
OUT = ROOT / "data" / "question_bank.json"

QUANT_RULES = [
    ("Profit & Loss", r"profit|loss|cost price|selling price|discount|marked price"),
    ("Interest", r"interest|principal|compound"),
    ("Time & Work", r"\bwork\b|days|pipe|tank|cistern|finish"),
    ("Speed & Distance", r"speed|km|train|distance|boat|stream|hour"),
    ("Ratio & Partnership", r"ratio|partnership|share|proportion"),
    ("Percentages", r"percent|%"),
    ("Averages & Ages", r"average|\bage\b|ages|years old"),
    ("Probability & Counting", r"probability|ways|arrange|dice|coin|cards"),
]
LOGIC_RULES = [
    ("Number Series", r"series|next number|come next|missing number"),
    ("Coding-Decoding", r"\bcode|coded|coding"),
    ("Blood Relations", r"father|mother|brother|sister|\bson\b|daughter|uncle|aunt|grand"),
    ("Directions", r"north|south|east|west|direction"),
    ("Analogies", r"related|analogy|similar|same way|pair"),
    ("Statements & Arguments", r"statement|argument|conclusion|assumption"),
]
TECH_RULES = [
    ("DBMS", r"sql|database|dbms|normal form|relation|tuple|query|primary key|foreign key|transaction"),
    ("Operating Systems", r"process|thread|deadlock|paging|memory|scheduling|semaphore|kernel|operating system"),
    ("Computer Networks", r"tcp|udp|\bip\b|osi|protocol|router|network|http|dns|mac address"),
]
HINTS = {
    "Profit & Loss": "Work from the cost price: profit% = profit / CP x 100 and SP = CP x (1 + p/100).",
    "Interest": "Simple interest = P x R x T / 100; compound amount = P (1 + R/100)^T.",
    "Time & Work": "Convert each rate to work-per-day (1/days), add rates for people working together, then invert.",
    "Speed & Distance": "Use distance = speed x time; convert km/h to m/s with x 5/18; add or subtract speeds for relative motion.",
    "Ratio & Partnership": "Scale the ratio parts to the total; in partnerships profit is shared in proportion to capital x time.",
    "Percentages": "Express the change as a fraction of the original value and compare before and after amounts.",
    "Averages & Ages": "Average = total / count - set up the totals as equations and solve for the unknown.",
    "Probability & Counting": "Count favourable outcomes over total outcomes; use nCr for selections and nPr for arrangements.",
    "Number System & Algebra": "Form the equation from the statement and simplify step by step; check each option if stuck.",
    "Number Series": "Look at the differences (or ratios) between consecutive terms and continue the pattern.",
    "Coding-Decoding": "Map each letter of the example to its code and apply the same shift or substitution to the target word.",
    "Blood Relations": "Draw a small family tree from the statement, marking generations and genders.",
    "Directions": "Sketch the moves on a grid starting from the origin, turning left/right relative to the current heading.",
    "Analogies": "Identify how the first pair is related and find the option with the same relationship.",
    "Statements & Arguments": "Accept only what follows directly from the given statements - no outside assumptions.",
    "Logical Reasoning": "Break the statement into facts, eliminate options that contradict any fact.",
    "Data Structures & Algorithms": "Recall the defining property and time complexity of the structure or algorithm involved.",
    "DBMS": "Recall the relational-model definition involved (keys, normal forms, SQL semantics, ACID).",
    "Operating Systems": "Recall the OS concept involved (process scheduling, synchronisation, memory management).",
    "Computer Networks": "Place the concept in its OSI/TCP-IP layer and recall the protocol's behaviour.",
    "Programming": "Trace the code or recall the language rule step by step.",
}

# Original technical MCQs: (topic, question, [A, B, C, D], answer_index, explanation, difficulty)
ORIGINAL = [
    ("DBMS", "Which normal form removes partial dependency of non-key attributes on a composite key?", ["1NF", "2NF", "3NF", "BCNF"], 1, "2NF requires every non-key attribute to depend on the whole candidate key, which removes partial dependencies.", "Medium"),
    ("DBMS", "Which SQL clause filters groups produced by GROUP BY?", ["WHERE", "HAVING", "ORDER BY", "LIMIT"], 1, "WHERE filters rows before grouping; HAVING filters the groups after aggregation.", "Easy"),
    ("DBMS", "The 'I' in ACID stands for:", ["Integrity", "Isolation", "Indexing", "Idempotence"], 1, "ACID = Atomicity, Consistency, Isolation, Durability. Isolation keeps concurrent transactions from seeing each other's partial work.", "Easy"),
    ("DBMS", "A foreign key is used to:", ["Speed up queries", "Uniquely identify every row", "Enforce referential integrity between tables", "Encrypt a column"], 2, "A foreign key references a key in another table, so rows cannot point to non-existent parents.", "Easy"),
    ("DBMS", "Which join returns all rows of the left table and matching rows of the right table?", ["INNER JOIN", "LEFT OUTER JOIN", "CROSS JOIN", "SELF JOIN"], 1, "A LEFT OUTER JOIN keeps every left row and fills unmatched right columns with NULL.", "Easy"),
    ("DBMS", "Which index structure is used by most relational databases for range queries?", ["Hash index", "B+ tree", "Bitmap only", "Linked list"], 1, "B+ trees keep keys sorted with linked leaves, so range scans are efficient.", "Medium"),
    ("DBMS", "COUNT(column) differs from COUNT(*) because COUNT(column):", ["Counts duplicates twice", "Ignores NULL values", "Only works on numbers", "Is always faster"], 1, "COUNT(column) counts non-NULL values of that column, while COUNT(*) counts rows.", "Medium"),
    ("DBMS", "A schedule of transactions is conflict-serializable if its precedence graph:", ["Has a cycle", "Is acyclic", "Is complete", "Has one node"], 1, "Conflict serializability holds exactly when the precedence (serialization) graph has no cycle.", "Hard"),
    ("DBMS", "Which command removes all rows from a table but keeps its structure, and usually cannot be rolled back in many systems?", ["DELETE", "DROP", "TRUNCATE", "ALTER"], 2, "TRUNCATE deallocates all rows quickly and keeps the table definition; DROP removes the table itself.", "Medium"),
    ("DBMS", "In an ER model, a weak entity is one that:", ["Has no attributes", "Cannot be identified without its owner entity", "Has only one row", "Is never stored"], 1, "A weak entity has no key of its own and is identified through its relationship with an owner entity.", "Medium"),
    ("DBMS", "Which isolation level prevents dirty reads but still allows non-repeatable reads?", ["Read Uncommitted", "Read Committed", "Repeatable Read", "Serializable"], 1, "Read Committed only shows committed data, but a re-read may see another transaction's newer commit.", "Hard"),
    ("DBMS", "A candidate key is:", ["Any column with NULLs", "A minimal set of attributes that uniquely identifies a row", "The first column of a table", "A key used only for sorting"], 1, "Candidate keys are minimal super keys; one of them is chosen as the primary key.", "Easy"),
    ("Operating Systems", "Which of these is NOT a necessary condition for deadlock?", ["Mutual exclusion", "Hold and wait", "Preemption", "Circular wait"], 2, "The Coffman conditions include NO preemption; allowing preemption breaks deadlock.", "Medium"),
    ("Operating Systems", "Which scheduling algorithm can cause starvation of long jobs?", ["Round Robin", "First Come First Served", "Shortest Job First", "FIFO"], 2, "SJF keeps picking short jobs, so a long job may wait indefinitely if short jobs keep arriving.", "Medium"),
    ("Operating Systems", "Threads of the same process share:", ["Stack", "Registers", "Address space (code, data, heap)", "Program counter"], 2, "Each thread has its own stack, registers and PC but shares the process's code, data and heap.", "Easy"),
    ("Operating Systems", "A page fault occurs when:", ["The CPU overheats", "A referenced page is not in main memory", "A process finishes", "The disk is full"], 1, "The MMU raises a page fault when the page table entry is not present; the OS loads the page from disk.", "Easy"),
    ("Operating Systems", "Belady's anomaly can occur with which page replacement algorithm?", ["LRU", "Optimal", "FIFO", "LFU with aging"], 2, "With FIFO, adding frames can increase page faults; stack algorithms like LRU and Optimal do not suffer this.", "Hard"),
    ("Operating Systems", "A counting semaphore initialised to 3 allows at most how many processes in the critical region at once?", ["1", "2", "3", "Unlimited"], 2, "Each wait() decrements the count; the fourth caller blocks when it reaches zero.", "Easy"),
    ("Operating Systems", "Thrashing happens when:", ["The CPU is idle waiting for I/O only", "Processes spend more time paging than executing", "Too few processes are loaded", "Cache is disabled"], 1, "When working sets exceed physical memory, the system constantly swaps pages and throughput collapses.", "Medium"),
    ("Operating Systems", "Which system call creates a new process in UNIX?", ["exec()", "fork()", "wait()", "exit()"], 1, "fork() duplicates the calling process; exec() replaces the program image of an existing process.", "Easy"),
    ("Operating Systems", "Internal fragmentation is typical of:", ["Paging with fixed-size frames", "Pure segmentation", "Linked allocation", "Contiguous variable partitions"], 0, "Fixed-size frames waste the unused tail of the last page of each process.", "Medium"),
    ("Operating Systems", "Banker's algorithm is used for:", ["Deadlock avoidance", "Deadlock detection only", "Disk scheduling", "Page replacement"], 0, "It grants a request only if the system stays in a safe state, avoiding deadlock.", "Medium"),
    ("Operating Systems", "A context switch saves and restores:", ["Only the disk contents", "The process state such as registers and program counter", "The whole main memory", "Only open files"], 1, "The CPU state (registers, PC, stack pointer) is saved in the PCB of the outgoing process.", "Easy"),
    ("Operating Systems", "Which disk scheduling algorithm services requests in one direction and then jumps back to the start?", ["SSTF", "SCAN", "C-SCAN", "FCFS"], 2, "C-SCAN moves in one direction only and returns to the beginning without servicing, giving uniform wait.", "Hard"),
    ("Computer Networks", "Which layer of the OSI model is responsible for routing?", ["Data link", "Network", "Transport", "Session"], 1, "The network layer (IP) chooses paths between networks.", "Easy"),
    ("Computer Networks", "TCP differs from UDP because TCP:", ["Is connectionless", "Provides reliable, ordered delivery", "Has no headers", "Cannot be used on the internet"], 1, "TCP uses a handshake, sequence numbers, acknowledgements and retransmission for reliable ordered delivery.", "Easy"),
    ("Computer Networks", "How many usable host addresses does a /26 IPv4 subnet have?", ["62", "64", "30", "126"], 0, "A /26 has 2^6 = 64 addresses; minus network and broadcast leaves 62.", "Medium"),
    ("Computer Networks", "DNS primarily translates:", ["MAC to IP", "Domain names to IP addresses", "IP to port numbers", "HTTP to HTTPS"], 1, "DNS resolves human-readable names like example.com to IP addresses.", "Easy"),
    ("Computer Networks", "Which protocol maps an IP address to a MAC address on a LAN?", ["ARP", "ICMP", "DHCP", "FTP"], 0, "ARP broadcasts 'who has this IP' and the owner replies with its MAC address.", "Easy"),
    ("Computer Networks", "The TCP three-way handshake sequence is:", ["SYN, ACK, FIN", "SYN, SYN-ACK, ACK", "ACK, SYN, ACK", "SYN, FIN, ACK"], 1, "Client sends SYN, server replies SYN-ACK, client confirms with ACK.", "Easy"),
    ("Computer Networks", "Which HTTP status code means the resource was not found?", ["200", "301", "404", "500"], 2, "404 Not Found; 5xx codes are server errors.", "Easy"),
    ("Computer Networks", "TCP congestion control's 'slow start' phase grows the congestion window:", ["Linearly", "Exponentially per RTT", "Not at all", "Randomly"], 1, "In slow start the window doubles each round-trip until it reaches the threshold.", "Hard"),
    ("Computer Networks", "Which device operates mainly at the data link layer?", ["Router", "Switch", "Hub", "Gateway"], 1, "A switch forwards frames using MAC addresses (layer 2); hubs are layer 1, routers layer 3.", "Medium"),
    ("Computer Networks", "Which protocol automatically assigns IP addresses to hosts?", ["DNS", "DHCP", "SMTP", "SNMP"], 1, "DHCP leases IP address, gateway and DNS settings to clients.", "Easy"),
    ("Computer Networks", "Default port for HTTPS is:", ["80", "21", "443", "25"], 2, "HTTPS uses TCP port 443; HTTP uses 80.", "Easy"),
    ("Computer Networks", "Sliding window protocols are used for:", ["Encryption", "Flow control", "Routing", "Name resolution"], 1, "The window limits unacknowledged data in flight so a fast sender cannot overwhelm a receiver.", "Medium"),
    ("Programming", "What is the time complexity of binary search on a sorted array of n elements?", ["O(n)", "O(log n)", "O(n log n)", "O(1)"], 1, "Each step halves the search range, giving log2(n) steps.", "Easy"),
    ("Programming", "In Python, what does `[1, 2, 3][::-1]` evaluate to?", ["[1, 2, 3]", "[3, 2, 1]", "[3]", "Error"], 1, "A slice step of -1 walks the list backwards, producing a reversed copy.", "Easy"),
    ("Programming", "In Java, which keyword prevents a class from being subclassed?", ["static", "final", "private", "sealed only"], 1, "A final class cannot be extended.", "Easy"),
    ("Programming", "In C++, what happens when you access a vector element with `v.at(i)` and i is out of range?", ["Undefined behaviour", "Returns 0", "Throws std::out_of_range", "Compilation error"], 2, "at() is bounds-checked and throws std::out_of_range; operator[] is unchecked.", "Medium"),
    ("Programming", "Which OOP principle lets a subclass provide its own version of a parent method?", ["Encapsulation", "Overriding (runtime polymorphism)", "Abstraction", "Overloading"], 1, "Overriding replaces an inherited method's behaviour and is resolved at runtime.", "Easy"),
    ("Programming", "What is the output of `print(0.1 + 0.2 == 0.3)` in Python?", ["True", "False", "Error", "None"], 1, "Binary floating point cannot represent 0.1 and 0.2 exactly, so the sum is 0.30000000000000004.", "Medium"),
    ("Programming", "Which data structure gives O(1) average lookup by key?", ["Linked list", "Hash table", "Binary search tree", "Stack"], 1, "Hash tables compute the bucket directly from the key's hash.", "Easy"),
    ("Programming", "A function that calls itself without a base case will eventually:", ["Return 0", "Run forever with no effect", "Overflow the call stack", "Be optimised away always"], 2, "Each call adds a stack frame; without a base case the stack overflows (RecursionError in Python).", "Easy"),
    ("Programming", "In Java, `String` objects are:", ["Mutable", "Immutable", "Primitive types", "Always null"], 1, "Java Strings are immutable; operations create new String objects (use StringBuilder for mutation).", "Easy"),
    ("Programming", "What is the worst-case time complexity of quicksort?", ["O(n log n)", "O(n^2)", "O(n)", "O(log n)"], 1, "Consistently bad pivots (e.g. already sorted input with first-element pivot) give n levels of O(n) work.", "Medium"),
    ("Programming", "In Python, a mutable default argument like `def f(a=[])`:", ["Is recreated on every call", "Is shared between calls", "Raises a SyntaxError", "Is converted to a tuple"], 1, "Default values are evaluated once at definition time, so the same list is reused across calls.", "Hard"),
    ("Programming", "Which traversal of a binary search tree yields keys in sorted order?", ["Preorder", "Inorder", "Postorder", "Level order"], 1, "Inorder visits left subtree, node, right subtree - ascending order for a BST.", "Easy"),
]


def tag(text, rules, default):
    t = text.lower()
    for name, pat in rules:
        if re.search(pat, t):
            return name
    return default


def difficulty_labels(rows):
    scores = [len(r["q"].split()) + 3 * len(re.findall(r"\d+", r["q"])) for r in rows]
    order = sorted(scores)
    lo, hi = order[len(order) // 3], order[2 * len(order) // 3]
    return ["Easy" if s <= lo else "Medium" if s <= hi else "Hard" for s in scores]


def load_csv(name):
    rows = []
    with open(APT / name, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            ans = (r.get("Answer") or "").strip().upper()[:1]
            opts = [(r.get(k) or "").strip() for k in ("Option A", "Option B", "Option C", "Option D")]
            q = (r.get("Question") or "").strip()
            if ans not in "ABCD" or not ans or not q or not all(opts):
                continue
            rows.append({"q": q, "options": opts, "answer": "ABCD".index(ans)})
    return rows


def main():
    bank = []
    sources = [
        ("clean_general_aptitude_dataset.csv", "aptitude", QUANT_RULES, "Number System & Algebra"),
        ("logical_reasoning_questions.csv", "aptitude", LOGIC_RULES, "Logical Reasoning"),
        ("cse_dataset.csv", "technical", TECH_RULES, "Data Structures & Algorithms"),
    ]
    for fname, kind, rules, default in sources:
        rows = load_csv(fname)
        for r, diff in zip(rows, difficulty_labels(rows)):
            topic = tag(r["q"], rules, default)
            letter = "ABCD"[r["answer"]]
            bank.append({
                "kind": kind, "topic": topic, "difficulty": diff, "text": r["q"], "options": r["options"],
                "answer": r["answer"], "source": f"kaggle:{fname}",
                "explanation": f"Correct answer: ({letter}) {r['options'][r['answer']]}. Method: {HINTS[topic]}",
            })
    for topic, q, opts, ans, expl, diff in ORIGINAL:
        bank.append({"kind": "technical", "topic": topic, "difficulty": diff, "text": q, "options": opts,
                     "answer": ans, "source": "original", "explanation": expl})
    OUT.write_text(json.dumps(bank, indent=1, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    c = Counter((b["kind"], b["topic"]) for b in bank)
    for k, v in sorted(c.items()):
        print(f"{k[0]:10s} {k[1]:30s} {v}")
    print(f"total {len(bank)} -> {OUT}")


if __name__ == "__main__":
    main()
