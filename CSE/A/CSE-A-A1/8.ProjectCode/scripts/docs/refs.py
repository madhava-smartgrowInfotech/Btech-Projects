"""
Reference list (IEEE style) for the Adaptive Learning Intelligence Platform documents. The index in this list is the number used in the
text, [n]; the numbering is fixed because the chapter documents, decks and the paper all cite it.

[1] is the base paper. [2] and [3] are the two supporting papers kept in archived_base_papers/ (both read in full). [4]-[18] are standard
works on retrieval, RAG, compression and tooling; entries 10-15 and 23-30 were checked against the reference list printed in the base
paper [1]. [19]-[22] are the four batch-survey items of 5.LITERATURE SURVEY.docx, looked up on the web; [22] could not be verified
beyond the title, year and venue given in the batch file and is never quoted for results.
"""

REFS = [
    # 1
    "D. Zhang, H. Yu, J. Huo and M. Su, \"SAC-RAG: Semantic Adaptive Context Compression for Retrieval-Augmented Generation,\" "
    "IEEE Access, vol. 14, pp. 117406-117418, 2026, doi: 10.1109/ACCESS.2026.3718025.",
    # 2
    "Z. Li, V. Yazdanpanah, J. Wang, W. Gu, L. Shi, A. I. Cristea, S. Kiden and S. Stein, \"TutorLLM: Customizing learning recommendations with "
    "knowledge tracing and retrieval-augmented generation,\" in Proc. 18th ACM Conf. Recommender Syst. (RecSys 2024), Bari, Italy, Oct. 2024; "
    "arXiv:2502.15709.",
    # 3
    "R. Vatankhah Barenji, N. Salimi and S. Khoshgoftar, \"An LLM-powered assessment retrieval-augmented generation (RAG) for higher education,\" "
    "arXiv:2601.06141, Jan. 2026.",
    # 4
    "P. Lewis et al., \"Retrieval-augmented generation for knowledge-intensive NLP tasks,\" in Advances in Neural Information Processing "
    "Systems, vol. 33, 2020, pp. 9459-9474.",
    # 5
    "V. Karpukhin, B. Oguz, S. Min, P. Lewis, L. Wu, S. Edunov, D. Chen and W.-T. Yih, \"Dense passage retrieval for open-domain question "
    "answering,\" in Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP), 2020, pp. 6769-6781.",
    # 6
    "S. Robertson and H. Zaragoza, \"The probabilistic relevance framework: BM25 and beyond,\" Found. Trends Inf. Retr., vol. 3, no. 4, "
    "pp. 333-389, 2009.",
    # 7
    "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Inf. Process. Manage., vol. 24, no. 5, "
    "pp. 513-523, 1988.",
    # 8
    "S. Deerwester, S. T. Dumais, G. W. Furnas, T. K. Landauer and R. Harshman, \"Indexing by latent semantic analysis,\" J. Amer. Soc. Inf. "
    "Sci., vol. 41, no. 6, pp. 391-407, 1990.",
    # 9
    "S. Xiao, Z. Liu, P. Zhang and N. Muennighoff, \"C-Pack: Packaged resources to advance general Chinese embedding,\" arXiv:2309.07597, 2023 "
    "(BGE embedding models, including BAAI/bge-small-en-v1.5).",
    # 10
    "H. Jiang, Q. Wu, C.-Y. Lin, Y. Yang and L. Qiu, \"LLMLingua: Compressing prompts for accelerated inference of large language models,\" "
    "in Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP), 2023, pp. 13358-13376.",
    # 11
    "S. Jeong, J. Baek, S. Cho, S. J. Hwang and J. Park, \"Adaptive-RAG: Learning to adapt retrieval-augmented large language models through "
    "question complexity,\" in Proc. Conf. North Amer. Chapter Assoc. Comput. Linguistics: Hum. Lang. Technol. (NAACL-HLT), 2024, pp. 7036-7050.",
    # 12
    "N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni and P. Liang, \"Lost in the middle: How language models use long "
    "contexts,\" Trans. Assoc. Comput. Linguistics, vol. 12, pp. 157-173, Feb. 2024.",
    # 13
    "Z. Yang, P. Qi, S. Zhang, Y. Bengio, W. Cohen, R. Salakhutdinov and C. D. Manning, \"HotpotQA: A dataset for diverse, explainable "
    "multi-hop question answering,\" in Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP), 2018, pp. 2369-2380.",
    # 14
    "A. Asai, Z. Wu, Y. Wang, A. Sil and H. Hajishirzi, \"Self-RAG: Learning to retrieve, generate, and critique through self-reflection,\" "
    "in Proc. 12th Int. Conf. Learn. Represent. (ICLR), 2024.",
    # 15
    "F. Xu, W. Shi and E. Choi, \"RECOMP: Improving retrieval-augmented LMs with compression and selective augmentation,\" in Proc. 12th "
    "Int. Conf. Learn. Represent. (ICLR), 2024.",
    # 16
    "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, Oct. 2011.",
    # 17
    "A. T. Corbett and J. R. Anderson, \"Knowledge tracing: Modeling the acquisition of procedural knowledge,\" User Model. User-Adapt. "
    "Interact., vol. 4, no. 4, pp. 253-278, 1994.",
    # 18
    "Wikimedia Foundation, \"English Wikipedia,\" https://en.wikipedia.org (text licensed CC BY-SA 4.0; the 36 articles and revision "
    "identifiers used for the evaluation corpus are listed in experiments/corpus_manifest.json).",
    # 19
    "J. Kaczmarek, J. Pokrywka, K. Biedalak, G. Kurzyp and L. Grzybowski, \"Optimizing retrieval-augmented generation of medical content for "
    "spaced repetition learning,\" in Proc. 17th Int. Conf. Comput. Supported Educ. (CSEDU), 2025, pp. 174-186, doi: 10.5220/0013477700003932; "
    "arXiv:2503.01859.",
    # 20
    "R. Gokhman, J. Li and Y. Zhang, \"Automatic teaching platform on vision language retrieval augmented generation,\" presented at the 2025 "
    "IEEE Integrated STEM Education Conf. (ISEC), Princeton, NJ, USA, Mar. 2025; arXiv:2503.05464.",
    # 21
    "D. S. Eleuterio, P. F. Oliveira and P. Matos, \"Democratizing financial education: An API-driven platform powered by retrieval-augmented "
    "generation,\" in Proc. 2025 17th Int. Conf. Educ. Technol. Comput. (ICETC), 2025, pp. 108-112, doi: 10.1109/ICETC66579.2025.11387160.",
    # 22
    "\"Student-designed educational resources for Lean: exploring ChatGPT and Retrieval-Augmented Generation,\" ZDM - Mathematics Education, "
    "2026 (title, year and venue as listed in the batch literature survey; authors and pagination not verified).",
    # 23
    "Z. Jiang, F. F. Xu, L. Gao, Z. Sun, Q. Liu, J. Dwivedi-Yu, Y. Yang, J. Callan and G. Neubig, \"Active retrieval augmented generation,\" "
    "in Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP), 2023, pp. 7969-7992.",
    # 24
    "W. Shi, S. Min, M. Yasunaga, M. Seo, R. James, M. Lewis, L. Zettlemoyer and W.-T. Yih, \"REPLUG: Retrieval-augmented black-box language "
    "models,\" Trans. Assoc. Comput. Linguistics, vol. 12, pp. 1-19, Jun. 2024.",
    # 25
    "H. Jiang, Q. Wu, X. Luo, D. Li, C.-Y. Lin, Y. Yang and L. Qiu, \"LongLLMLingua: Accelerating and enhancing LLMs in long context scenarios "
    "via prompt compression,\" in Proc. 62nd Annu. Meeting Assoc. Comput. Linguistics (ACL), 2024, pp. 1658-1677.",
    # 26
    "Z. Pan et al., \"LLMLingua-2: Data distillation for efficient and faithful task-agnostic prompt compression,\" in Findings Assoc. Comput. "
    "Linguistics: ACL 2024, pp. 963-981.",
    # 27
    "Y. Gao et al., \"Retrieval-augmented generation for large language models: A survey,\" arXiv:2312.10997, 2023 (revised 2024).",
    # 28
    "X. Ho, A.-K. Duong Nguyen, S. Sugawara and A. Aizawa, \"Constructing a multi-hop QA dataset for comprehensive evaluation of reasoning "
    "steps,\" in Proc. 28th Int. Conf. Comput. Linguistics (COLING), 2020, pp. 6609-6625.",
    # 29
    "H. Trivedi, N. Balasubramanian, T. Khot and A. Sabharwal, \"MuSiQue: Multihop questions via single-hop question composition,\" Trans. "
    "Assoc. Comput. Linguistics, vol. 10, pp. 539-554, May 2022.",
    # 30
    "G. Izacard et al., \"Atlas: Few-shot learning with retrieval augmented language models,\" J. Mach. Learn. Res., vol. 24, no. 251, "
    "pp. 1-43, 2023.",
]

# Batch-survey items whose details could not be verified; listed in the reference list with a note, never quoted for results.
UNVERIFIED = [22]
