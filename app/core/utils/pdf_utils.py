import fitz, re, os, pymupdf
from collections import Counter
from fastapi import UploadFile
from core.utils.aws_utils import s3_download_pdf
from core.utils.gcp_utils import download_pdf_file




def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text





def remove_unwanted_sections(text, section_to_remove="References"):
    pattern = re.compile(rf'{section_to_remove}.*', re.DOTALL | re.IGNORECASE)
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text





def extract_results_section(text):
    """
    Extracts the results section from the text using regex.
    :param text: The full text from which to extract the results section.
    :return: The extracted results section.
    """
    match = re.search(
        r'(?i)results?(.+?)(?=(conclusions?|discussion|references?|acknowledgements?|methods?|materials?))', text,
        re.DOTALL)
    return match.group(1).strip() if match else "Results section not found."





def process_pdfs(input_dir, output_dir, results_file):
    """
    Processes all PDF files in the input directory, extracts text, saves it,
    extracts results sections, and saves them in a single results file.
    :param input_dir: Directory containing PDF files.
    :param output_dir: Directory to save extracted text files.
    :param results_file: File to save all extracted results sections.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    results = []

    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename)
            text = extract_text_from_pdf(pdf_path)

            text_filename = os.path.splitext(filename)[0] + '_text.txt'
            text_filepath = os.path.join(output_dir, text_filename)

            with open(text_filepath, 'w', encoding='utf-8') as text_file:
                text_file.write(text)

            result_section = extract_results_section(text)
            results.append(f"Results for {filename}:\n{result_section}\n{'-' * 80}\n")

    with open(results_file, 'w', encoding='utf-8') as results_output:
        results_output.write("\n".join(results))
    return results




def process_pdfs(s3_pdf_path):
    results = []
    print("s3_path", s3_pdf_path)
    
    downloaded_pdf = download_pdf_file(path=s3_pdf_path)

    print("DOWNLOADED PDF ", downloaded_pdf)
    text = extract_text_from_pdf(downloaded_pdf)
    result_section = extract_results_section(text)
    results.append((result_section))
    return results

