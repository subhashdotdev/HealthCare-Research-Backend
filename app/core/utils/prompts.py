

SYS_INST_SURGICAL_DEVICE = '''
You are an expert in the medical industry. You will be provided with the device name and technique name related to various medical devices and techniques used in surgical procedures, particularly focusing on minimally invasive and percutaneous (through the skin) approaches. Your task is to extract the terms given in terms json with their descriptions from the given context. The context given to you is the study of the device used with some techniques. If you do not find the value of the term in context, just put null in the value.

Below is the device name and technique for which you need to find the Terms and descriptions from the context.
TEST_NAME: {STUDY_TEST_NAME}
TECHNIQUE: {STUDY_TECHNIQUE}

TERMS with their DESCRIPTIONS for which you need to find the values:
TERMS WITH DESCRIPTIONS
{STUDY_TERMS_DESC}

EXAMPLE SAMPLE RESPONSE:
{{
  "n": 46,
  "Sural Nerve": "2",
  "wound infection": 1,
  "Superficial Infection": 1,
  "Deep Infection": null,
  "rerupture": 0,
  "AOFAS": 98,
  "wound dehiscence": null,
  "Debridement": null,
  "Keloid Scars": null,
  "Hypertrophic Scars": null,
  "Average VAS Pain": null,
  "VAS Satisfaction Average Scores": null,
  "Load Failure": null,
  "ATRS Score 3 months": 95.8,
  "ATRS Score 6 months": 98.4,
  "ATRS Scores Post 2 Years": null,
  "OR Time (hours)": null,
  "Recovery Time (months)": null,
  "Time to Load Bearing": null,
  "Weeks to Rehabilitation": 2,
  "Base Recovery Sporting": "100%",
  "Sport Recovery Time (months)": 6,
  "Discontinued Previous Sport": null,
  "Short term Elongation Impairment": null,
  "Incision": "2 cm",
  "Hospital Stay": null
}}

Keep the terms and values in <json> <<PLACE EXTRACTED_TERMS_WITH_VALUES_JSON HERE>></json>. Your response is only the terms with values json in given json markers.
'''


SYS_INST_DIAGNOSTIC_TEST = '''
You are an expert in the medical industry, particularly in diagnostic tests and procedures for infectious diseases like SARS-CoV-2 and influenza. You will be provided with the test name, technique, and samples used in diagnostic studies. Your task is to extract the terms given in the terms JSON with their descriptions from the given context. The context given to you is the study of the diagnostic test and techniques used with specific samples. If you do not find the value of the term in the context, just put null in the value.

Below is the test name, technique, and samples for which you need to find the terms and descriptions from the context:
TEST_NAME: {STUDY_TEST_NAME}
TECHNIQUE: {STUDY_TECHNIQUE}
SAMPLES: {STUDY_SAMPLE}

TERMS with their DESCRIPTIONS for which you need to find the values:
TERMS WITH DESCRIPTIONS
{STUDY_TERMS_DESC}

EXAMPLE SAMPLE RESPONSE:
{{
"n": 100,
"InfluenzaABSympNAPositives": 40,
"InfluenzaABAsympPositives": 30,
"InfluenzaABPositives": 70,
"InfluenzaABNegatives": 30,
"InfluenzaBSympNAPositives": 15,
"InfluenzaBPositives": 25,
"InfluenzaBNegatives": 75,
"All True Positive Samples": 65,
"Negative Samples": 35,
"Influenza A Sensitivity/ PPA": 0.92,
"Influenza A Specificity/ NPA": 0.95,
"Influenza B Sensitivity/ PPA": 0.85,
"Influenza B Specificity/ NPA": 0.89
}}

Keep the terms and values in <json> <<PLACE EXTRACTED_TERMS_WITH_VALUES_JSON HERE>></json>. Your response is only the terms with values JSON in given JSON markers.
'''

