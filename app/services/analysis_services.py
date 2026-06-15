from openai import OpenAI
from core.utils import prompts 
import os
from dotenv import load_dotenv


load_dotenv(override=True)
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))




def run_openai_analysis(text, TEST_NAME, TECHNIQUE):
    print(f"INFO: Analysing the given Context")
    CONTEXT = text
    TERMS_DESC = '''[
      {
        "term": "n",
        "desc": "Number of patients who take part in the study/patients who agreed for the study for the given technique and device"
      },
      {
        "term": "Sural Nerve",
        "desc": "Number or Percent of patients who experienced damage to the sural nerve, leading to neuritis.
                Also, Number or Percent of patients who experienced Paraesthesia in the territory of the sural nerve."
      },
      {
        "term": "wound infection",
        "desc": "Number or percentage of wound infections; ensure to consider if the wound infection is for the given technique, including cases where no wound infection is found"
      },
      { 
        "term": "Superficial Infection",
        "desc": "The rate of patients who developed a superficial infection at the surgery site." 
      },
      {
        "term": "Deep Infection",
        "desc": "The rate of patients who developed a deep, potentially septic, infection."
      },
      {
        "term": "rerupture",
        "desc": "Number or percent of patients who experienced a rerupture after the surgery."
      },
      {
        "term": "AOFAS",
        "desc": "Average American Orthopaedic Foot & Ankle Society (AOFAS) score for a technique used in the given study or text"
      },
      {
        "term": "wound dehiscence",
        "desc": "Number of patients who experienced wound dehiscence"
      },
      {
        "term": "Debridement",
        "desc": "The rate at which patients required surgical debridement, a procedure to remove dead or infected tissue to promote healing."
      },
      {
        "term": "Keloid Scars",
        "desc": "The rate of patients who developed keloid scarring."
      },
      {
        "term": "Hypertrophic Scars",
        "desc": "The rate of patients who developed hypertrophic scarring."
      }
      {
        "term": "Average VAS Pain",
        "desc": "The average VAS (Visual Analog Scale) pain score."
      },
      {
        "term": "VAS Satisfaction Average Scores",
        "desc": "The average satisfaction score reported by patients, measured by VAS."
      },
      {
        "term": "Load Failure",
        "desc": "The proportion of cases where the repaired Achilles tendon did not withstand normal forces, leading to mechanical failure ,measured as the ultimate load to failure.
                 The average load to failure for the specified technique."
      },
      {
        "term": "ATRS Score 3 months",
        "desc": "refers to the Achilles Tendon Total Rupture Score (ATRS) measured three months after the surgery for Achilles tendon rupture."
      },
      {
        "term": "ATRS Score 6 months",
        "desc": "The Achilles Tendon Total Rupture Score (ATRS) measured six months after the surgical repair of the Achilles tendon rupture. If not explicitly mentioned, examine sections discussing post-operative follow-up, functional outcomes, rehabilitation progress, results, complications, individual patient data, and any indications of follow-up duration, such as scars mentioned at a certain timeframe after the surgery. Look for any implicit references or clues to the timing of ATRS assessments. Additionally, consider the follow-up period between 6 months and 2 years, as the ATRS scores might be reported during this interval."
      },
      {
        "term": "ATRS Scores Post 2 Years",
        "desc": "The Achilles Tendon Total Rupture Score (ATRS) measured two years after the surgical repair of the Achilles tendon rupture."
      },
      {
        "term": "OR Time (hours)",
        "desc": "The average amount of time the patient spent in the operating room."
      },
      {
        "term": "Recovery Time (months)",
        "desc": "total number of week or months after which patients were allowed to walk OR resumed normal walking after the surgery."
      },  
      {
        "term": "Time to Load Bearing",
        "desc": "The duration until patients are able to stand and bear full weight on the affected limb without the use of aids like crutches or orthoses, following a surgical procedure or injury.
                 It is time period when the patient is allowed to walk with full weight bearing without any aid after the surgery."
      },  
      {
        "term": "Weeks to Rehabilitation",
        "desc": "the amount of time, measured in weeks, from the date of surgery until the patient begins the rehabilitation process. "
      },
      {
        "term": "Base Recovery Sporting",
        "desc": "Number or percent of the patients returned to their pre-injury level of sports activity."
      },
      {
        "term": "Sport Recovery Time (months)",
        "desc": "The number of months or weeks it took for patients to return to their sports activities."
      }
      {
        "term": "Discontinued Previous Sport",
        "desc": "Number or percentage of patients who discontinued their previous level of sport post-operation Ex:- ().
                 It can be calculated by identifying the subset of patients who used to play sports before the injury and then subtracting the number or percent of those who continued sports post-operation from the total number or percentage of patients who used to play sports."
      },  
      {
        "term": "Short term Elongation Impairment",
        "desc": "The rate at which repaired tendons stretched beyond their normal length soon after surgery, potentially affecting function."
      },
      { 
        "term": "Incision",
        "desc": "The length of the surgical cut made during a procedure, measured in centimeters.
        The incision can be made on the sides of the proximal and distal stumps of the tendon."
      },
      {
        "term": "Hospital Stay",
        "desc": "Number of days patients remained hospitalized after undergoing surgery. If it is one night stay give it 1."
      },
    ]
    '''
    SYS_INST_SURGICAL_DEVICE = prompts.SYS_INST_SURGICAL_DEVICE.format(STUDY_TEST_NAME=TEST_NAME,
                                                                       STUDY_TECHNIQUE=TECHNIQUE,
                                                                       STUDY_TERMS_DESC=TERMS_DESC)

    messages = [{"role": "system", "content": SYS_INST_SURGICAL_DEVICE}]
    messages.append({"role": "user", "content": f'This is the context of the study: {CONTEXT}'})

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()




def run_openai_analysis_for_Influenza_diagnostic(CONTEXT, TEST_NAME, TECHNIQUE, SAMPLE):
    print(f"INFO: Analysing the given Context")
    TERMS_DESC = '''[
        {
            "term": "n",
            "desc": "number of patients or specimens or samples were included in study"
        },
        {
            "term": "InfluenzaABSympNAPositives",
            "desc": "number of symptomatic patients or specimens that tested positive for Influenza A or B"
        },
        {
            "term": "InfluenzaABAsympPositives",
            "desc": "number of asymptomatic patients or specimens that tested positive for Influenza A or B"
        },
        {
            "term": "InfluenzaABPositives",
            "desc": "number of patients or specimens that tested positive for Influenza A or B"
        },
        {
            "term": "InfluenzaABNegatives",
            "desc": "number of patients or specimens that tested negative for Influenza A or B"
        },
        {
            "term": "InfluenzaBSympNAPositives",
            "desc": "number of symptomatic patients or specimens that tested positive for Influenza B"
        },
        {
            "term": "InfluenzaBPositives",
            "desc": "number of patients or specimens that tested positive for Influenza B"
        },
        {
            "term": "InfluenzaBNegatives",
            "desc": "number of patients or specimens that tested negative for Influenza B"
        },
        {
            "term": "All True Positive Samples",
            "desc": "number of samples correctly identified as positive"
        },
        {
            "term": "Negative Samples",
            "desc": "number of samples correctly identified as negative"
        },
        {
            "term": "Influenza A Sensitivity/ PPA",
            "desc": "1. proportion of true positive results for Influenza A among all positive cases (Positive Percent Agreement).,
                     2. The sensitivity (PPA) for Influenza A is based on the agreement percentage for detection."
        },
        {
            "term": "Influenza A Specificity/ NPA",
            "desc": "1. proportion of true negative results for Influenza A among all negative cases (Negative Percent Agreement).
                     2. The specificity (NPA) for Influenza A is based on the agreement percentage for negative results."
        },
        {
            "term": "Influenza B Sensitivity/ PPA",
            "desc": "1. proportion of true positive results for Influenza B among all positive cases (Positive Percent Agreement).
                     2. The sensitivity (PPA) for Influenza B are both based on the agreement percentage for detection."
        },
        {
            "term": "Influenza B Specificity/ NPA",
            "desc": "1. proportion of true negative results for Influenza B among all negative cases (Negative Percent Agreement).
                     2. The specificity (NPA) for Influenza B are both based on the agreement percentage for negative results."
        },
        {
        "term": "Influenza A/B (LDT) Ct Value Positive Threshold",
        "desc": "the critical Cycle Threshold (Ct) value at which a laboratory-developed test (LDT) for detecting both Influenza A and Influenza B viruses considers a sample as positive."
        },
        {
        "term": "# Multiplex Differential Diagnoses Per Run",
        "desc": "the number of pathogens being detected in the article."
        },
        {
        "term": "Pathogen Sample Time to Result Hours",
        "desc": "the total time duration it takes for the pathogen detection."
        },
        {
        "term": "Hands on Time (Instrument only) Hours",
        "desc": "the total duration spent actively using the instrument for testing or analysis, excluding any other activities or tasks."
        },
        {
        "term": "Number of Steps Instrument only",
        "desc": "A device or tool that measures the number of steps taken."
        },
        {
        "term": "Percent who easily understood the user manual",
        "desc": "the percentage of individuals who found the user manual for a product or service easy to comprehend and follow without encountering significant difficulties or confusion."
        },
        {
        "term": "Percent of patients who found the test easy to use (as expected)",
        "desc": "the proportion of patients who reported finding a particular medical test easy to utilize according to their expectation."
        },
        {
        "term": "Percent of patients who found the test very easy to use",
        "desc": "the percentage of patients who reported finding a particular medical test extremely straightforward and user-friendly."
        },
        {
        "term": "Percent who correctly interpreted the results",
        "desc": "the percentage of individuals who accurately understood and interpreted the outcomes or findings of a particular test, assessment, or experiment."
        },
        {
        "term": "Percent who were confident they could use the test at home",
        "desc": "the percentage of individuals who expressed assurance in their ability to effectively utilize a particular test or medical device in a home setting."
        }
        ]
    '''
    SYS_INST_SURGICAL_DEVICE = prompts.SYS_INST_DIAGNOSTIC_TEST.format(STUDY_TEST_NAME=TEST_NAME,
                                                                       STUDY_TECHNIQUE=TECHNIQUE, STUDY_SAMPLE=SAMPLE,
                                                                       STUDY_TERMS_DESC=TERMS_DESC)

    messages = [{"role": "system", "content": SYS_INST_SURGICAL_DEVICE}]
    messages.append({"role": "user", "content": f'This is the context of the study: {CONTEXT}'})

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()





def run_openai_analysis_for_sars_diagnostic(text, TEST_NAME, TECHNIQUE, SAMPLE):
    print(f"INFO: Analysing the given Context")
    TERMS_DESC = '''[
            {
            "term": "n",
            "desc": "number of patients or specimens or samples were included in study"
            },
            {
            "term": "COVIDSympNAPositives",
            "desc": "Number of COVID-19 positive cases with symptoms and nucleic acid test positive results"            
            },
            {
            "term": "COVIDAsympPositives",
            "desc": "Number of COVID-19 positive cases without symptoms but with positive test results"
            },
            {
            "term": "COVIDPositives",
            "desc": "Total number of confirmed COVID-19 positive cases, including both symptomatic and asymptomatic"
            },
            {
            "term": "COVIDNegatives",
            "desc": "Number of individuals tested for COVID-19 who received negative results"
            },
            {
            "term" : "SARS-CoV-2 Positive Percent Agreement",
            "description" : "sensitivity or true positive rate, represents the proportion of positive cases correctly identified by a {TEST_NAME} compared to a reference standard."
            },
            {
            "term" : "SARS-CoV-2 Negative Percent Agreement",
            "desc" : "specificity or true negative rate, represents the proportion of negative cases correctly identified by a {TEST_NAME} test compared to a reference standard."
            },
            {
            "term" : "SARS-CoV-2 Ct Value Positive Detection Cutoff",
            "desc" : "threshold cycle (Ct) value used to determine the positivity of SARS-CoV-2 detection in PCR tests across all individuals, including both symptomatic and asymptomatic cases, or the Ct value at which the sensitivity of the test is less than 75%."
            },
            {
            "term" : "SARS-CoV-2 Asymptomatic Sensitivity",
            "desc" : "the proportion of asymptomatic positive cases"
            },
            {
            "term" : "SARS-CoV-2 Symptomatic Sensitivity",
            "desc" : "the proportion of symptomatic positive cases"
            },
            {
            "term" : "SARS-CoV-2 Asymptomatic Specificity",
            "desc" : "the proportion of asymptomatic negative cases"
            },
            {
            "term" : "SARS-CoV-2 Symptomatic Specificity",
            "desc" : "the proportion of symptomatic negative cases correctly"
            },  
            {
            "term" : "SARS-CoV-2 Days Past Infection/Symptom Onset Sensitivity Day 0/2/6/10",
            "desc" : "1. SARS-CoV-2 Days Past Infection/Symptom Onset Sensitivity Day 0: This term refers to the sensitivity of a diagnostic test for detecting SARS-CoV-2 infection or symptoms on the same day as the onset of symptoms or infection.
                      2. SARS-CoV-2 Days Past Infection/Symptom Onset Sensitivity Day 2: This term refers to the sensitivity of a diagnostic test for detecting SARS-CoV-2 infection or symptoms two days after the onset of symptoms or infection.
                      3. SARS-CoV-2 Days Past Infection/Symptom Onset Sensitivity Day 6: This term refers to the sensitivity of a diagnostic test for detecting SARS-CoV-2 infection or symptoms six days after the onset of symptoms or infection.
                      4. SARS-CoV-2 Days Past Infection/Symptom Onset Sensitivity Day 10: This term refers to the sensitivity of a diagnostic test for detecting SARS-CoV-2 infection or symptoms ten days after the onset of symptoms or infection."
            }, 
            {
            "term": "# Multiplex Differential Diagnoses Per Run",
            "desc": "the number of pathogens being detected in the article."
            },
            {
            "term": "Pathogen Sample Time to Result Hours",
            "desc": "the total time duration it takes for the pathogen detection."
            },
            {
            "term": "Hands on Time (Instrument only) Hours",
            "desc": "the total duration spent actively using the instrument for testing or analysis, excluding any other activities or tasks."
            },
            {
            "term": "Number of Steps Instrument only",
            "desc": "A device or tool that measures the number of steps taken."
            },
            {
            "term": "Percent who easily understood the user manual",
            "desc": "the percentage of individuals who found the user manual for a product or service easy to comprehend and follow without encountering significant difficulties or confusion."
            },
            {
            "term": "Percent of patients who found the test easy to use (as expected)",
            "desc": "the proportion of patients who reported finding a particular medical test easy to utilize according to their expectation."
            },
            {
            "term": "Percent of patients who found the test very easy to use",
            "desc": "the percentage of patients who reported finding a particular medical test extremely straightforward and user-friendly."
            },
            {
            "term": "Percent who correctly interpreted the results",
            "desc": "the percentage of individuals who accurately understood and interpreted the outcomes or findings of a particular test, assessment, or experiment."
            },
            {
            "term": "Percent who were confident they could use the test at home",
            "desc": "the percentage of individuals who expressed assurance in their ability to effectively utilize a particular test or medical device in a home setting."
            }
            ]
        '''
    SYS_INST_SURGICAL_DEVICE = prompts.SYS_INST_DIAGNOSTIC_TEST.format(STUDY_TEST_NAME=TEST_NAME,
                                                                       STUDY_TECHNIQUE=TECHNIQUE, STUDY_SAMPLE=SAMPLE,
                                                                       STUDY_TERMS_DESC=TERMS_DESC)

    messages = [{"role": "system", "content": SYS_INST_SURGICAL_DEVICE}]
    messages.append({"role": "user", "content": f'This is the context of the study: {text}'})

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()





def run_openai_finding_keywords_for_search(result):
    print(f"Called function 'run_openai_finding_keywords_for_search'")
    system_prompt = '''
    Analyze the following text from medical research papers on diagnostic methods and medical devices. Please perform the task below:
    Identify common technical terms related to the disease, procedure, specialty, competitors, current techniques, diagnosis, and treatment methods or devices discussed in the text.
    Based on these technical terms, generate a list of search phrases that specifically combine concepts of comparative clinical effectiveness and comparative economic impact. These phrases should be suitable for searching academic databases like Google Scholar or PubMed.
    Return the output in a Python list, e.g.:
    [
        "Comparative clinical effectiveness of MRI versus ultrasound in Achilles tendon rupture diagnosis",
        "Economic impact of growth factor therapies in Achilles tendon injury treatment",
        "Cost-effectiveness analysis of low-frequency vibration training in tendon rehabilitation"
    ]
    Your Response must only contain the python list which carry search results.
    Ensure your analysis is concise yet comprehensive, focusing on aspects that link clinical outcomes with economic considerations.

    '''
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": f"Text to analyze: {result}"})
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()

