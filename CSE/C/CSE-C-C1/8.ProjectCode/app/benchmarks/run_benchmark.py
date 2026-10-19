import time
import json
import statistics
import asyncio
import pathlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models.models import User, VoterProfile, Election, Candidate, VoterEligibility, BenchmarkRun
from app.security.auth import hash_password
from app.security.crypto import hash_aadhaar, mask_aadhaar
from app.identity.verhoeff import generate_valid_aadhaar
from app.services.voting_service import issue_authorization, cast_vote
from app.ledger.ledger import init_validators, create_genesis_block

DEFAULT_VOTERS = 1000
BATCH_SIZES = [10,20,30]

def ensure_election_for_benchmark(db: Session):
    e = db.query(Election).filter(Election.title=="Benchmark Election").first()
    if e:
        return e
    now = datetime.utcnow()
    e = Election(title="Benchmark Election", description="Synthetic benchmark election", start_time=now - timedelta(days=1), end_time=now + timedelta(days=1), status="OPEN", created_by=1)
    db.add(e)
    db.commit()
    db.refresh(e)
    # candidates
    for name in ["Benchmark Alpha", "Benchmark Beta", "Benchmark Gamma"]:
        c = Candidate(election_id=e.id, name=name, party="Benchmark Party", description="Benchmark candidate", manifesto="Benchmark manifesto", is_active=True)
        db.add(c)
    db.commit()
    return e

def generate_synthetic_voters(db: Session, count: int):
    start = db.query(User).filter(User.role=="VOTER").count()
    created = []
    for i in range(count):
        uname = f"bench_voter_{start+i+1}_{int(time.time())%100000}"
        # ensure unique
        while db.query(User).filter(User.username==uname).first():
            uname = uname+"_x"
        pwd = "Bench@123"
        u = User(username=uname, password_hash=hash_password(pwd), role="VOTER", display_name=f"Bench Voter {i+1}", email=f"{uname}@bench.local")
        db.add(u)
        db.flush()
        aadhaar = generate_valid_aadhaar()
        vp = VoterProfile(user_id=u.id, full_name=f"Bench Voter {i+1}", aadhaar_hash=hash_aadhaar(aadhaar), aadhaar_masked=mask_aadhaar(aadhaar))
        db.add(vp)
        created.append(u)
    db.commit()
    return created

def measure_latency(func, iterations):
    latencies = []
    successes = 0
    fails = 0
    start_all = time.perf_counter()
    for _ in range(iterations):
        s = time.perf_counter()
        try:
            func()
            successes+=1
        except Exception:
            fails+=1
        e = time.perf_counter()
        latencies.append((e-s)*1000)
    total = time.perf_counter() - start_all
    return {
        "total_ops": iterations,
        "successes": successes,
        "fails": fails,
        "total_duration": total,
        "mean_ms": statistics.mean(latencies) if latencies else 0,
        "median_ms": statistics.median(latencies) if latencies else 0,
        "p95_ms": sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0,
        "min_ms": min(latencies) if latencies else 0,
        "max_ms": max(latencies) if latencies else 0,
        "stdev_ms": statistics.stdev(latencies) if len(latencies)>1 else 0,
        "throughput_ops_per_sec": iterations/total if total>0 else 0,
        "latencies": latencies
    }

def sync_vote_operation(election_id, voter_user_id, candidate_id):
    db = SessionLocal()
    try:
        tok = issue_authorization(db, election_id, voter_user_id)
        cast_vote(db, election_id, voter_user_id, tok, candidate_id)
    finally:
        db.close()

def run_benchmark(voters_count=1000):
    init_db()
    db = SessionLocal()
    try:
        init_validators(db)
        create_genesis_block(db)
        # ensure at least voters_count synthetic voters
        existing = db.query(User).filter(User.role=="VOTER").count()
        need = max(0, voters_count - existing)
        if need>0:
            print(f"Generating {need} synthetic voters...")
            t0 = time.perf_counter()
            generate_synthetic_voters(db, need)
            print(f"Generated in {time.perf_counter()-t0:.2f}s")

        election = ensure_election_for_benchmark(db)
        # ensure eligibility for all bench voters
        all_voters = db.query(User).filter(User.role=="VOTER").all()
        # pick only bench voters or all? Use first voters_count voters not already voted in this election
        candidates = db.query(Candidate).filter(Candidate.election_id==election.id).all()
        # eligibility
        for v in all_voters:
            exists = db.query(VoterEligibility).filter(VoterEligibility.election_id==election.id, VoterEligibility.voter_user_id==v.id).first()
            if not exists:
                db.add(VoterEligibility(election_id=election.id, voter_user_id=v.id, is_eligible=True))
        db.commit()
        # reset participation for benchmark election (clear previous benchmark votes if any)
        # We won't clear, but choose voters not yet participated
        from app.models.models import VoterParticipation, Ballot, LedgerTransaction, LedgerBlock
        participated_ids = {p.voter_user_id for p in db.query(VoterParticipation).filter(VoterParticipation.election_id==election.id).all()}
        available = [v for v in all_voters if v.id not in participated_ids][:voters_count]
        if len(available) < voters_count:
            # generate more
            more = generate_synthetic_voters(db, voters_count - len(available))
            for v in more:
                db.add(VoterEligibility(election_id=election.id, voter_user_id=v.id, is_eligible=True))
            db.commit()
            available += more
            available = available[:voters_count]

        print(f"Benchmarking with {len(available)} voters, candidates {[c.id for c in candidates]}")
        # sync benchmark
        print("Running synchronous benchmark...")
        sync_latencies = []
        sync_success = 0
        sync_fail = 0
        sync_start = time.perf_counter()
        for idx, voter in enumerate(available):
            cand = candidates[idx % len(candidates)].id
            s = time.perf_counter()
            db2 = SessionLocal()
            try:
                tok = issue_authorization(db2, election.id, voter.id)
                cast_vote(db2, election.id, voter.id, tok, cand)
                sync_success+=1
            except Exception as e:
                sync_fail+=1
            finally:
                db2.close()
            e = time.perf_counter()
            sync_latencies.append((e-s)*1000)
        sync_duration = time.perf_counter() - sync_start

        # For async/batched we simulate batch sizes: create new election per batch size? Instead we measure batched submission using separate election
        # Create separate elections for batched tests to avoid duplicate vote
        async_results = {}
        for batch in BATCH_SIZES:
            # create new election for this batch size
            db3 = SessionLocal()
            now = datetime.utcnow()
            be = Election(title=f"Benchmark Async {batch}", description="async batch", start_time=now - timedelta(days=1), end_time=now+timedelta(days=1), status="OPEN", created_by=1)
            db3.add(be)
            db3.commit()
            db3.refresh(be)
            for name in ["Alpha","Beta","Gamma"]:
                db3.add(Candidate(election_id=be.id, name=f"{name} {batch}", party="Bench", description="desc", manifesto="mani"))
            db3.commit()
            be_cands = db3.query(Candidate).filter(Candidate.election_id==be.id).all()
            be_cand_ids = [c.id for c in be_cands]
            be_id = be.id
            # new voters for this batch
            bench_voters = generate_synthetic_voters(db3, voters_count)
            for v in bench_voters:
                db3.add(VoterEligibility(election_id=be_id, voter_user_id=v.id, is_eligible=True))
            db3.commit()
            bench_ids = [v.id for v in bench_voters]
            db3.close()

            # measure batched: submit in batches
            latencies = []
            succ = 0
            fail = 0
            total_start = time.perf_counter()
            # We'll simulate async by processing batches sequentially but measuring batch throughput
            for i in range(0, len(bench_ids), batch):
                batch_ids = bench_ids[i:i+batch]
                batch_start = time.perf_counter()
                for idx, vid in enumerate(batch_ids):
                    cand = be_cand_ids[idx % len(be_cand_ids)]
                    dbt = SessionLocal()
                    try:
                        tok = issue_authorization(dbt, be_id, vid)
                        cast_vote(dbt, be_id, vid, tok, cand)
                        succ+=1
                    except Exception:
                        fail+=1
                    finally:
                        dbt.close()
                batch_end = time.perf_counter()
                # per-vote latency approx batch duration / batch size
                avg = (batch_end - batch_start)/len(batch_ids)*1000 if batch_ids else 0
                for _ in batch_ids:
                    latencies.append(avg)
            total_dur = time.perf_counter() - total_start
            async_results[batch] = {
                "batch_size": batch,
                "total_ops": voters_count,
                "successes": succ,
                "fails": fail,
                "total_duration": total_dur,
                "throughput": voters_count/total_dur if total_dur else 0,
                "mean_ms": statistics.mean(latencies) if latencies else 0,
                "median_ms": statistics.median(latencies) if latencies else 0,
                "p95_ms": sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0,
                "min_ms": min(latencies) if latencies else 0,
                "max_ms": max(latencies) if latencies else 0,
                "stdev_ms": statistics.stdev(latencies) if len(latencies)>1 else 0,
            }

        # aggregate sync stats
        sync_mean = statistics.mean(sync_latencies) if sync_latencies else 0
        sync_median = statistics.median(sync_latencies) if sync_latencies else 0
        sync_p95 = sorted(sync_latencies)[int(len(sync_latencies)*0.95)] if sync_latencies else 0

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "voters_count": voters_count,
            "sync": {
                "total_duration": sync_duration,
                "throughput": len(available)/sync_duration if sync_duration else 0,
                "mean_ms": sync_mean,
                "median_ms": sync_median,
                "p95_ms": sync_p95,
                "min_ms": min(sync_latencies) if sync_latencies else 0,
                "max_ms": max(sync_latencies) if sync_latencies else 0,
                "stdev_ms": statistics.stdev(sync_latencies) if len(sync_latencies)>1 else 0,
                "successes": sync_success,
                "fails": sync_fail,
            },
            "async_batches": async_results
        }

        # save to file and DB
        pathlib.Path("benchmark_results").mkdir(exist_ok=True)
        out_path = pathlib.Path(f"benchmark_results/benchmark_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        out_path.write_text(json.dumps(result, indent=2))
        pathlib.Path("benchmark_results/latest.json").write_text(json.dumps(result, indent=2))

        # also save to DB
        db4 = SessionLocal()
        br = BenchmarkRun(
            total_ops=voters_count,
            sync_duration=sync_duration,
            async_duration=async_results[20]["total_duration"] if 20 in async_results else 0,
            throughput_sync=len(available)/sync_duration if sync_duration else 0,
            throughput_async=async_results[20]["throughput"] if 20 in async_results else 0,
            mean_latency_ms=sync_mean,
            p95_latency_ms=sync_p95,
            details_json=json.dumps(result)
        )
        db4.add(br)
        db4.commit()
        db4.close()

        print(json.dumps(result, indent=2))
        print(f"Saved to {out_path}")
        return result
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--voters", type=int, default=DEFAULT_VOTERS)
    args = parser.parse_args()
    run_benchmark(args.voters)
