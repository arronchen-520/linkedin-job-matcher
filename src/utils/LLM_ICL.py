icl_example = """
### EXAMPLE 1: THE HARD REJECT (Logic: Tech Stack Mismatch)
[[JD Summary]]: Senior Backend Engineer. Requirements: Expert in C++, Rust, Embedded Systems, Linux Kernel.
[[Resume Summary]]: Machine Learning Engineer. Skills: Python, PyTorch, Scikit-Learn, Jupyter.
[[Evaluation]]:
{
    "match_score": 35,
    "reasoning": "REJECT: Fundamental Tech Stack Mismatch. JD requires low-level systems programming (C++/Rust), while candidate focuses on high-level ML scripting (Python). These are distinct engineering domains.",
    "missing_skills": ["C++", "Rust", "Embedded Systems"]
}

### EXAMPLE 2: THE TRANSFERABLE MATCH (Logic: Smart Flexibility)
[[JD Summary]]: Cloud Data Engineer. Requirements: 5+ years exp. Must know GCP BigQuery and Airflow.
[[Resume Summary]]: Data Engineer. 4 years exp. Expert in AWS Redshift and AWS Step Functions.
[[Evaluation]]:
{
    "match_score": 82,
    "reasoning": "Strong Match despite tool differences. Candidate's deep expertise in AWS stack (Redshift, Step Functions) is highly transferable to the required GCP stack (BigQuery, Airflow). The 1-year experience gap is acceptable given the strong skill alignment.",
    "missing_skills": []
}

### EXAMPLE 3: THE SENIORITY TRAP (Logic: Experience Gap)
[[JD Summary]]: Senior Product Manager. Requirements: 5+ years of PM experience, experience leading roadmaps.
[[Resume Summary]]: Associate Product Manager. 2 years of experience. Assisting on roadmaps, no leadership exp.
[[Evaluation]]:
{
    "match_score": 55,
    "reasoning": "REJECT: Significant Seniority Gap. JD requires a Senior level (5+ years) with leadership experience, but candidate is Junior (2 years) with only support experience. This gap is too large to bridge.",
    "missing_skills": ["5+ Years Experience", "Roadmap Leadership"]
}
"""