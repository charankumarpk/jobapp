import fitz  # PyMuPDF
import spacy
import re
import streamlit as st

# Load English NLP model from SpaCy
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file."""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = " "
    for page in doc:
        text += page.get_text("text") + " "
    return text

def load_skills_database():
    """Define a more comprehensive skills set."""
    skills_set = {
        "python", "java", "c", "c++", "c#", "javascript", "typescript", "sql", "html", "css",
        "ruby", "php", "swift", "kotlin", "go", "r", "perl", "dart", "scala", "rust", "matlab",
        "bash", "powershell", "assembly", "react", "angular", "vue", "django", "flask", "spring",
        "tensorflow", "pytorch", "machine learning", "deep learning", "data science",
        "natural language processing", "computer vision", "data structures",
        "database management system", "operating systems", "object-oriented programming"
    }
    return skills_set

def extract_skills(text, skills_set):
    """Extract technical skills from text by matching multi-word and single-word skills."""
    found_skills = set()
    text = text.lower()

    # Use NLP for better phrase matching
    doc = nlp(text)

    # Extract words and phrases
    words = [token.text for token in doc if token.is_alpha]
    phrases = [chunk.text.lower() for chunk in doc.noun_chunks]  # Extract noun phrases

    # Check for matches in single words and phrases
    for skill in skills_set:
        if skill in words or skill in phrases:
            found_skills.add(skill)

    return list(found_skills)

def main():
    st.title("Resume Skill Extractor")
    uploaded_file = st.file_uploader("Upload a Resume (PDF only)", type=["pdf"])

    if uploaded_file is not None:
        text = extract_text_from_pdf(uploaded_file)
        skills_set = load_skills_database()
        skills = extract_skills(text, skills_set)
        st.subheader("Extracted Technical Skills:")
        st.write(", ".join(map(str.capitalize, skills)) if skills else "No technical skills found")

if __name__ == "__main__":
    main()
