from app.ml.faithfulness import ClaimInput, score_claims

CLAUSES = {
    1: "Expenses related to the treatment of the listed conditions, including cataract, shall be excluded until the "
       "expiry of 24 months of continuous coverage after the date of inception of the first policy.",
    2: "Road ambulance expenses are payable up to Rs. 750 per hospitalization.",
}


def test_supported_claim_scores_high():
    result = score_claims([ClaimInput("Cataract treatment is excluded until 24 months of continuous coverage.", [1])],
                          CLAUSES)
    assert result["score"] >= 70
    assert result["claims"][0]["numbers_ok"] is True


def test_wrong_number_and_unsupported_claims_score_low():
    wrong = score_claims([ClaimInput("Cataract treatment is covered after 12 months.", [1])], CLAUSES)
    assert wrong["claims"][0]["numbers_ok"] is False
    assert wrong["score"] < 50
    uncited = score_claims([ClaimInput("Maternity is covered from day one.", [])], CLAUSES)
    assert uncited["score"] == 0
    assert uncited["label"] == "weakly_supported"


def test_no_claims_is_not_scored():
    assert score_claims([], CLAUSES)["score"] is None
