"""F4: clause graph (NetworkX) - flags combinations that are harmless alone but
dangerous together."""
import networkx as nx

# Each combo: set of rule ids that, together across the contract, are flagged
# as a risky combination, with a human-readable reason.
RISKY_COMBOS = [
    {
        "id": "termination_norefund_penalty",
        "rule_ids": {"unilateral_termination", "no_refund", "penalty_clause"},
        "reason": "The other party can end the contract at will, keep your payments, and still "
                   "charge a penalty - each clause alone is common, but together they let one side "
                   "walk away with your money and more.",
    },
    {
        "id": "restraint_unlimited_liability",
        "rule_ids": {"restraint_of_trade", "unlimited_liability"},
        "reason": "You are barred from working elsewhere while also carrying unlimited liability - "
                   "this combination concentrates both income risk and financial risk on you alone.",
    },
    {
        "id": "autorenew_unilateral_termination",
        "rule_ids": {"auto_renewal", "unilateral_termination"},
        "reason": "The contract renews automatically, but only the other party can terminate freely - "
                   "you can be locked into successive terms with no matching exit right.",
    },
]


def build_clause_graph(clauses: list[dict]) -> nx.Graph:
    """clauses: list of {id, clause_type, flags: [rule_id, ...]}"""
    graph = nx.Graph()
    for c in clauses:
        graph.add_node(c["id"], clause_type=c["clause_type"], flags=c["flags"], text_preview=c.get("text_preview", ""))
    return graph


def detect_risky_combinations(clauses: list[dict]) -> list[dict]:
    """clauses: list of {id, flags: [rule_id, ...]}. Returns list of
    {combo_id, reason, clause_ids: [...]} for each combo whose rule_ids are all
    present somewhere in the contract (possibly on different clauses)."""
    rule_to_clauses: dict[str, list[int]] = {}
    for c in clauses:
        for rule_id in c["flags"]:
            rule_to_clauses.setdefault(rule_id, []).append(c["id"])

    present_rules = set(rule_to_clauses.keys())
    hits = []
    for combo in RISKY_COMBOS:
        if combo["rule_ids"].issubset(present_rules):
            clause_ids = sorted({cid for rid in combo["rule_ids"] for cid in rule_to_clauses[rid]})
            hits.append({
                "combo_id": combo["id"],
                "reason": combo["reason"],
                "rule_ids": sorted(combo["rule_ids"]),
                "clause_ids": clause_ids,
            })
    return hits


def graph_to_json(clauses: list[dict], combos: list[dict]) -> dict:
    graph = build_clause_graph(clauses)
    nodes = [
        {
            "id": n,
            "clause_type": data["clause_type"],
            "flags": data["flags"],
            "text_preview": data["text_preview"],
            "risky": len(data["flags"]) > 0,
        }
        for n, data in graph.nodes(data=True)
    ]
    edges = []
    for combo in combos:
        ids = combo["clause_ids"]
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                edges.append({"source": ids[i], "target": ids[j], "combo_id": combo["combo_id"], "reason": combo["reason"]})
    return {"nodes": nodes, "edges": edges, "risky_combinations": combos}
