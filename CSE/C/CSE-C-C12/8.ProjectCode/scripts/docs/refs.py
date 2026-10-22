"""
Reference list for the SymptoTrackAI (CSE-C-C12) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Verification (see REF_NOTES): [1] and the related works [7]-[13], [36] were checked against the base-paper PDF; [5] against the
Healthcare Informatics Research article page; [6] against the archived ClinicBot PDF; [14]-[35] are standard, widely cited papers and
standards whose bibliographic data are well established. [2]-[4] come from the batch literature survey with title, year and source only:
no abstract or page data could be found for them, so they are listed with a note and are never cited for a claim.
Italics use *...* markup (rendered by kit.add_runs). Cite from other modules with CITE['key'] (the number).
"""

_ITEMS = [
    ("base", "U. S. Madhury and M. Ramesh, \"A hybrid retrieval-augmented generation framework for intelligent symptom monitoring and disease guidance,\" "
             "*Int. J. Eng. Res. Sci. Technol.*, vol. 22, no. 3, pp. 702-707, 2026, doi: 10.62643/ijerst.2026.v22.n3.4170."),
    ("survey2", "\"A retrieval-augmented generation framework for medical question answering: design, implementation, and evaluation of an AI-driven healthcare chatbot,\" "
                "*Iconic Research and Engineering Journals*, 2026. [Listed in the batch literature survey; authors, volume and pages could not be verified.]"),
    ("survey3", "\"A book-verified retrieval-augmented medical chatbot for reliable and explainable healthcare assistance,\" in *Proc. 7th Int. Conf. Intelligent "
                "Communication Technologies and Virtual Mobile Networks (ICICV)*, 2026. [Listed in the batch literature survey; authors and pages could not be verified.]"),
    ("survey4", "\"Healthcare chatbot: AI-powered medical information assistant using retrieval-augmented generation,\" *Int. J. Pharmacy with Medical Sciences*, 2026. "
                "[Listed in the batch literature survey; authors, volume and pages could not be verified.]"),
    ("emr", "N. Son, I. Kang, I. Kim, K. Lee, S. Nam and D. Lee, \"Development and evaluation of a retrieval-augmented generation-based electronic medical record chatbot system,\" "
            "*Healthc. Inform. Res.*, vol. 31, no. 3, pp. 218-225, Jul. 2025, doi: 10.4258/hir.2025.31.3.218."),
    ("clinicbot", "N. Nananukul and M. Kejriwal, \"ClinicBot: a guideline-grounded clinical chatbot with prioritized evidence RAG and verifiable citations,\" "
                  "system demonstration, CAIS 2026, arXiv:2605.00846, 2026."),
    ("divya", "S. Divya, V. Indumathi, S. Ishwarya, M. Priyasankari and S. K. Devi, \"A self-diagnosis medical chatbot using artificial intelligence,\" "
              "*J. Web Develop. Web Designing*, vol. 3, no. 1, pp. 1-7, 2018."),
    ("kumar", "S. S. Kumar, S. T. Ahmed, A. S. Fathima, M. Nishabai and S. Sophia, \"Medical chatbot assistance for primary clinical guidance using machine learning techniques,\" "
              "*Procedia Comput. Sci.*, vol. 233, pp. 279-287, 2024."),
    ("hsu", "I.-C. Hsu and J.-D. Yu, \"A medical chatbot using machine learning and natural language understanding,\" *Multimedia Tools Appl.*, vol. 81, no. 17, "
            "pp. 23777-23799, Jul. 2022."),
    ("babu", "A. Babu and S. B. Boddu, \"BERT-based medical chatbot: enhancing healthcare communication through natural language understanding,\" "
             "*Explor. Res. Clin. Social Pharmacy*, vol. 13, Art. no. 100419, Mar. 2024."),
    ("peri", "S. D. Bhavani Peri, S. Santhanalakshmi and R. Radha, \"Chatbot to chat with medical books using retrieval-augmented generation model,\" in *Proc. IEEE North Karnataka "
             "Subsection Flagship Int. Conf. (NKCon)*, Bagalkote, India, Sep. 2024, pp. 1-5, doi: 10.1109/NKCON62728.2024.10774900."),
    ("prescience", "Prathwini and Prathyakshini, \"PreScienceMED: leveraging text classification for precise disease prediction,\" in *Proc. IEEE Int. Conf. Distributed Computing, "
                   "VLSI, Electrical Circuits and Robotics (DISCOVER)*, Mangalore, India, Oct. 2024, pp. 90-95, doi: 10.1109/DISCOVER62353.2024.10750775."),
    ("natarajan", "Y. Natarajan, K. R. S. Preethaa, S. Pandian, S. U. Geetha and S. Senthilkumar, \"Enhancing medical information retrieval with a language model,\" in *Proc. Int. Conf. "
                  "Cognitive Robotics and Intelligent Systems (ICC-ROBINS)*, Coimbatore, India, Apr. 2024, pp. 437-441, doi: 10.1109/ICCROBINS60238.2024.10533903."),
    ("alqaidi", "S. H. Alqaidi, S. M. Albugami, W. S. Alzahrani, S. Badri and A. Wali, \"Network-integrated medical chatbot for enhanced healthcare services,\" "
                "*Telematics Informat. Rep.*, vol. 15, Art. no. 100153, Sep. 2024."),
    ("rag", "P. Lewis *et al.*, \"Retrieval-augmented generation for knowledge-intensive NLP tasks,\" in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 9459-9474."),
    ("dpr", "V. Karpukhin *et al.*, \"Dense passage retrieval for open-domain question answering,\" in *Proc. Conf. Empirical Methods Natural Language Process. (EMNLP)*, 2020, pp. 6769-6781."),
    ("faiss", "J. Johnson, M. Douze and H. Jegou, \"Billion-scale similarity search with GPUs,\" *IEEE Trans. Big Data*, vol. 7, no. 3, pp. 535-547, Jul. 2021."),
    ("sbert", "N. Reimers and I. Gurevych, \"Sentence-BERT: sentence embeddings using Siamese BERT-networks,\" in *Proc. EMNLP-IJCNLP*, 2019, pp. 3982-3992."),
    ("bm25", "S. Robertson and H. Zaragoza, \"The probabilistic relevance framework: BM25 and beyond,\" *Found. Trends Inf. Retr.*, vol. 3, no. 4, pp. 333-389, 2009."),
    ("hyde", "L. Gao, X. Ma, J. Lin and J. Callan, \"Precise zero-shot dense retrieval without relevance labels,\" in *Proc. 61st Annu. Meeting Assoc. Comput. Linguistics (ACL)*, 2023, pp. 1762-1777."),
    ("monobert", "R. Nogueira and K. Cho, \"Passage re-ranking with BERT,\" arXiv:1901.04085, 2019."),
    ("msmarco", "P. Bajaj *et al.*, \"MS MARCO: a human generated machine reading comprehension dataset,\" arXiv:1611.09268, 2016."),
    ("flan", "H. W. Chung *et al.*, \"Scaling instruction-finetuned language models,\" *J. Mach. Learn. Res.*, vol. 25, no. 70, pp. 1-53, 2024."),
    ("minilm", "W. Wang, F. Wei, L. Dong, H. Bao, N. Yang and M. Zhou, \"MiniLM: deep self-attention distillation for task-agnostic compression of pre-trained transformers,\" "
               "in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 5776-5788."),
    ("rrf", "G. V. Cormack, C. L. A. Clarke and S. Buettcher, \"Reciprocal rank fusion outperforms Condorcet and individual rank learning methods,\" in *Proc. 32nd Int. ACM SIGIR Conf. "
            "Research and Development in Information Retrieval*, 2009, pp. 758-759."),
    ("medrag", "G. Xiong, Q. Jin, Z. Lu and A. Zhang, \"Benchmarking retrieval-augmented generation for medicine,\" in *Findings Assoc. Comput. Linguistics: ACL 2024*, 2024, pp. 6233-6251."),
    ("halluc", "Z. Ji *et al.*, \"Survey of hallucination in natural language generation,\" *ACM Comput. Surveys*, vol. 55, no. 12, Art. no. 248, 2023."),
    ("medpalm", "K. Singhal *et al.*, \"Large language models encode clinical knowledge,\" *Nature*, vol. 620, no. 7972, pp. 172-180, 2023."),
    ("hf", "T. Wolf *et al.*, \"Transformers: state-of-the-art natural language processing,\" in *Proc. EMNLP: System Demonstrations*, 2020, pp. 38-45."),
    ("sklearn", "F. Pedregosa *et al.*, \"Scikit-learn: machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, pp. 2825-2830, 2011."),
    ("irbook", "C. D. Manning, P. Raghavan and H. Schutze, *Introduction to Information Retrieval*. Cambridge, U.K.: Cambridge Univ. Press, 2008."),
    ("bcrypt", "N. Provos and D. Mazieres, \"A future-adaptable password scheme,\" in *Proc. USENIX Annu. Tech. Conf., FREENIX Track*, 1999, pp. 81-91."),
    ("jwt", "M. Jones, J. Bradley and N. Sakimura, \"JSON Web Token (JWT),\" IETF RFC 7519, May 2015."),
    ("wilson", "E. B. Wilson, \"Probable inference, the law of succession, and statistical inference,\" *J. Amer. Statist. Assoc.*, vol. 22, no. 158, pp. 209-212, 1927."),
    ("fastapi", "S. Ramirez, \"FastAPI,\" software, 2018. [Online]. Available: https://fastapi.tiangolo.com"),
]

REFS = [t for _, t in _ITEMS]
CITE = {k: i + 1 for i, (k, _) in enumerate(_ITEMS)}

REF_NOTES = {
    "base": "Checked against the base-paper PDF (BASEPAPER_A_Hybrid_Retrieval_Augmented_Generation_Framework_for_Inte.pdf), pp. 702-707. The author name 'Ullaganti Shreeyaa Madhury' is written 'U. S. Madhury'.",
    "survey2-4": "Listed in 5.LITERATURE SURVEY.docx (title, year, source). Web searches did not locate them; they appear in the list with a not-verified note and are not cited for any claim.",
    "emr": "Verified on the Healthcare Informatics Research article page (synapse.koreamed.org): 5,931 question-document pairs, BGE-M3 retrieval accuracy 97.6%, Multilingual-E5-Large 89.7%, query latency under 10 ms.",
    "clinicbot": "Read in archived_base_papers/ (arXiv 2605.00846): structured guideline extraction, evidence prioritisation, citations, ADA Standards of Care 2025; a system demonstration with no accuracy table.",
    "divya-natarajan": "Bibliographic data copied from the base paper's reference list and related-work section; the base paper reports only that they 'effectively supported' users - no numbers.",
    "canonical": "Standard papers (RAG, DPR, FAISS, SBERT, BM25, HyDE, monoBERT, MS MARCO, Flan, MiniLM, RRF, MedRAG, hallucination survey, Med-PaLM) whose bibliographic data are well established; nothing is quoted from them except their method.",
}
