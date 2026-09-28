"""Generate data/problems.json: 30 original coding problems with sample and hidden tests.

Every expected output is produced by running the reference solution on the input,
and every hidden input comes from a seeded random generator, so the file is fully
reproducible:  python scripts/gen_problems.py
"""
import contextlib
import io
import json
import random
import sys
from pathlib import Path

SEED = 2024
OUT = Path(__file__).resolve().parents[1] / "data" / "problems.json"

P = []


def problem(slug, title, difficulty, topic, statement, ref, samples, gen, hidden=8, big=None):
    P.append(dict(slug=slug, title=title, difficulty=difficulty, topic=topic,
                  statement=statement.strip(), ref=ref.strip() + "\n", samples=samples,
                  gen=gen, hidden=hidden, big=big))


def arr(rng, n, lo, hi):
    return " ".join(str(rng.randint(lo, hi)) for _ in range(n))


def word(rng, lo=1, hi=10, alpha="abcdefghijklmnopqrstuvwxyz"):
    return "".join(rng.choice(alpha) for _ in range(rng.randint(lo, hi)))


# ---------------------------------------------------------------- easy
problem("array-sum", "Array Sum", "Easy", "Arrays", """
Given N integers, print their sum.

**Input:** first line N (1 <= N <= 2*10^5); second line N integers (|a_i| <= 10^9).
**Output:** a single integer, the sum.
""", """
import sys
d = sys.stdin.read().split()
n = int(d[0]); print(sum(map(int, d[1:1+n])))
""", ["5\n1 2 3 4 5\n", "3\n-5 10 -2\n"],
    lambda r: (lambda n: f"{n}\n{arr(r, n, -10**9, 10**9)}\n")(r.randint(1, 50)),
    big=lambda r: f"200000\n{arr(r, 200000, -10**9, 10**9)}\n")

problem("reverse-words", "Reverse the Words", "Easy", "Strings", """
Given a line of words separated by single spaces, print the words in reverse order.

**Input:** one line with 1 to 1000 lowercase words.
**Output:** the same words in reverse order, separated by single spaces.
""", """
import sys
print(" ".join(sys.stdin.readline().split()[::-1]))
""", ["the quick brown fox\n", "hello\n"],
    lambda r: " ".join(word(r) for _ in range(r.randint(1, 30))) + "\n")

problem("count-vowels", "Count Vowels", "Easy", "Strings", """
Count how many vowels (a, e, i, o, u - either case) appear in a string.

**Input:** one line of text (up to 10^5 characters, letters and spaces).
**Output:** the number of vowels.
""", """
import sys
s = sys.stdin.readline()
print(sum(1 for c in s.lower() if c in "aeiou"))
""", ["Hello World\n", "rhythm\n"],
    lambda r: " ".join(word(r, 1, 8, "abcdeiouXYZAEIOUqrst") for _ in range(r.randint(1, 20))) + "\n")

problem("second-largest", "Second Largest Distinct", "Easy", "Arrays", """
Print the second largest **distinct** value in the array, or -1 if it does not exist.

**Input:** N (1 <= N <= 10^5), then N integers.
**Output:** the second largest distinct value or -1.
""", """
import sys
d = sys.stdin.read().split(); n = int(d[0])
v = sorted(set(map(int, d[1:1+n])))
print(v[-2] if len(v) >= 2 else -1)
""", ["5\n4 1 7 7 3\n", "3\n2 2 2\n"],
    lambda r: (lambda n: f"{n}\n{arr(r, n, 1, 6)}\n")(r.randint(1, 12)))

problem("palindrome-check", "Palindrome Check", "Easy", "Strings", """
A string is a palindrome if it reads the same forwards and backwards after removing every
non-alphanumeric character and ignoring case. Print YES or NO.

**Input:** one line (up to 10^5 characters).
**Output:** YES or NO.
""", """
import sys
s = [c.lower() for c in sys.stdin.readline() if c.isalnum()]
print("YES" if s == s[::-1] else "NO")
""", ["A man, a plan, a canal: Panama\n", "race a car\n"],
    lambda r: (lambda w: (w + w[::-1] if r.random() < 0.5 else w + word(r, 1, 3)) + "\n")(word(r, 1, 8, "abcAB1, ")))

problem("gcd-lcm", "GCD and LCM", "Easy", "Math", """
For each pair of positive integers print their GCD and LCM.

**Input:** T (1 <= T <= 10^4), then T lines each with a and b (1 <= a, b <= 10^9).
**Output:** for each pair, one line: gcd lcm.
""", """
import sys, math
d = sys.stdin.read().split(); t = int(d[0]); out = []
for i in range(t):
    a, b = int(d[1+2*i]), int(d[2+2*i]); g = math.gcd(a, b); out.append(f"{g} {a//g*b}")
print("\\n".join(out))
""", ["2\n12 18\n7 5\n"],
    lambda r: (lambda t: f"{t}\n" + "".join(f"{r.randint(1, 10**6)} {r.randint(1, 10**6)}\n" for _ in range(t)))(r.randint(1, 10)))

problem("fizzbuzz-sum", "FizzBuzz Count", "Easy", "Math", """
Among the integers 1..N, count how many are divisible by 3 or 5 (or both).

**Input:** one integer N (1 <= N <= 10^18).
**Output:** the count.
""", """
n = int(input())
print(n//3 + n//5 - n//15)
""", ["15\n", "1\n"],
    lambda r: f"{r.randint(1, 10**r.randint(1, 18))}\n")

problem("missing-number", "Missing Number", "Easy", "Arrays", """
The numbers 1..N appear exactly once each except one number that is missing. Find it.

**Input:** N (2 <= N <= 2*10^5), then N-1 distinct integers from 1..N.
**Output:** the missing number.
""", """
import sys
d = sys.stdin.read().split(); n = int(d[0])
print(n*(n+1)//2 - sum(map(int, d[1:n])))
""", ["5\n1 2 4 5\n"],
    lambda r: (lambda n: (lambda v: f"{n}\n{' '.join(map(str, v))}\n")(r.sample(range(1, n+1), n-1)))(r.randint(2, 40)),
    big=lambda r: (lambda v: f"200000\n{' '.join(map(str, v))}\n")(r.sample(range(1, 200001), 199999)))

problem("digit-sum", "Repeated Digit Sum", "Easy", "Math", """
Repeatedly replace a non-negative integer by the sum of its digits until one digit remains. Print it.

**Input:** one integer with up to 1000 digits.
**Output:** the final single digit.
""", """
s = input().strip()
while len(s) > 1:
    s = str(sum(int(c) for c in s))
print(s)
""", ["9875\n", "0\n"],
    lambda r: str(r.randint(0, 9)) if r.random() < 0.1 else "".join(r.choice("0123456789") for _ in range(r.randint(1, 200))).lstrip("0") or "0")

problem("run-length", "Run-Length Encoding", "Easy", "Strings", """
Compress a string by replacing each maximal run of the same character with the character
followed by the run length (e.g. aaabcc -> a3b1c2).

**Input:** one line of lowercase letters (1 to 10^5 characters).
**Output:** the encoded string.
""", """
s = input().strip(); out = []; i = 0
while i < len(s):
    j = i
    while j < len(s) and s[j] == s[i]: j += 1
    out.append(f"{s[i]}{j-i}"); i = j
print("".join(out))
""", ["aaabcc\n", "z\n"],
    lambda r: "".join(r.choice("ab") * r.randint(1, 5) for _ in range(r.randint(1, 15))) + "\n")

# ---------------------------------------------------------------- medium
problem("balanced-brackets", "Balanced Brackets", "Medium", "Stacks", """
Check whether a string of brackets ()[]{} is balanced. Print YES or NO.

**Input:** one line of up to 10^5 bracket characters.
**Output:** YES or NO.
""", """
s = input().strip(); st = []; pair = {')': '(', ']': '[', '}': '{'}; ok = True
for c in s:
    if c in "([{": st.append(c)
    elif not st or st.pop() != pair[c]: ok = False; break
print("YES" if ok and not st else "NO")
""", ["{[()]}\n", "([)]\n"],
    lambda r: (lambda k: (lambda base: base if r.random() < 0.5 else base[:-1] + r.choice(")]}"))("".join(r.choice(["()", "[]", "{}", "([])", "{()}"]) for _ in range(k))))(r.randint(1, 10)) + "\n")

problem("anagram-groups", "Anagram Groups", "Medium", "Hashing", """
Given N words, count how many groups of anagrams there are (words that are rearrangements of each other
belong to the same group).

**Input:** N (1 <= N <= 10^5), then N lowercase words (each up to 20 letters).
**Output:** the number of groups.
""", """
import sys
d = sys.stdin.read().split(); n = int(d[0])
print(len({"".join(sorted(w)) for w in d[1:1+n]}))
""", ["6\neat tea tan ate nat bat\n"],
    lambda r: (lambda n: f"{n}\n" + " ".join("".join(r.sample("abcd", r.randint(1, 3))) for _ in range(n)) + "\n")(r.randint(1, 20)))

problem("max-subarray", "Maximum Subarray Sum", "Medium", "Dynamic Programming", """
Find the largest sum of a non-empty contiguous subarray.

**Input:** N (1 <= N <= 2*10^5), then N integers (|a_i| <= 10^9).
**Output:** the maximum subarray sum.
""", """
import sys
d = sys.stdin.read().split(); n = int(d[0]); a = list(map(int, d[1:1+n]))
best = cur = a[0]
for x in a[1:]:
    cur = max(x, cur + x); best = max(best, cur)
print(best)
""", ["9\n-2 1 -3 4 -1 2 1 -5 4\n", "3\n-3 -1 -2\n"],
    lambda r: (lambda n: f"{n}\n{arr(r, n, -20, 20)}\n")(r.randint(1, 30)),
    big=lambda r: f"200000\n{arr(r, 200000, -10**9, 10**9)}\n")

problem("two-sum-count", "Pairs With Target Sum", "Medium", "Hashing", """
Count pairs of indices i < j with a_i + a_j = K.

**Input:** N and K (1 <= N <= 2*10^5, |K| <= 10^9), then N integers.
**Output:** the number of pairs.
""", """
import sys
from collections import Counter
d = sys.stdin.read().split(); n, k = int(d[0]), int(d[1]); seen = Counter(); c = 0
for x in map(int, d[2:2+n]):
    c += seen[k - x]; seen[x] += 1
print(c)
""", ["5 6\n1 5 3 3 2\n"],
    lambda r: (lambda n: f"{n} {r.randint(0, 10)}\n{arr(r, n, 0, 8)}\n")(r.randint(1, 25)),
    big=lambda r: f"200000 100\n{arr(r, 200000, 0, 100)}\n")

problem("longest-unique", "Longest Substring Without Repeats", "Medium", "Sliding Window", """
Find the length of the longest substring with all distinct characters.

**Input:** one line of lowercase letters (1 to 2*10^5 characters).
**Output:** the length.
""", """
s = input().strip(); last = {}; start = best = 0
for i, c in enumerate(s):
    if last.get(c, -1) >= start: start = last[c] + 1
    last[c] = i; best = max(best, i - start + 1)
print(best)
""", ["abcabcbb\n", "bbbb\n"],
    lambda r: word(r, 1, 40, "abcdefg") + "\n",
    big=lambda r: word(r, 200000, 200000) + "\n")

problem("rotate-array", "Rotate Array", "Easy", "Arrays", """
Rotate an array to the right by K steps.

**Input:** N and K (1 <= N <= 10^5, 0 <= K <= 10^9), then N integers.
**Output:** the rotated array on one line.
""", """
import sys
d = sys.stdin.read().split(); n, k = int(d[0]), int(d[1]); a = d[2:2+n]; k %= n
print(" ".join(a[n-k:] + a[:n-k]))
""", ["5 2\n1 2 3 4 5\n"],
    lambda r: (lambda n: f"{n} {r.randint(0, 10**9)}\n{arr(r, n, 1, 99)}\n")(r.randint(1, 15)))

problem("prime-count", "Count Primes", "Medium", "Math", """
Count the prime numbers less than or equal to N.

**Input:** one integer N (1 <= N <= 5*10^6).
**Output:** the count.
""", """
n = int(input())
if n < 2: print(0)
else:
    s = bytearray([1]) * (n + 1); s[0] = s[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if s[i]: s[i*i::i] = bytearray(len(range(i*i, n+1, i)))
    print(sum(s))
""", ["10\n", "1\n"],
    lambda r: f"{r.randint(1, 10**r.randint(1, 5))}\n",
    big=lambda r: "5000000\n")

problem("power-mod", "Modular Power", "Medium", "Math", """
Compute a^b mod m for each query.

**Input:** T (1 <= T <= 10^4), then T lines with a, b, m (0 <= a, b <= 10^18, 1 <= m <= 10^9).
**Output:** one result per line.
""", """
import sys
d = sys.stdin.read().split(); t = int(d[0])
print("\\n".join(str(pow(int(d[1+3*i]), int(d[2+3*i]), int(d[3+3*i]))) for i in range(t)))
""", ["2\n2 10 1000\n3 0 7\n"],
    lambda r: (lambda t: f"{t}\n" + "".join(f"{r.randint(0, 10**18)} {r.randint(0, 10**18)} {r.randint(1, 10**9)}\n" for _ in range(t)))(r.randint(1, 8)))

problem("climb-stairs", "Climbing Stairs", "Easy", "Dynamic Programming", """
You can climb 1 or 2 steps at a time. In how many ways can you reach step N? Print the answer mod 10^9+7.

**Input:** one integer N (1 <= N <= 10^6).
**Output:** the number of ways mod 1000000007.
""", """
n = int(input()); a, b = 1, 1
for _ in range(n): a, b = b, (a + b) % 1000000007
print(a)
""", ["3\n", "10\n"],
    lambda r: f"{r.randint(1, 10**r.randint(1, 5))}\n",
    big=lambda r: "1000000\n")

problem("coin-change-ways", "Coin Change Ways", "Medium", "Dynamic Programming", """
Count the ways to make amount S using unlimited coins of the given denominations (order does not matter),
mod 10^9+7.

**Input:** N and S (1 <= N <= 100, 0 <= S <= 10^4), then N distinct coin values (1..10^4).
**Output:** the number of ways mod 1000000007.
""", """
import sys
d = sys.stdin.read().split(); n, s = int(d[0]), int(d[1]); w = [1] + [0] * s
for c in map(int, d[2:2+n]):
    for v in range(c, s + 1): w[v] = (w[v] + w[v-c]) % 1000000007
print(w[s])
""", ["3 5\n1 2 5\n", "1 3\n2\n"],
    lambda r: (lambda n: f"{n} {r.randint(0, 300)}\n{' '.join(map(str, r.sample(range(1, 60), n)))}\n")(r.randint(1, 6)))

problem("lis-length", "Longest Increasing Subsequence", "Hard", "Dynamic Programming", """
Find the length of the longest strictly increasing subsequence.

**Input:** N (1 <= N <= 2*10^5), then N integers.
**Output:** the LIS length.
""", """
import sys, bisect
d = sys.stdin.read().split(); n = int(d[0]); t = []
for x in map(int, d[1:1+n]):
    i = bisect.bisect_left(t, x)
    if i == len(t): t.append(x)
    else: t[i] = x
print(len(t))
""", ["8\n10 9 2 5 3 7 101 18\n"],
    lambda r: (lambda n: f"{n}\n{arr(r, n, 1, 30)}\n")(r.randint(1, 25)),
    big=lambda r: f"200000\n{arr(r, 200000, 1, 10**9)}\n")

problem("merge-intervals", "Merge Intervals", "Medium", "Sorting", """
Merge all overlapping intervals (intervals that touch, like [1,3] and [3,5], also merge) and print how many
intervals remain and their total covered length.

**Input:** N (1 <= N <= 10^5), then N lines with l r (0 <= l <= r <= 10^9).
**Output:** two integers: the number of merged intervals and the total length (sum of r - l).
""", """
import sys
d = sys.stdin.read().split(); n = int(d[0])
iv = sorted((int(d[1+2*i]), int(d[2+2*i])) for i in range(n)); m = []
for l, r in iv:
    if m and l <= m[-1][1]: m[-1][1] = max(m[-1][1], r)
    else: m.append([l, r])
print(len(m), sum(r - l for l, r in m))
""", ["4\n1 3\n2 6\n8 10\n15 18\n"],
    lambda r: (lambda n: f"{n}\n" + "".join((lambda l: f"{l} {l + r.randint(0, 6)}\n")(r.randint(0, 30)) for _ in range(n)))(r.randint(1, 10)))

problem("kth-smallest", "K-th Smallest", "Medium", "Sorting", """
Print the K-th smallest element of the array (1-indexed, counting duplicates).

**Input:** N and K (1 <= K <= N <= 2*10^5), then N integers.
**Output:** the K-th smallest value.
""", """
import sys
d = sys.stdin.read().split(); n, k = int(d[0]), int(d[1])
print(sorted(map(int, d[2:2+n]))[k-1])
""", ["6 2\n7 10 4 3 20 15\n"],
    lambda r: (lambda n: f"{n} {r.randint(1, n)}\n{arr(r, n, -50, 50)}\n")(r.randint(1, 20)))

problem("stock-profit", "Best Time to Trade", "Easy", "Greedy", """
Given daily prices, choose one day to buy and a later day to sell to maximise profit. Print the best profit
(0 if no profit is possible).

**Input:** N (1 <= N <= 2*10^5), then N prices (1..10^9).
**Output:** the maximum profit.
""", """
import sys
d = sys.stdin.read().split(); n = int(d[0]); lo = 10**18; best = 0
for p in map(int, d[1:1+n]):
    lo = min(lo, p); best = max(best, p - lo)
print(best)
""", ["6\n7 1 5 3 6 4\n", "3\n5 4 3\n"],
    lambda r: (lambda n: f"{n}\n{arr(r, n, 1, 100)}\n")(r.randint(1, 20)),
    big=lambda r: f"200000\n{arr(r, 200000, 1, 10**9)}\n")

problem("majority-element", "Majority Element", "Easy", "Arrays", """
Print the value that appears more than N/2 times, or -1 if no such value exists.

**Input:** N (1 <= N <= 2*10^5), then N integers.
**Output:** the majority value or -1.
""", """
import sys
from collections import Counter
d = sys.stdin.read().split(); n = int(d[0])
v, c = Counter(d[1:1+n]).most_common(1)[0]
print(v if c * 2 > n else -1)
""", ["5\n3 3 4 2 3\n", "4\n1 2 1 2\n"],
    lambda r: (lambda n: f"{n}\n{arr(r, n, 1, 3)}\n")(r.randint(1, 15)))

problem("range-sum-queries", "Range Sum Queries", "Medium", "Prefix Sums", """
Answer Q queries: the sum of a[l..r] (1-indexed, inclusive).

**Input:** N and Q (1 <= N, Q <= 2*10^5), then N integers (|a_i| <= 10^9), then Q lines with l r.
**Output:** one sum per line.
""", """
import sys
d = sys.stdin.buffer.read().split(); n, q = int(d[0]), int(d[1]); p = [0]
for x in d[2:2+n]: p.append(p[-1] + int(x))
o = 2 + n
print("\\n".join(str(p[int(d[o+2*i+1])] - p[int(d[o+2*i])-1]) for i in range(q)))
""", ["5 3\n1 2 3 4 5\n1 3\n2 5\n4 4\n"],
    lambda r: (lambda n, q: f"{n} {q}\n{arr(r, n, -100, 100)}\n" + "".join((lambda a, b: f"{min(a,b)} {max(a,b)}\n")(r.randint(1, n), r.randint(1, n)) for _ in range(q)))(r.randint(1, 15), r.randint(1, 10)),
    big=lambda r: "200000 200000\n" + arr(r, 200000, -10**9, 10**9) + "\n" + "".join((lambda a, b: f"{min(a,b)} {max(a,b)}\n")(r.randint(1, 200000), r.randint(1, 200000)) for _ in range(200000)))

problem("grid-paths", "Grid Paths With Walls", "Medium", "Dynamic Programming", """
Count paths from the top-left to the bottom-right of an R x C grid moving only right or down, never entering
a wall '#'. Print the count mod 10^9+7.

**Input:** R and C (1 <= R, C <= 1000), then R lines of C characters ('.' or '#').
**Output:** the number of paths mod 1000000007.
""", """
import sys
d = sys.stdin.read().split(); r, c = int(d[0]), int(d[1]); g = d[2:2+r]; M = 1000000007
row = [0] * c
for i in range(r):
    for j in range(c):
        if g[i][j] == '#': row[j] = 0
        elif i == 0 and j == 0: row[j] = 1
        else: row[j] = (row[j] + (row[j-1] if j else 0)) % M
print(row[-1])
""", ["3 3\n...\n.#.\n...\n", "2 2\n.#\n#.\n"],
    lambda r: (lambda R, C: f"{R} {C}\n" + "".join("".join("#" if r.random() < 0.15 and (i, j) not in ((0, 0), (R-1, C-1)) else "." for j in range(C)) + "\n" for i in range(R)))(r.randint(1, 8), r.randint(1, 8)))

problem("word-frequency", "Most Frequent Word", "Easy", "Hashing", """
Print the most frequent word and its count. On a tie, print the lexicographically smallest word.

**Input:** N (1 <= N <= 10^5), then N lowercase words.
**Output:** the word and its count separated by a space.
""", """
import sys
from collections import Counter
d = sys.stdin.read().split(); c = Counter(d[1:1+int(d[0])])
w = min(c, key=lambda k: (-c[k], k)); print(w, c[w])
""", ["7\napple bat apple cat bat dog bat\n"],
    lambda r: (lambda n: f"{n}\n" + " ".join(r.choice(["ant", "bee", "cat", "dog", "eel"]) for _ in range(n)) + "\n")(r.randint(1, 20)))

problem("binary-search-count", "Count in Range", "Medium", "Binary Search", """
Given a sorted array, answer Q queries: how many elements lie in [x, y]?

**Input:** N and Q (1 <= N, Q <= 2*10^5), then N sorted integers, then Q lines with x y (x <= y).
**Output:** one count per line.
""", """
import sys, bisect
d = sys.stdin.buffer.read().split(); n, q = int(d[0]), int(d[1]); a = list(map(int, d[2:2+n])); o = 2 + n
print("\\n".join(str(bisect.bisect_right(a, int(d[o+2*i+1])) - bisect.bisect_left(a, int(d[o+2*i]))) for i in range(q)))
""", ["6 3\n1 3 3 5 8 9\n3 5\n0 1\n6 7\n"],
    lambda r: (lambda n, q: f"{n} {q}\n{' '.join(map(str, sorted(r.randint(0, 30) for _ in range(n))))}\n" + "".join((lambda a, b: f"{min(a,b)} {max(a,b)}\n")(r.randint(0, 30), r.randint(0, 30)) for _ in range(q)))(r.randint(1, 15), r.randint(1, 8)),
    big=lambda r: "200000 200000\n" + " ".join(map(str, sorted(r.randint(0, 10**9) for _ in range(200000)))) + "\n" + "".join((lambda a, b: f"{min(a,b)} {max(a,b)}\n")(r.randint(0, 10**9), r.randint(0, 10**9)) for _ in range(200000)))

problem("island-count", "Count Islands", "Hard", "Graphs", """
Count the islands in a grid: groups of '1' cells connected up, down, left or right.

**Input:** R and C (1 <= R, C <= 1000), then R lines of C characters ('0' or '1').
**Output:** the number of islands.
""", """
import sys
d = sys.stdin.read().split(); R, C = int(d[0]), int(d[1]); g = [bytearray(x, 'ascii') for x in d[2:2+R]]; n = 0
for i in range(R):
    for j in range(C):
        if g[i][j] == 49:
            n += 1; st = [(i, j)]; g[i][j] = 48
            while st:
                a, b = st.pop()
                for x, y in ((a+1, b), (a-1, b), (a, b+1), (a, b-1)):
                    if 0 <= x < R and 0 <= y < C and g[x][y] == 49:
                        g[x][y] = 48; st.append((x, y))
print(n)
""", ["4 5\n11000\n11000\n00100\n00011\n"],
    lambda r: (lambda R, C: f"{R} {C}\n" + "".join("".join(r.choice("0001") for _ in range(C)) + "\n" for _ in range(R)))(r.randint(1, 10), r.randint(1, 10)))

problem("shortest-path-grid", "Shortest Path in a Maze", "Hard", "Graphs", """
Find the minimum number of moves from 'S' to 'E' in a maze moving up, down, left or right through '.' cells
(walls are '#'). Print -1 if E is unreachable.

**Input:** R and C (1 <= R, C <= 1000), then R lines of C characters containing exactly one S and one E.
**Output:** the minimum number of moves or -1.
""", """
import sys
from collections import deque
d = sys.stdin.read().split(); R, C = int(d[0]), int(d[1]); g = d[2:2+R]
s = next((i, j) for i in range(R) for j in range(C) if g[i][j] == 'S')
dist = {s: 0}; q = deque([s]); ans = -1
while q:
    a, b = q.popleft()
    if g[a][b] == 'E': ans = dist[(a, b)]; break
    for x, y in ((a+1, b), (a-1, b), (a, b+1), (a, b-1)):
        if 0 <= x < R and 0 <= y < C and g[x][y] != '#' and (x, y) not in dist:
            dist[(x, y)] = dist[(a, b)] + 1; q.append((x, y))
print(ans)
""", ["3 4\nS..#\n.#..\n...E\n", "2 2\nS#\n#E\n"],
    lambda r: (lambda R, C: (lambda cells: f"{R} {C}\n" + "".join("".join(cells[i*C:(i+1)*C]) + "\n" for i in range(R)))((lambda c: (c.__setitem__(0, 'S'), c.__setitem__(R*C-1, 'E'), c)[2])([r.choice("...#") for _ in range(R*C)])))(r.randint(1, 8), r.randint(2, 8)))

problem("topo-order", "Course Order", "Hard", "Graphs", """
There are N tasks numbered 1..N and M prerequisite pairs "a b" meaning a must come before b. Print YES if all
tasks can be completed (the dependency graph has no cycle), otherwise NO.

**Input:** N and M (1 <= N <= 10^5, 0 <= M <= 2*10^5), then M lines with a b.
**Output:** YES or NO.
""", """
import sys
from collections import deque
d = sys.stdin.read().split(); n, m = int(d[0]), int(d[1]); adj = [[] for _ in range(n+1)]; indeg = [0]*(n+1)
for i in range(m):
    a, b = int(d[2+2*i]), int(d[3+2*i]); adj[a].append(b); indeg[b] += 1
q = deque(i for i in range(1, n+1) if indeg[i] == 0); seen = 0
while q:
    u = q.popleft(); seen += 1
    for v in adj[u]:
        indeg[v] -= 1
        if indeg[v] == 0: q.append(v)
print("YES" if seen == n else "NO")
""", ["3 2\n1 2\n2 3\n", "3 3\n1 2\n2 3\n3 1\n"],
    lambda r: (lambda n: (lambda m: f"{n} {m}\n" + "".join((lambda a, b: f"{a} {b}\n")(*((lambda x, y: (min(x, y), max(x, y)) if r.random() < 0.9 else (max(x, y), min(x, y)))(*r.sample(range(1, n+1), 2)))) for _ in range(m)))(r.randint(0, n)))(r.randint(2, 10)))


def run_ref(src, inp):
    buf = io.StringIO()
    old_in = sys.stdin
    sys.stdin = io.TextIOWrapper(io.BytesIO(inp.encode()), encoding="utf-8")
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(src, "<ref>", "exec"), {"__name__": "__main__", "input": lambda *a: sys.stdin.readline().rstrip("\n")})
    finally:
        sys.stdin = old_in
    return buf.getvalue()


def main():
    rng = random.Random(SEED)
    out = []
    for i, p in enumerate(P, 1):
        hidden_inputs = [p["gen"](rng) for _ in range(p["hidden"])]
        if p["big"]:
            hidden_inputs.append(p["big"](rng))
        tests = lambda ins: [{"input": x, "output": run_ref(p["ref"], x)} for x in ins]
        out.append({
            "id": i, "slug": p["slug"], "title": p["title"], "difficulty": p["difficulty"], "topic": p["topic"],
            "statement": p["statement"], "reference_python": p["ref"],
            "samples": tests(p["samples"]), "hidden": tests(hidden_inputs),
        })
        print(f"{i:2d} {p['slug']:22s} samples={len(p['samples'])} hidden={len(hidden_inputs)}")
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote {len(out)} problems -> {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
