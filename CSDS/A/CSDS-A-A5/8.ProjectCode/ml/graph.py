"""Buyer-seller network analysis with NetworkX: trade graph, circular-trading cycles,
shared-identity clusters (possible shell networks) and trade communities."""
from collections import defaultdict

import networkx as nx
import numpy as np


def build_trade_graph(ds):
    G = nx.DiGraph()
    G.add_nodes_from(range(len(ds["taxpayers"])))
    for r in ds["invoices"]:
        s, b = r["_s"], r["_b"]
        if not G.has_edge(s, b):
            G.add_edge(s, b, value=0.0, tax=0.0, count=0, months=set(), unmatched=0.0, invoices=[])
        e = G[s][b]
        e["value"] += r["taxable_value"]
        e["tax"] += r["tax_amount"]
        e["count"] += 1
        e["months"].add(r["_m"])
        e["invoices"].append(r["id"])
        if not r["seller_reported"]:
            e["unmatched"] += r["taxable_value"]
    return G


def detect_cycles(G, purchases_total, max_len=5, cap=20000, min_score=0.25):
    """Find short trade cycles and score how much they look like circular trading.

    balance        - circulated values stay similar around the loop (min/max edge value)
    recurrence     - the whole loop trades in the same months, month after month
    concentration  - the loop is a large part of every member's purchases (not incidental)
    """
    values = np.array([d["value"] for _, _, d in G.edges(data=True)])
    thr = float(np.percentile(values, 50)) if len(values) else 0
    H = nx.DiGraph()
    H.add_edges_from((u, v) for u, v, d in G.edges(data=True) if len(d["months"]) >= 2 and d["value"] >= thr)
    cycles = []
    for k, cyc in enumerate(nx.simple_cycles(H, length_bound=max_len)):
        if k >= cap:
            break
        edges = [(cyc[i], cyc[(i + 1) % len(cyc)]) for i in range(len(cyc))]
        vals = [G[u][v]["value"] for u, v in edges]
        common = set.intersection(*[G[u][v]["months"] for u, v in edges])
        balance = min(vals) / max(vals)
        recurrence = min(1.0, len(common) / 3)
        conc = float(min(G[u][v]["value"] / max(purchases_total[v], 1) for u, v in edges))
        score = balance ** 0.5 * recurrence * min(1.0, conc) ** 0.5
        cycles.append(dict(nodes=list(cyc), edges=edges, value=float(sum(vals)), balance=round(balance, 3),
                           common_months=sorted(common), concentration=round(conc, 3), score=round(score, 3)))
    suspicious = [c for c in cycles if c["score"] >= min_score]
    # merge overlapping suspicious cycles into rings
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    for c in suspicious:
        for v in c["nodes"][1:]:
            parent[find(v)] = find(c["nodes"][0])
    groups = defaultdict(list)
    for c in suspicious:
        groups[find(c["nodes"][0])].append(c)
    rings = []
    for cs in sorted(groups.values(), key=lambda cs: -max(c["score"] for c in cs)):
        nodes = sorted({v for c in cs for v in c["nodes"]})
        edges = sorted({e for c in cs for e in c["edges"]})
        best = max(cs, key=lambda c: c["score"])
        rings.append(dict(id=f"R{len(rings) + 1:02d}", nodes=nodes, edges=edges, score=best["score"],
                          best_cycle=best["nodes"], balance=best["balance"], common_months=best["common_months"],
                          value=float(sum(G[u][v]["value"] for u, v in edges)),
                          tax=float(sum(G[u][v]["tax"] for u, v in edges)), n_cycles=len(cs)))
    return dict(n_cycles_scanned=len(cycles), truncated=len(cycles) >= cap, rings=rings)


def identity_clusters(taxpayers):
    """Registrations linked by a shared address or contact number."""
    g = nx.Graph()
    g.add_nodes_from(range(len(taxpayers)))
    by_attr = defaultdict(list)
    for i, t in enumerate(taxpayers):
        by_attr[("address", t["address_id"])].append(i)
        by_attr[("contact", t["contact_id"])].append(i)
    for (kind, _), members in by_attr.items():
        for a, b in zip(members, members[1:]):
            g.add_edge(a, b)
    out = []
    for comp in nx.connected_components(g):
        if len(comp) < 2:
            continue
        comp = sorted(comp)
        out.append(dict(nodes=comp, shared_address=len({taxpayers[i]["address_id"] for i in comp}) < len(comp),
                        shared_contact=len({taxpayers[i]["contact_id"] for i in comp}) < len(comp)))
    return out


def communities(G, seed=42):
    U = nx.Graph()
    U.add_nodes_from(G.nodes)
    for u, v, d in G.edges(data=True):
        w = U[u][v]["weight"] + d["value"] if U.has_edge(u, v) else d["value"]
        U.add_edge(u, v, weight=w)
    comm = nx.community.louvain_communities(U, weight="weight", seed=seed)
    label = {}
    for k, c in enumerate(sorted(comm, key=len, reverse=True)):
        for v in c:
            label[v] = k
    return label
