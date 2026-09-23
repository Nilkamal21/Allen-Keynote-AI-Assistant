import fitz
import re
import json
import os
from typing import List, Dict, Any

STANDARD_SECTIONS = [
    "Constitution", "Mental Generals", "Mental", "Mentals", "Physical Generals", "Physical General",
    "Head", "Outer Head", "Eyes", "Ears", "Nose", "Face", "Mouth", "Teeth", "Throat",
    "Stomach", "Abdomen", "Stool", "Stool and Rectum", "Stool and Anus",
    "Gastro-intestinal System", "Digestive System", "Digestion",
    "Urinary System", "Urinary", "Bladder", "Kidney", "Urine",
    "Male Reproductive System", "Male", "Female Reproductive System", "Female",
    "Respiratory System", "Chest", "Heart", "Cardio-vascular System", "Circulation",
    "Neck", "Back", "Neck and Back", "Back and Extremities", "Extremities", "Limbs in General", "Upper Limbs", "Lower Limbs",
    "Nervous System", "Neuro-muscular System", "Fever", "Skin", "Sleep",
    "Modalities", "Motdalities", "Relation", "Relations", "Concomitants"
]

NON_REMEDY_TITLES = [
    "REMEDIES", "ASSOCIATED REMEDIES", "THE BOWEL NOSODES", "CONTENTS",
    "INDEX", "REPERTORIAL INDEX", "EDITOR'S NOTE", "PUBLISHER'S NOTE",
    "PREFACE TO SIXTH EDITION", "PREFACE TO THIRD EDITION", "PREFACE TO SECOND EDITION",
    "PREFACE TO FIRST EDITION", "INTRODUCTION"
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\ufffd\u25cf\u25a0\u2022]+', '• ', text)
    text = re.sub(r'•\s*', '• ', text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def extract_cross_references(text: str) -> List[str]:
    matches = re.findall(r'\(([A-Z][a-z0-9\-]+(?:\.|\b)(?:,\s*[A-Z][a-z0-9\-]+(?:\.|\b))*)\)', text)
    refs = set()
    for m in matches:
        parts = [p.strip().rstrip('.') for p in m.split(',')]
        for p in parts:
            if len(p) >= 2 and p[0].isupper():
                refs.add(p)
    return sorted(list(refs))

def parse_allens_keynotes_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    doc = fitz.open(pdf_path)
    chunks = []

    current_remedy = ""
    current_common_name = ""
    current_family = ""
    current_section = "General"
    current_lines = []
    current_start_page = 1
    section_type = "materia_medica"
    chunk_counter = 0

    def finalize_chunk(next_page: int):
        nonlocal current_lines, current_remedy, current_common_name, current_family, current_section, current_start_page, section_type, chunk_counter
        if not current_lines or not current_remedy:
            current_lines = []
            return
        
        # Skip generic non-remedy titles
        if current_remedy.strip().upper() in NON_REMEDY_TITLES:
            current_lines = []
            return

        full_text = clean_text('\n'.join(current_lines))
        if len(full_text.strip()) < 15:
            current_lines = []
            return

        chunk_counter += 1
        rem_slug = re.sub(r'[^a-zA-Z0-9]', '_', current_remedy.lower())
        sec_slug = re.sub(r'[^a-zA-Z0-9]', '_', current_section.lower())
        chunk_id = f"{rem_slug}_{sec_slug}_p{current_start_page}_{chunk_counter}"
        
        cross_refs = extract_cross_references(full_text)

        chunks.append({
            "chunk_id": chunk_id,
            "remedy_name": current_remedy,
            "common_name": current_common_name,
            "family": current_family,
            "section": current_section,
            "start_page": current_start_page,
            "end_page": next_page,
            "section_type": section_type,
            "cross_references": cross_refs,
            "text": full_text
        })
        current_lines = []

    for page_idx in range(len(doc)):
        page_num = page_idx + 1
        page = doc[page_idx]

        if page_num < 20:
            continue
        elif 20 <= page_num <= 421:
            section_type = "materia_medica"
        elif 422 <= page_num <= 439:
            section_type = "bowel_nosodes"
        else:
            section_type = "repertorial_index"

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                line_text = ""
                max_size = 0
                is_bold = False
                is_italic = False

                for span in line["spans"]:
                    t = span["text"]
                    line_text += t
                    sz = round(span["size"], 1)
                    if sz > max_size:
                        max_size = sz
                    if span["flags"] in (20, 22):
                        is_bold = True
                    if span["flags"] in (6, 22):
                        is_italic = True

                line_clean = line_text.strip()
                if not line_clean:
                    continue

                if max_size >= 18.0 and line_clean.isupper() and len(line_clean) >= 3 and not line_clean.startswith("PAGE"):
                    finalize_chunk(page_num)
                    current_remedy = line_clean
                    current_common_name = ""
                    current_family = ""
                    current_section = "General / Constitution"
                    current_start_page = page_num
                    continue

                if current_remedy and max_size == 15.0 and (is_italic or is_bold) and not current_common_name and len(current_lines) == 0:
                    if not current_common_name:
                        current_common_name = line_clean
                    elif not current_family:
                        current_family = line_clean
                    continue

                if max_size <= 13.5 and max_size >= 12.0 and is_bold:
                    matched_sec = None
                    for sec in STANDARD_SECTIONS:
                        if line_clean.lower() == sec.lower() or line_clean.lower().startswith(sec.lower()):
                            matched_sec = sec
                            break
                    
                    if matched_sec or (line_clean.isupper() and len(line_clean) > 3):
                        finalize_chunk(page_num)
                        current_section = line_clean
                        current_start_page = page_num
                        continue

                current_lines.append(line_clean)

    finalize_chunk(len(doc))
    doc.close()
    return chunks

if __name__ == "__main__":
    pdf_file = r"C:\Users\adhik\OneDrive\Desktop\Allen Keynote\441647980-NEW-ALLENS-KEYNOTES-ALLEN-HC-1.pdf"
    print(f"Parsing PDF: {pdf_file}...")
    extracted_chunks = parse_allens_keynotes_pdf(pdf_file)
    print(f"Extraction complete! Total chunks generated: {len(extracted_chunks)}")
    
    os.makedirs("backend/data", exist_ok=True)
    with open("backend/data/processed_chunks.json", "w", encoding="utf-8") as f:
        json.dump(extracted_chunks, f, indent=2, ensure_ascii=False)
    print("Saved clean chunks to backend/data/processed_chunks.json")
