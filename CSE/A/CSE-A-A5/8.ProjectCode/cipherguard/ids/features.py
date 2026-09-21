"""
ThreatSense Engine - Feature schema and preprocessing.

UNSW-NB15 has ~49 features; we support a core 42-feature subset plus label/attack_cat.
Synthetic demo data uses the same schema so retraining with real CSVs is drop-in.

Key categorical features: proto, service, state
Numeric features: everything else except id, label, attack_cat

Preprocessing: one-hot or ordinal for categoricals (we use OrdinalEncoder + OneHot for stability),
MinMax scaling for numeric, stratified splits, class balancing via scale_pos_weight / class_weight.
"""

FEATURE_NAMES = [
    "dur", "proto", "service", "state", "spkts", "dpkts", "sbytes", "dbytes",
    "rate", "sttl", "dttl", "sload", "dload", "sloss", "dloss", "sinpkt", "dinpkt",
    "sjit", "djit", "swin", "stcpb", "dtcpb", "dwin", "tcprtt", "synack", "ackdat",
    "smean", "dmean", "trans_depth", "response_body_len",
    "ct_srv_src", "ct_state_ttl", "ct_dst_ltm", "ct_src_dport_ltm", "ct_dst_sport_ltm", "ct_dst_src_ltm",
    "is_ftp_login", "ct_ftp_cmd", "ct_flw_http_mthd", "ct_src_ltm", "ct_srv_dst", "is_sm_ips_ports"
]

CATEGORICAL_FEATURES = ["proto", "service", "state"]
LABEL_COL = "label"  # 0 normal, 1 attack
ATTACK_COL = "attack_cat"

PROTO_VALUES = ["tcp", "udp", "icmp", "arp", "ospf", "igmp"]
SERVICE_VALUES = ["-", "http", "ftp", "smtp", "ssh", "dns", "ftp-data", "pop3", "dhcp", "ssl", "snmp", "radius", "irc"]
STATE_VALUES = ["FIN", "INT", "CON", "REQ", "RST", "ECO", "ACC", "CLO", "PAR", "URN", "no", "-"]

# Full expected column order for CSV import
ALL_COLUMNS = ["id"] + FEATURE_NAMES + [LABEL_COL, ATTACK_COL]
