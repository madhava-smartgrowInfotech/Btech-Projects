"""Chapter 2: Literature survey."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .lit import LIT_TABLE


def blocks():
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),

        H2("2.1 Overview"),
        P("This chapter reviews the work on which the Smart Campus Placement System builds and against which it has to be judged. It begins with the two papers that "
          "shape the project: the paper named as the batch base paper, a placement-prediction web application published in IJETMS in 2026 [1], and the arXiv paper "
          "on hybrid XGBoost-plus-kNN prediction with a recommendation module [2], whose technique the code actually implements. Both are analysed in detail. "
          "Related work is then grouped by theme: classical classifiers for placement and employability, ensemble methods, placement platforms and matching, and educational "
          "data mining in general. The chapter then describes the datasets and algorithms that the present project uses, summarises strengths and limitations, lists the "
          "sources named in the batch literature survey that could not be verified, and ends with the research gap that this project addresses."),
        P("A note on method. A number is quoted from a paper only when we read it in the paper itself or in its abstract on the publisher's page. Where only a title and a venue "
          "are known, no result is stated. The declared base paper [1] reports no accuracy, F1 or AUC at all, and this chapter says so rather than filling the gap."),

        H2("2.2 Analysis of the Declared Base Paper"),
        P("The batch documents name as base paper \"Student placement prediction system using machine learning\" by Prasanna Kumari, Punith, Srinath, Koushik and Gourav of "
          "Vidya Jyothi Institute of Technology, Hyderabad, published in the International Journal of Engineering Technology and Management Sciences, volume 10, issue 3 "
          "(May-June 2026), pages 47-51 [1]. It is a five-page application paper in plain language rather than a research study with measurements."),
        H3("What the paper does"),
        B("It builds a web application that predicts a student's placement chances from academic scores, technical skills, communication ability, internships, projects and "
          "extracurricular activities.",
          "Because real records are hard to obtain, it generates a synthetic dataset of student records to stand in for real scenarios. The size of the dataset is not stated.",
          "Pre-processing handles missing values, encodes categorical variables and scales numeric ones; feature engineering is mentioned without detail.",
          "Logistic Regression, Random Forest and Gradient Boosting are trained on an 80:20 train-test split and compared on accuracy, precision, recall and ROC-AUC (the design "
          "section adds F1); the best model is tuned further and deployed.",
          "The application is built with Streamlit and offers individual prediction, batch prediction from an uploaded CSV file, interactive charts, skill-gap analysis, "
          "model-performance views, an automatically generated PDF report and e-mail delivery of that report through SMTP."),
        P("The design section divides the system into five layers - data, processing, model, application and output - and the objectives list seven goals, among them predicting "
          "placement from several factors rather than one, helping students see strengths and weaknesses, supporting batch prediction and helping colleges understand placement trends [1]."),
        H3("What the paper does not report"),
        P("The results section of the paper states the 80:20 split and names the three algorithms and four metrics, and then ends; it contains no table, no figure and no figure of merit. "
          "No accuracy, precision, recall, F1 or AUC value is given, the winning model is not named, the number of students in the synthetic dataset is not given, and the generating "
          "process is not described. The introductory literature section says that earlier studies reached \"around 90% or more\" accuracy with careful preprocessing and tuning, "
          "but cites no specific study for that figure. The conclusion lists real-time data and more advanced models as future work [1]."),
        P("For this project that has two consequences. First, there is no numeric baseline to compare against: any comparison with [1] can be a comparison of scope and design, "
          "not of accuracy. Second, the paper's own method shares a weakness with ours that deserves stating early - the data are synthetic. Whatever accuracy a model reaches on "
          "synthetic records measures how well it recovers the rule that generated them, not how well it would predict real placements."),

        H2("2.3 Analysis of the Technique Paper"),
        P("The code of this project is built on a second paper, recorded in the batch folder as the technique source: \"A hybrid machine learning approach for graduate admission "
          "prediction and combined university-program recommendation\" by Heidari Fard and Tabrizi, arXiv:2603.29881, February 2026 [2]. It solves a problem of the same shape - "
          "predict an outcome for an applicant and a target, then recommend better targets to those predicted to fail - in the domain of graduate admissions. Mapping admissions to "
          "placement is direct: the applicant becomes the student, the university becomes the company, the program becomes the role."),
        H3("Data and set-up"),
        P("The authors scraped about 34,000 self-reported records from GradCafe, kept those from 2021 onwards, removed outcomes other than accepted or rejected, and arrived at about 13,000 "
          "applicants with 15 features, enriched with QS ranking indicators; 51% were accepted and 49% rejected. Categorical variables were frequency-encoded, numeric ones standardised, "
          "and an interaction feature between program and QS rank was added after a decision-tree analysis. The data were split 70/15/15 (9,100/1,950/1,950) with a fixed seed, and "
          "XGBoost hyper-parameters were tuned with 9-fold cross-validation [2]."),
        H3("Hybrid residual refinement"),
        P("Single models plateaued at 0.68-0.73 accuracy on this data: the test accuracy of logistic regression and the decision tree was 0.6944, random forest 0.7344, SVM 0.6954, "
          "kNN 0.6774 and XGBoost 0.7241. The authors observed that misclassified applicants sit near the decision boundary and proposed a residual set R, the applicants for whom "
          "XGBoost is wrong or only weakly confident (predicted probability between 0.4 and 0.6), for which a local kNN model (k = 9) replaces the XGBoost decision. The hybrid reached "
          "0.8723 accuracy (an SVM-based variant 0.8749), and Platt-scaled probabilities gave a Brier score of 0.1864 [2]."),
        H3("Recommendation module"),
        P("For applicants predicted to be rejected, the paper recommends alternative universities, alternative programs and the combination of both. Candidates must pass feasibility filters - "
          "a maximum GPA difference that depends on the QS rank, an affordability rule and a country preference - and are ranked by predicted acceptance probability with a GPA "
          "proximity bonus. On 6,028 rejected applicants about 93% were matched, and the hybrid university-program strategy raised the mean predicted acceptance probability by "
          "0.704 (university-only 0.687, program-only 0.142); the abstract summarises the gain as 70% [2]. SHAP ranks the degree type, GPA and program discipline as the main drivers."),
        H3("A point the paper leaves open"),
        P("The residual set is defined with the true labels (Equation 1 of the paper selects applicants whose prediction is wrong). The reported 0.8723 therefore uses information that "
          "is not available when a new applicant arrives. The authors do not report a variant that selects residuals by the confidence band alone. This project measures exactly that "
          "difference on its own data (Chapter 8); here it is enough to note that the paper's headline figure should be read with that caveat."),
        H3("How the technique paper maps onto placement"),
        P("The project keeps the structure of [2] and replaces its domain objects. The table lists each element of the paper and what stands in for it here; the choices follow the "
          "project README and the code in `src/`."),
        TAB("From admissions [2] to placement (this project)", ["Technique paper [2]", "This project"], [
            ["University / program", "Company / role"],
            ["QS rank (university quality)", "Company tier (1 dream, 2 core, 3 mass recruiter)"],
            ["Applicant GPA and its distance to the university's level", "CGPA and its gap to the company's CGPA cut-off; aptitude and technical gaps"],
            ["Program admission rate", "Company hiring rate"],
            ["Program x QS rank interaction", "CGPA x tier interaction"],
            ["Maximum allowed GPA difference by QS rank (0.10-0.25)", "Maximum allowed CGPA difference by tier (0.6 / 1.0 / 1.5)"],
            ["Country and budget filters", "Location preference and minimum package"],
            ["Platt scaling, Brier score, SHAP, PCA, 70/15/15 split, 9-fold CV", "The same, on 3,000 synthetic students"],
            ["University-only, program-only and hybrid recommendation", "Company-only, role-only and hybrid company-role recommendation"],
        ], widths=[3.1, 3.2], align=["l", "l"], size=10),

        H2("2.4 Related Work"),
        H3("2.4.1 Classical classifiers for placement and employability"),
        P("Most published placement work compares standard classifiers on a small table of student attributes. Thangavel, Bkaratki and Sankar describe a placement analyser that uses "
          "decision-tree classifiers on historical student data and, instead of a yes-no answer, predicts one of five statuses: Dream Company, Core Company, Mass Recruiter, Not Eligible or "
          "Not Interested [21]. The three-way company grouping is the same idea that the present project encodes as company tiers. Khandale and Bhoite compare logistic regression, SVM, kNN, decision trees, "
          "random forests and the ensemble techniques bagging, boosting and voting; their abstract reports about 78% accuracy for XGBoost and AdaBoost [22]."),
        P("Baffa, Miyim and Dauda study employability prediction from 218 Computer Science graduates of one Nigerian university between 2016 and 2021, using CGPA, a work-experience "
          "scheme score, union group and gender; a random forest is reported to reach 98% accuracy and an F1 of 0.99 against logistic regression and a decision tree [15]. The very high "
          "figure on 218 records from one department illustrates a recurring problem: small single-site datasets give optimistic and non-transferable results."),
        H3("2.4.2 Ensemble methods"),
        P("A second group reports higher accuracy through ensembles. Ambili and Abraham apply a stacking ensemble to 20 student attributes and report 90.21% accuracy [16]. Gupta et al. "
          "present ML-CPC, an exploratory analysis followed by supervised classifiers and an ensemble, with accuracy 0.9524, precision 0.8667, recall 1.0 and F1 0.9286 on their recruitment data [17]. "
          "Pathak et al. train a voting classifier on a public Kaggle placement dataset with hyper-parameter search and cross-validation and report, on an unseen test set, accuracy 0.8923, "
          "precision 0.9430, recall 0.8567, F1 0.8978 and AUC 0.9433 in under a second of training time [18]. Kumar et al. compare logistic regression, random forest and XGBoost on "
          "academic scores, projects, internships, certificates and aptitude results, find that XGBoost performs best, and serve the model through a React and MongoDB application [19]. "
          "These results are not comparable with one another or with ours: the datasets differ in size, source and label rule, and none of the papers reports a calibration measure."),
        H3("2.4.3 Placement platforms and matching"),
        P("Beyond prediction, Sanjana et al. propose a broader placement ecosystem in which an SVM predicts placement (87.4% accuracy on an 80:20 split of data whose size is not given) and "
          "a Deep Q-Network optimises scheduling and job matching, with reported gains of 28% fewer scheduling conflicts and up to 21% better matching accuracy [20]. The thrust is the same as "
          "that of this project - to move from a verdict to guidance - but the evidence is thin because the data are not described. Recommendation in general is surveyed by Schafer, "
          "Konstan and Riedl, who classify recommendation applications in electronic commerce by their inputs, technology and degree of personalisation [13]; the filter-then-rank pattern "
          "of the technique paper [2] and of this project is one of the simple, transparent members of that family."),
        H3("2.4.4 Educational data mining"),
        P("The field in which all of the above sit is educational data mining. Romero and Ventura survey the tasks to which data mining has been applied in education, among them predicting student "
          "performance and providing feedback to instructors and students [23]. Placement prediction is a late-stage instance of the same activity: it turns records of past cohorts into "
          "decision support for the next one."),
        H3("2.4.5 Calibration, residual refinement and explanation"),
        P("Two methodological threads matter for this project. Platt scaling fits a sigmoid to a classifier's scores to obtain probabilities [4]; Niculescu-Mizil and Caruana show that boosted trees "
          "and other margin-based learners produce distorted probabilities that calibration improves [9], and the Brier score measures the result [8]. SHAP assigns each feature a contribution "
          "to an individual prediction with game-theoretic guarantees [5]. Both are used by the technique paper [2] and are carried into this project because a recommendation module that ranks "
          "options by probability needs probabilities that can be trusted and a placement officer needs reasons."),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [list(r) for r in LIT_TABLE],
            widths=[1.0, 1.55, 1.15, 1.35, 1.25], align=["l", "l", "l", "l", "l"], size=8),
        P("The numbers in the table are those stated by each paper's abstract or results; they come from different data and are not a league table."),

        H3("2.4.6 Which attributes the literature uses"),
        P("The attribute lists in the surveyed placement papers overlap heavily, which is useful: it shows what a placement predictor is expected to see. The declared base paper [1] "
          "uses academic scores, technical skills, communication ability, internships, projects and extracurricular activities. Kumar et al. add certificates and aptitude test results [19]. "
          "Baffa et al., working with a different kind of institution, use CGPA, a work-experience scheme result, union group and gender [15]. The technique paper [2], in the admissions "
          "setting, relies on the applicant's GPA and on quality indicators of the target (rank, faculty-student ratio, citations, international ratio)."),
        P("One design decision follows from this: the project deliberately does not use gender or similar personal attributes as predictors, because a placement-readiness tool "
          "that scores students on such attributes would be hard to defend. The target's requirements enter the model as gap features, so that the same student receives different probabilities for different companies."),

        H2("2.5 Datasets and Algorithms Used in This Project"),
        H3("Dataset"),
        P(f"The surveyed work uses student attribute tables (academic scores, skills, internships, certifications), admissions records or small institutional samples. Real placement "
          f"records are personal and rarely shared, and the declared base paper [1] itself uses synthetic data. This project does the same and says so: it generates {F.DS['rows']:,} synthetic "
          f"students and a table of {F.DS['companies']} invented companies with CGPA, aptitude and technical cut-offs, package, location and hiring rate, using a fixed random seed. "
          "The student's label is drawn from a logistic score of the gaps to the company's cut-offs, internships, projects, backlogs and a tier penalty, plus noise. The design copies the "
          "structure of the technique paper's data (a student-by-target table with target-quality features) without copying its content."),
        H3("Algorithms"),
        TAB("Algorithms used and why", ["Algorithm", "Role in this project", "Source"], [
            ["Logistic Regression", "Linear baseline; also reveals how linear the synthetic label rule is", "standard"],
            ["Decision Tree, Random Forest", "Threshold-style rules; random forest reduces variance", "[10]"],
            ["SVM with RBF kernel", "Non-linear margin classifier; baseline and local residual model", "[11]"],
            ["kNN (k = 9)", "Baseline and local model that refines borderline cases", "[7]"],
            ["XGBoost (100 trees, depth 8)", "Main global model; handles interactions between gap features", "[3]"],
            ["Platt scaling (sigmoid, 3-fold)", "Turns scores into probabilities used for ranking and the 0.4-0.6 band", "[4], [9]"],
            ["Brier score", "Quality of the probabilities", "[8]"],
            ["SHAP, PCA", "Global explanation of drivers; view of where errors fall", "[5]"],
            ["Filter-then-rank recommendation", "Feasibility filters, proximity bonus, three strategies", "[2], [13]"],
        ], widths=[1.9, 3.3, 1.1], align=["l", "l", "c"], size=10),
        P("Gradient boosting [12] and LightGBM [14] are the other tree-ensemble options mentioned by the technique paper; the code contains a LightGBM branch that is skipped when the "
          "library is not installed, as it was on the machine used for this work."),
        H2("2.6 Strengths and Limitations of the Surveyed Approaches"),
        TAB("Approach families compared", ["Family", "Strengths", "Limitations for this project's goals"], [
            ["Single classifiers [15], [21], [22]", "Simple, fast, interpretable; easy to deploy", "Verdict only; accuracy depends heavily on a small dataset; no probability quality check"],
            ["Ensembles and voting [16]-[19]", "Higher reported accuracy; robust to noise", "Opaque; results not comparable across datasets; no recommendation or explanation"],
            ["Calibrated hybrid with residual refinement [2]", "Reliable probabilities; local correction near the boundary", "Residual set defined with true labels; designed for admissions"],
            ["Placement platforms [1], [19], [20]", "Usable interfaces, reports, matching ideas", "Evidence thin; synthetic or undescribed data; no numeric result in [1]"],
        ], widths=[1.7, 2.2, 2.4], align=["l", "l", "l"], size=10),
        B("Strength common to the field: most placement attributes (CGPA, backlogs, aptitude, internships) are cheap to collect and carry real signal.",
          "Limitation common to the field: small, single-institution or synthetic data, and evaluation on one random split, so that reported accuracies of 78% to 98% cannot be ranked.",
          "Limitation common to the field: accuracy is almost the only measure reported; calibration, per-student explanation and the usefulness of advice are rarely examined."),

        H2("2.7 Sources Named in the Batch Survey That Could Not Be Verified"),
        P("The batch literature survey (5.LITERATURE SURVEY.docx) lists the declared base paper and four further titles with a year and a venue only. Searches by exact title found no "
          "matching record for any of them, so their authors, content and results are unknown to us and nothing is quoted from them. They are listed in the reference list under a clear "
          "\"unverified\" mark and are not cited in the text. Of the alternatives named in the batch folder, EduPredict (ICICAT 2025) was not found, a Springer chapter is recorded there as paywalled and was not "
          "read, and a 2025 Foundry Journal paper was not examined."),
        TAB("Sources recorded in the batch survey", ["Title as recorded", "Year", "Source as recorded", "Status"], [
            ["Excelling through Placement Process", "2025", "Campus to Corporate", "Not found; not cited"],
            ["Campus Placement Prediction And Analysis Using Machine Learning", "2025", "Int. J. of Research Publication and Reviews", "Not found; not cited"],
            ["Student Placement Package Prediction By Regression Analysis", "2024", "Int. J. of Research Publication and Reviews", "Not found; not cited"],
            ["Predictive Analysis of Campus Placement of Student Using Machine Learning Algorithms", "2024", "Journal of IoT and Machine Learning", "Not found; not cited"],
        ], widths=[2.9, 0.5, 1.9, 1.0], align=["l", "c", "l", "l"], size=9.5),
        P("The ten references of the declared base paper were checked only in part. Two of them were located and match their description there: Ambili and Abraham on ensemble-based "
          "employability prediction, 2024 [16], and Baffa, Miyim and Dauda on predicting students' employability, 2023 [15]. A search for El Mrabet and Ait Moussa's paper on academic orientation did "
          "not return the paper itself. The remaining entries were not examined and are not used here."),

        H2("2.8 Research Gap"),
        P("Putting the surveyed work side by side shows what is missing. The placement literature predicts a verdict from a small table of attributes and, at best, wraps it in a web page; the declared "
          "base paper [1] adds reports and e-mail but no measured result and no recommendation. The one paper that combines a strong hybrid model with calibrated probabilities and a "
          "feasibility-filtered recommendation [2] works on admissions, on a data set that is not about placements, with a residual rule that depends on the labels."),
        N("Prediction for a specific company and role, not a generic placed or not placed verdict, with probabilities that are calibrated and therefore usable for ranking.",
          "Actionable guidance: the skill gaps against the target company's cut-offs, and company-role alternatives where the estimated probability is higher - the gap named in the batch survey.",
          "A recommendation module with explicit feasibility rules (CGPA distance by company tier, aptitude margin, backlog rule, package and location preferences) rather than an opaque score.",
          "Role-specific interfaces for students, placement officers (metrics, SHAP, PCA, branch statistics) and recruiters (shortlisting), over code that is separable from the interface.",
          "An honest evaluation: a stated protocol, repeated splits, and a test of whether the hybrid rule of [2] still helps when the residual set cannot use the labels."),
        P("The Smart Campus Placement System addresses these five points. What it cannot close is the data gap: like [1], it runs on synthetic records, so its accuracy figures describe "
          "the method on controlled data and make no claim about real placement outcomes. Chapter 8 reports the results and Chapter 9 states this limit again."),

        H2("2.9 Summary of the Chapter"),
        B("Two papers shape the project: the declared base paper [1], an application paper that reports no numeric result, and the technique paper [2], which supplies the hybrid residual "
          "model, calibration and the recommendation pattern and reports 0.8723 accuracy on 13,000 real admission records.",
          "Eight further works on placement and employability were read at abstract level or better [15]-[22]; they report accuracies between about 78% and 98% on small or undescribed data, "
          "and none reports calibration or a recommendation that is evaluated.",
          "Four titles named in the batch survey and one alternative base paper could not be verified and are not used.",
          "The research gap is a calibrated, company-specific placement predictor with feasibility-filtered recommendations and role-based interfaces, evaluated honestly - the scope of this project."),
    ]
