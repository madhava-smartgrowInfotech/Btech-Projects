# Verhoeff algorithm for Aadhaar checksum (12 digits)
# Tables from standard Verhoeff

d_table = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],
    [3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],
    [5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],
    [7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],
    [9,8,7,6,5,4,3,2,1,0],
]

p_table = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],
    [8,9,1,6,0,4,3,7,2,5],
    [9,4,5,3,1,2,6,8,7,0],
    [4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],
    [7,0,4,6,9,1,3,2,5,8],
]

inv_table = [0,4,3,2,1,5,6,7,8,9]

def validate_verhoeff(num: str) -> bool:
    if not num.isdigit():
        return False
    c = 0
    # iterate reversed
    for i, ch in enumerate(reversed(num)):
        c = d_table[c][p_table[(i % 8)][int(ch)]]
    return c == 0

def generate_verhoeff(num_without_check: str) -> str:
    # compute check digit
    c = 0
    for i, ch in enumerate(reversed(num_without_check)):
        c = d_table[c][p_table[((i+1) % 8)][int(ch)]]
    check = inv_table[c]
    return num_without_check + str(check)

def generate_valid_aadhaar() -> str:
    import secrets
    # generate 11 random digits first, ensure not starting with 0/1 per Aadhaar spec? Keep simple: first digit 2-9
    first = str(secrets.randbelow(8)+2)  # 2-9
    rest = "".join(str(secrets.randbelow(10)) for _ in range(10))
    base11 = first + rest
    return generate_verhoeff(base11)
