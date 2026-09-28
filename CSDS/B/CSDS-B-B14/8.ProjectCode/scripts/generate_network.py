"""Generate the city distribution network (seeded) -> data/network/city.inp + layout.json."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services import twin  # noqa: E402


def main():
    wn, zones = twin.build_network(seed=7)
    twin.save_network(wn, zones)
    wn2 = twin.copy_network()
    res = twin.run(wn2)
    s = twin.summarize_eps(wn2, res)
    print(f"Network: {wn.num_junctions} junctions, {wn.num_pipes} pipes, {wn.num_pumps} pump, {wn.num_tanks} tank")
    print(f"NRW {s['nrw_pct']}%  avg pressure {s['avg_pressure']} m  min {s['min_pressure']} m  equity {s['equity_score']}")
    for z, v in s["zones"].items():
        print(z, v)
    print("tank levels", s["tank_level"])


if __name__ == "__main__":
    main()
