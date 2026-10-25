"""
Hand-written evaluation questions for the notes corpus built by scripts/fetch_corpus.py.

Each item: (subject, type, question, evidence, answer_any)
  type        fact / definition / reasoning, the three question types of the SAC-RAG base paper, assigned
              from the wording of the question (When/Which/How many -> fact, What is/Define -> definition,
              Why/How -> reasoning).
  evidence    a sentence fragment copied from the corpus. A retrieved chunk "hits" when it contains it.
  answer_any  short strings; a generated answer "contains the key" when it contains any of them.

Run `python scripts/eval_questions.py` to check that every evidence string exists exactly in its subject file.
"""
import os
import re
import sys

F, D, R = "fact", "definition", "reasoning"

QUESTIONS = [
    # ---- Data Structures
    ("Data Structures", F, "Which stack operation removes the most recently added element?", "Pop, which removes the most recently added element", ["pop"]),
    ("Data Structures", F, "What is the front of a queue called, where items are removed?", "called the head or front of the queue", ["head or front", "front"]),
    ("Data Structures", F, "What does each node in a basic linked list contain?", "each node contains data, and a reference", ["reference"]),
    ("Data Structures", F, "Which two collision resolution strategies are most common in hash tables?", "The two common methods for collision resolution are separate chaining and open addressing", ["separate chaining", "open addressing"]),
    ("Data Structures", D, "What is a binary search tree?", "with the key of each internal node being greater than all the keys in the respective node's left subtree", ["left subtree"]),
    ("Data Structures", D, "Define a hash table.", "a hash table is a data structure that implements an associative array", ["associative array"]),
    ("Data Structures", D, "What is the heap property?", "In a max heap, for any given node C", ["max heap", "parent"]),
    ("Data Structures", D, "What does LIFO mean for a stack?", "last in, first out, referred to by the acronym LIFO", ["last in"]),
    ("Data Structures", R, "Why is inserting in the middle of a linked list cheaper than in an array?", "is a constant-time operation (otherwise without this reference it is O(n))", ["constant"]),
    ("Data Structures", R, "Why can a binary search tree become as slow as a linked list?", "an unbalanced BST may degenerate to a linked list", ["unbalanced", "degenerate"]),
    ("Data Structures", R, "Why do hash tables have to handle collisions?", "where the hash function generates the same index for more than one key", ["same index"]),
    ("Data Structures", R, "How is a stack used to support function calls?", "to hold information about procedure/function calling and nesting", ["call stack"]),
    # ---- Operating Systems
    ("Operating Systems", F, "What are the four necessary conditions for a deadlock called?", "These four conditions are known as the Coffman conditions", ["coffman"]),
    ("Operating Systems", F, "Which algorithm is one of the most used for deadlock avoidance?", "One of the most used deadlock avoidance algorithms is Banker's algorithm", ["banker"]),
    ("Operating Systems", F, "Who invented the semaphore and when?", "invented by Dutch computer scientist Edsger Dijkstra in 1962 or 1963", ["dijkstra"]),
    ("Operating Systems", F, "Which page replacement algorithm is often used to choose the page to evict?", "often through the least recently used (LRU) algorithm", ["lru", "least recently used"]),
    ("Operating Systems", D, "What is a deadlock?", "deadlock is any situation in which no member of some group of entities can proceed because each waits for another member", ["waits for another", "no member"]),
    ("Operating Systems", D, "What is a page fault?", "the processor treats this invalid memory reference as a page fault", ["not currently mapped", "page frame"]),
    ("Operating Systems", D, "What is thrashing?", "Thrashing occurs on a program that works with huge data structures, as its large working set causes continual page faults", ["page faults", "working set"]),
    ("Operating Systems", D, "What is the difference between counting and binary semaphores?", "semaphores that are restricted to the values 0 and 1", ["0 and 1"]),
    ("Operating Systems", R, "Why does round-robin scheduling never cause starvation?", "Starvation can never occur, since no priority is given", ["no priority", "never"]),
    ("Operating Systems", R, "Why should unnecessary context switches be avoided?", "During the context switches, the processor is virtually idle for a fraction of time", ["idle"]),
    ("Operating Systems", R, "How can the hold and wait condition of a deadlock be removed?", "requiring processes to request all the resources they will need before starting up", ["request all"]),
    ("Operating Systems", R, "Why does virtual memory give the illusion of a very large memory?", "creates the illusion to users of a very large (main) memory", ["illusion"]),
    # ---- Database Systems
    ("Database Systems", F, "Who proposed the relational model and in what year?", "first described in 1969 by English computer scientist Edgar F. Codd", ["codd"]),
    ("Database Systems", F, "Who coined the acronym ACID and when?", "In 1983, Andreas Reuter and Theo Härder coined the acronym ACID", ["reuter", "härder", "1983"]),
    ("Database Systems", F, "In which year did Codd introduce the first normal form?", "Codd introduced the concept of normalization and what is now known as the first normal form (1NF) in 1970", ["1970"]),
    ("Database Systems", F, "Which kind of locking is often applied to guarantee full isolation?", "Two-phase locking is often applied to guarantee full isolation", ["two-phase locking"]),
    ("Database Systems", D, "What is database normalization?", "process of structuring a relational database in accordance with a series of normal forms to reduce data redundancy", ["redundancy"]),
    ("Database Systems", D, "What is a database index?", "a data structure that improves the speed of data retrieval operations on a database table", ["speed of data retrieval"]),
    ("Database Systems", D, "What is a B-tree?", "a B-tree is a self-balancing tree data structure that maintains sorted data", ["self-balancing"]),
    ("Database Systems", D, "What does durability guarantee?", "once a transaction has been committed, it will remain committed even in the case of a system failure", ["remain committed"]),
    ("Database Systems", R, "Why does a B-tree need fewer disk blocks than a binary tree?", "the B-tree reduces the height of the tree and puts the data in fewer separate blocks", ["height"]),
    ("Database Systems", R, "How does write-ahead logging guarantee durability?", "durability is guaranteed by writing the prospective change to a persistent log before changing the database", ["log"]),
    ("Database Systems", R, "Why is the update anomaly a problem in tables that are not normalized?", "The same information can be expressed on multiple rows; therefore updates to the relation may result in logical inconsistencies", ["inconsisten"]),
    ("Database Systems", R, "How does isolation keep concurrent transactions correct?", "Isolation ensures that concurrent execution of transactions leaves the database in the same state that would have been obtained if the transactions were executed sequentially", ["sequentially"]),
    # ---- Computer Networks
    ("Computer Networks", F, "Which layer of the TCP/IP suite does TCP belong to?", "which is part of the transport layer of the TCP/IP suite", ["transport"]),
    ("Computer Networks", F, "When was the OSI model published and by which organization?", "published in 1984 by the International Organization for Standardization", ["1984", "iso"]),
    ("Computer Networks", F, "Which servers serve the top of the DNS hierarchy?", "The top of the hierarchy is served by the root name servers", ["root name servers"]),
    ("Computer Networks", F, "What is the stable low-throughput state of a congested network called?", "The stable state with low throughput is known as congestive collapse", ["congestive collapse"]),
    ("Computer Networks", D, "What is TCP?", "providing reliable, ordered, and error-checked delivery", ["reliable"]),
    ("Computer Networks", D, "What is routing?", "Routing is the process of selecting a path for traffic in a network", ["selecting a path"]),
    ("Computer Networks", D, "What is DHCP used for?", "for automatically assigning IP addresses and other communication parameters", ["assigning ip addresses"]),
    ("Computer Networks", D, "What is an authoritative name server?", "An authoritative name server is a name server that only gives answers to DNS queries from data that have been configured by an original source", ["only gives answers", "configured"]),
    ("Computer Networks", R, "Why does TCP use acknowledgments and retransmission?", "Since packet transfer by many networks is not reliable, TCP achieves this using a technique known as positive acknowledgment with re-transmission", ["not reliable", "acknowledgment"]),
    ("Computer Networks", R, "Why might an application use UDP instead of TCP?", "Applications that do not require reliable data stream service may use the User Datagram Protocol (UDP) instead", ["do not require reliable"]),
    ("Computer Networks", R, "How does a client begin a TCP connection?", "a client may establish a connection by initiating an active open using the three-way", ["active open", "syn"]),
    ("Computer Networks", R, "How do networks try to avoid congestive collapse?", "Networks use congestion control and congestion avoidance techniques to try to avoid collapse", ["congestion control"]),
    # ---- Machine Learning
    ("Machine Learning", F, "At which laboratory was the support vector machine developed?", "Developed at AT&T Bell Laboratories", ["bell"]),
    ("Machine Learning", F, "What are tree models with a discrete target variable called?", "Tree models where the target variable can take a discrete set of values are called classification trees", ["classification trees"]),
    ("Machine Learning", F, "Which technique lets SVMs perform non-linear classification?", "SVMs can efficiently perform non-linear classification using the kernel trick", ["kernel trick"]),
    ("Machine Learning", F, "Which method is suggested for choosing learning rates economically?", "A more economic way of choosing learning rates is backtracking line search", ["backtracking line search"]),
    ("Machine Learning", D, "What is overfitting?", "overfitting is the production of an analysis that corresponds too closely or exactly to a particular set of data", ["too closely"]),
    ("Machine Learning", D, "What is gradient descent?", "It is a first-order iterative algorithm for minimizing a differentiable multivariate function", ["first-order", "minimizing"]),
    ("Machine Learning", D, "What does the naive Bayes classifier assume?", "assume that the features are conditionally independent", ["conditionally independent"]),
    ("Machine Learning", D, "What is k-means clustering?", "aims to partition n observations into k clusters", ["partition"]),
    ("Machine Learning", R, "Why is regularization used to prevent overfitting?", "adding a penalty term to the loss function that discourages large parameter values", ["penalty"]),
    ("Machine Learning", R, "How can gradient descent get stuck?", "get stuck in some hole (i.e., local minimum or saddle point)", ["local minimum", "saddle"]),
    ("Machine Learning", R, "Why does naive Bayes often give overconfident probabilities?", "with naive Bayes models often producing wildly overconfident probabilities", ["overconfident", "independen"]),
    ("Machine Learning", R, "How does underfitting differ from overfitting in terms of bias and variance?", "A sign of underfitting is that there is a high bias and low variance", ["high bias"]),
    # ---- Algorithms
    ("Algorithms", F, "Who invented merge sort and when?", "invented by John von Neumann in 1945", ["von neumann"]),
    ("Algorithms", F, "Who developed quicksort?", "Quicksort was developed by British computer scientist Tony Hoare in 1959", ["hoare"]),
    ("Algorithms", F, "What is the running time of binary search in the worst case?", "Binary search runs in logarithmic time in the worst case", ["logarithmic"]),
    ("Algorithms", F, "Which data structure does Dijkstra's algorithm use to select the next node?", "The algorithm uses a min-priority queue data structure for selecting the shortest paths known so far", ["priority queue"]),
    ("Algorithms", D, "What is dynamic programming?", "Dynamic programming (DP) is both a mathematical optimization method and an algorithmic paradigm", ["optimization method", "paradigm"]),
    ("Algorithms", D, "What is breadth-first search?", "explores all nodes at the present depth prior to moving on to the nodes at the next depth level", ["present depth"]),
    ("Algorithms", D, "What does it mean that merge sort is stable?", "Most implementations of merge sort are stable, which means that the relative order of equal elements is the same between the input and output", ["relative order"]),
    ("Algorithms", D, "What is Dijkstra's algorithm used for?", "an algorithm for finding the shortest paths between nodes in a weighted graph", ["shortest path"]),
    ("Algorithms", R, "Why does breadth-first search need a queue?", "Extra memory, usually a queue, is needed to keep track of the child nodes that were encountered but not yet explored", ["queue"]),
    ("Algorithms", R, "How does binary search discard half of the array in each step?", "the half in which the target cannot lie is eliminated", ["eliminated", "half"]),
    ("Algorithms", R, "Why can some problems be solved by dynamic programming?", "if a problem can be solved optimally by breaking it into sub-problems", ["sub-problems"]),
    ("Algorithms", R, "Why is quicksort often faster than merge sort in practice?", "it is slightly faster than merge sort and heapsort for randomized data", ["slightly faster"]),
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "experiments", "corpus")


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def subject_file(subject):
    for name in sorted(os.listdir(CORPUS)):
        if name[3:-4].replace("_", " ") == subject:
            return os.path.join(CORPUS, name)
    raise KeyError(subject)


def check():
    texts, bad = {}, 0
    for i, (subject, qtype, q, ev, ans) in enumerate(QUESTIONS, 1):
        if subject not in texts:
            with open(subject_file(subject), encoding="utf-8") as f:
                texts[subject] = norm(f.read())
        n = texts[subject].count(norm(ev))
        if n != 1:
            bad += 1
            print(f"Q{i} [{subject}] evidence found {n}x: {ev[:90]}")
    counts = {}
    for s, t, *_ in QUESTIONS:
        counts[t] = counts.get(t, 0) + 1
    print(len(QUESTIONS), "questions", counts, "| bad evidence:", bad)
    return bad


if __name__ == "__main__":
    sys.exit(1 if check() else 0)
