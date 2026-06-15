import os, shutil
from core.settings import OUTPUT_DIR, BASE_PATH, DATA_DIR, BASE_DIR
from fastapi import File, UploadFile
from core.utils.pdf_utils import extract_text_from_pdf, remove_unwanted_sections
from core.utils.csv_utils import create_csv, parse_response, write_data_to_csv
from services.analysis_services import run_openai_analysis, run_openai_analysis_for_sars_diagnostic, run_openai_analysis_for_Influenza_diagnostic



path = os.path.join(BASE_DIR, "data", "surgical_file.csv")




def term_extractor( article_type: str,
    surgical_device_name: str,
    surgical_technique: str , 
    diagnostic_test_type: str,
    diagnostic_test_name: str,
    diagnostic_sample_type: str, 
    diagnostic_technique: str,
    file: UploadFile):
     
    if article_type == "Surgical Device":
         result = analyze_surgical_device(file, surgical_device_name, surgical_technique)
         return result
    elif article_type == "Diagnostic":
         result = analyze_diagnostic(file, diagnostic_test_name, diagnostic_technique, diagnostic_sample_type, diagnostic_test_type)
         return result





def analyze_surgical_device(pdf_file: UploadFile, device_name, technique):
        temp_pdf_path = os.path.join(BASE_DIR, "data", "temp.pdf")
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        with open(temp_pdf_path, "wb") as f:
            shutil.copyfileobj(pdf_file.file, f)

        text = extract_text_from_pdf(temp_pdf_path)
        cleaned_text = remove_unwanted_sections(text)

        analysis_result = run_openai_analysis(cleaned_text, device_name, technique)
        print(analysis_result)

        data = parse_response(analysis_result, pdf_file.filename)
        data["Device"] = device_name
        data["Technique"] = technique
        fieldsname = [
            "Reference", "Device", "Technique", "n", "Sural Nerve", "wound infection", "Superficial Infection",
            "Deep Infection", "rerupture", "AOFAS", "wound dehiscence",
            "Debridement", "Keloid Scars", "Hypertrophic Scars",
            "Average VAS Pain", "VAS Satisfaction Average Scores",
            "Load Failure", "ATRS Score 3 months", "ATRS Score 6 months",
            "ATRS Scores Post 2 Years", "OR Time (hours)",
            "Recovery Time (months)", "Time to Load Bearing",
            "Weeks to Rehabilitation", "Base Recovery Sporting",
            "Sport Recovery Time (months)", "Discontinued Previous Sport",
            "Short term Elongation Impairment", "Incision", "Hospital Stay"
        ]
        write_data_to_csv(data, path, fieldsname)
        print(f"Returning output from Surgical Device file.")

        return analysis_result





def analyze_diagnostic(pdf_file:UploadFile, test_name, technique, sample, diagnostic_type):
        temp_pdf_path = os.path.join(BASE_DIR, "data", "temp.pdf")
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        with open(temp_pdf_path, "wb") as f:
            shutil.copyfileobj(pdf_file.file, f)

        text = extract_text_from_pdf(temp_pdf_path)
        cleaned_text = remove_unwanted_sections(text)

        if diagnostic_type == "Influenza":
            path = os.path.join(BASE_DIR, "data", "flu.csv")
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)
            
            analysis_result = run_openai_analysis_for_Influenza_diagnostic(cleaned_text, test_name, technique, sample)
            fieldsname = [
                "Reference",
                "Test Name",
                "Technique",
                "Sample",
                "n",
                "InfluenzaABSympNAPositives",
                "InfluenzaABAsympPositives",
                "InfluenzaABPositives",
                "InfluenzaABNegatives",
                "InfluenzaBSympNAPositives",
                "InfluenzaBPositives",
                "InfluenzaBNegatives",
                "All True Positive Samples",
                "Negative Samples",
                "Influenza A Sensitivity/ PPA",
                "Influenza A Specificity/ NPA",
                "Influenza B Sensitivity/ PPA",
                "Influenza B Specificity/ NPA",
                "Influenza A/B (LDT) Ct Value Positive Threshold",
                "# Multiplex Differential Diagnoses Per Run",
                "Pathogen Sample Time to Result Hours",
                "Hands on Time (Instrument only) Hours",
                "Number of Steps Instrument only",
                "Percent who easily understood the user manual",
                "Percent of patients who found the test easy to use (as expected)",
                "Percent of patients who found the test very easy to use",
                "Percent who correctly interpreted the results",
                "Percent who were confident they could use the test at home"
            ]
        else:
            path = os.path.join(BASE_DIR, "data", "sars.csv")
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)
            analysis_result = run_openai_analysis_for_sars_diagnostic(cleaned_text, test_name, technique, sample)
            fieldsname = [
                "Reference",
                "Test Name",
                "Technique",
                "Sample",
                "n",
                "COVIDSympNAPositives",
                "COVIDAsympPositives",
                "COVIDPositives",
                "COVIDNegatives",
                "SARS-CoV-2 Positive Percent Agreement",
                "SARS-CoV-2 Negative Percent Agreement",
                "SARS-CoV-2 Ct Value Positive Detection Cutoff",
                "SARS-CoV-2 Asymptomatic Sensitivity",
                "SARS-CoV-2 Symptomatic Sensitivity",
                "SARS-CoV-2 Asymptomatic Specificity",
                "SARS-CoV-2 Symptomatic Specificity",
                "SARS-CoV-2 Days Past Infection/Symptom Onset Sensitivity Day 0/2/6/10",
                "# Multiplex Differential Diagnoses Per Run",
                "Pathogen Sample Time to Result Hours",
                "Hands on Time (Instrument only) Hours",
                "Number of Steps Instrument only",
                "Percent who easily understood the user manual",
                "Percent of patients who found the test easy to use (as expected)",
                "Percent of patients who found the test very easy to use",
                "Percent who correctly interpreted the results",
                "Percent who were confident they could use the test at home"
            ]
        data = parse_response(analysis_result, pdf_file.filename)
        data["Test Name"] = test_name
        data["Technique"] = technique
        data["Sample"] = sample
        write_data_to_csv(data, path, fieldsname)
        print(f"Returning output from Diagnostic file.")
        return analysis_result

