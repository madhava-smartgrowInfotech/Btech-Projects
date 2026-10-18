"""
IEEE-style reference list. Every entry is either (a) a file in the batch folder (base paper, supporting papers), (b) a standard,
well-known publication, or (c) a title/year/venue triple recorded in the batch literature survey (authors were not recorded there and are not guessed).
"""

REFS = [
    # 1 base paper
    "S. E. Eyimaya and N. Altin, \"Design of multi-agent-based energy management system for DC microgrids,\" IEEE Access, vol. 14, pp. 39120-39133, 2026, doi: 10.1109/ACCESS.2026.3672618.",
    # 2
    "Y. Zhang, A. M. Saber, A. Youssef, and D. Kundur, \"Grid-Agent: An LLM-powered multi-agent system for power grid control,\" arXiv:2508.05702, Aug. 2025.",
    # 3
    "J. Picault and C. Goubet, \"Orchestrating power grid studies with multi-agent AI and MCP servers,\" arXiv:2607.14158, Jul. 2026.",
    # 4
    "\"Multi-agent deep reinforcement learning for energy-efficient smart grid management,\" in Proc. 1st Int. Conf. Intelligent Methods and Advanced Computer Scientific Innovations, 2025. (Authors not recorded in the batch survey.)",
    # 5
    "\"Energy system fault reconstruction control strategy based on multi-agent deep reinforcement learning,\" in Proc. 6th Int. Conf. Energy, Power and Grid (ICEPG), 2024. (Authors not recorded in the batch survey.)",
    # 6
    "\"Distributed optimal scheduling for electric vehicles considering the multi-agent demands of electric vehicles, charging stations and power grid,\" in Proc. 3rd Int. Conf. Power, Grid and Energy Storage, 2025. (Authors not recorded in the batch survey.)",
    # 7
    "\"Multi-agent systems in power system: A comprehensive review of energy management in power grid,\" in Smart Grid Security and Protection, Lecture Notes in Electrical Engineering, 2025. (Authors not recorded in the batch survey.)",
    # 8
    "S. D. J. McArthur et al., \"Multi-agent systems for power engineering applications - Part I: Concepts, approaches, and technical challenges,\" IEEE Trans. Power Syst., vol. 22, no. 4, pp. 1743-1752, Nov. 2007, doi: 10.1109/TPWRS.2007.908471.",
    # 9
    "R. H. Lasseter, \"MicroGrids,\" in Proc. IEEE Power Eng. Soc. Winter Meeting, vol. 1, 2002, pp. 305-308, doi: 10.1109/PESW.2002.985003.",
    # 10
    "H. Farhangi, \"The path of the smart grid,\" IEEE Power Energy Mag., vol. 8, no. 1, pp. 18-28, Jan./Feb. 2010, doi: 10.1109/MPE.2009.934876.",
    # 11
    "L. Thurner et al., \"pandapower - An open-source Python tool for convenient modeling, analysis, and optimization of electric power systems,\" IEEE Trans. Power Syst., vol. 33, no. 6, pp. 6510-6521, Nov. 2018, doi: 10.1109/TPWRS.2018.2829021.",
    # 12
    "M. Alshiekh, R. Bloem, R. Ehlers, B. Konighofer, S. Niekum, and U. Topcu, \"Safe reinforcement learning via shielding,\" in Proc. AAAI Conf. Artif. Intell., 2018, pp. 2669-2678.",
    # 13
    "G. Dalal, K. Dvijotham, M. Vecerik, T. Hester, C. Paduraru, and Y. Tassa, \"Safe exploration in continuous action spaces,\" arXiv:1801.08757, 2018.",
    # 14
    "J. Garcia and F. Fernandez, \"A comprehensive survey on safe reinforcement learning,\" J. Mach. Learn. Res., vol. 16, pp. 1437-1480, 2015.",
    # 15
    "D. Amodei, C. Olah, J. Steinhardt, P. Christiano, J. Schulman, and D. Mane, \"Concrete problems in AI safety,\" arXiv:1606.06565, 2016.",
    # 16
    "S. Yao et al., \"ReAct: Synergizing reasoning and acting in language models,\" in Proc. Int. Conf. Learn. Represent. (ICLR), 2023.",
    # 17
    "M. Turpin, J. Michael, E. Perez, and S. R. Bowman, \"Language models don't always say what they think: Unfaithful explanations in chain-of-thought prompting,\" in Proc. Adv. Neural Inf. Process. Syst. (NeurIPS), 2023.",
    # 18
    "M. Wooldridge, An Introduction to MultiAgent Systems, 2nd ed. Chichester, U.K.: Wiley, 2009.",
    # 19
    "Voltage Characteristics of Electricity Supplied by Public Electricity Networks, European Standard EN 50160:2010, CENELEC, 2010.",
    # 20
    "Secure Hash Standard (SHS), Federal Information Processing Standards Publication FIPS 180-4, NIST, Aug. 2015.",
]

# references cited in the IEEE paper (those with a recorded author list), renumbered 1..N in the paper
PAPER_REFS = [1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]


def n(i):
    """Report reference number for a REFS index (1-based): returns '[i]'."""
    return f"[{i}]"
