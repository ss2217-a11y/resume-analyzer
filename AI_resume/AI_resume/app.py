import os
import json
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
import docx
from pdfminer.high_level import extract_text
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def extract_text_from_file(file_path):
    file_extension = file_path.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_path)
    elif file_extension == 'txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return None

def analyze_resume(text):
    # Basic metrics
    word_count = len(word_tokenize(text))
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text.lower())
    filtered_tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    
    # Common skills to look for
    common_skills = [
        "python", "java", "javascript", "html", "css", "react", "angular", "vue", 
        "node.js", "express", "django", "flask", "sql", "nosql", "mongodb", 
        "postgresql", "mysql", "aws", "azure", "gcp", "docker", "kubernetes", 
        "ci/cd", "git", "agile", "scrum", "machine learning", "data analysis", 
        "tensorflow", "pytorch", "nlp", "computer vision", "data science"
    ]
    
    # Look for skills in the text
    skills_found = []
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text.lower()):
            skills_found.append(skill)
    
    # Check for education keywords
    education_keywords = ["bachelor", "master", "phd", "degree", "university", "college", "diploma"]
    has_education = any(keyword in text.lower() for keyword in education_keywords)
    
    # Check for experience
    experience_pattern = re.compile(r'\b(\d+)\s*(?:years?|yrs?)\b', re.IGNORECASE)
    experience_matches = experience_pattern.findall(text.lower())
    years_experience = sum(int(year) for year in experience_matches) if experience_matches else 0
    
    # Calculate score (simple version)
    score = 0
    
    # Score based on word count (10 points max)
    if word_count > 300:
        score += 10
    else:
        score += (word_count / 300) * 10
    
    # Score based on skills (40 points max)
    skill_score = min(len(skills_found) * 5, 40)
    score += skill_score
    
    # Score based on education (20 points max)
    if has_education:
        score += 20
    
    # Score based on experience (30 points max)
    experience_score = min(years_experience * 5, 30)
    score += experience_score
    
    # Normalize score to 100
    final_score = min(score, 100)
    
    return {
        "score": final_score,
        "word_count": word_count,
        "skills": skills_found,
        "has_education": has_education,
        "years_experience": years_experience,
        "feedback": generate_feedback(final_score, skills_found, has_education, years_experience)
    }

def generate_feedback(score, skills, has_education, years_experience):
    feedback = []
    
    if score < 50:
        feedback.append("Your resume needs significant improvement.")
    elif score < 70:
        feedback.append("Your resume is average and could use some enhancement.")
    else:
        feedback.append("Your resume is strong, but there's always room for improvement.")
    
    if len(skills) < 5:
        feedback.append("Consider adding more relevant skills to your resume.")
    
    if not has_education:
        feedback.append("Add your educational background to strengthen your resume.")
    
    if years_experience < 2:
        feedback.append("Highlight any relevant experience, even if it's from internships or projects.")
    
    return feedback

def generate_improved_resume(original_text, analysis):
    prompt = f"""
    I need to improve the following resume that scored {analysis['score']} out of 100:
    
    {original_text}
    
    Analysis:
    - Skills found: {', '.join(analysis['skills'])}
    - Education mentioned: {'Yes' if analysis['has_education'] else 'No'}
    - Years of experience: {analysis['years_experience']}
    
    Please create an improved version of this resume that:
    1. Maintains the same personal information and core experience
    2. Uses stronger action verbs and quantifiable achievements
    3. Improves formatting and organization
    4. Adds any missing sections (summary, skills, education, experience)
    5. Highlights relevant skills more effectively
    
    Format the resume professionally with clear section headings.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use appropriate model
            messages=[
                {"role": "system", "content": "You are an expert resume writer who improves resumes to make them more effective."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating improved resume: {e}")
        return "Error generating improved resume. Please try again later."

def generate_resume_with_template(original_text, analysis, template_type):
    """Generate a resume with a specific template style"""
    
    template_descriptions = {
        "modern": "A clean, modern resume with bold section headers, subtle use of color, and a two-column layout.",
        "traditional": "A classic, professional resume with traditional formatting, serif fonts, and a single-column layout.",
        "creative": "A creative resume with unique formatting, modern fonts, and visual elements to stand out.",
        "technical": "A technical resume emphasizing skills with skill bars, technical competencies section, and project highlights."
    }
    
    prompt = f"""
    I need to improve the following resume that scored {analysis['score']} out of 100 and format it using a {template_type} template.
    
    Template style: {template_descriptions[template_type]}
    
    Original Resume:
    {original_text}
    
    Analysis:
    - Skills found: {', '.join(analysis['skills'])}
    - Education mentioned: {'Yes' if analysis['has_education'] else 'No'}
    - Years of experience: {analysis['years_experience']}
    
    Please create an improved version of this resume that:
    1. Maintains the same personal information and core experience
    2. Uses stronger action verbs and quantifiable achievements
    3. Follows the {template_type} template style described above
    4. Adds any missing sections (summary, skills, education, experience)
    5. Highlights relevant skills more effectively
    
    Format the resume professionally with clear section headings and provide HTML formatting that can be directly used in a web page.
    Include appropriate CSS styling inline within the HTML to match the {template_type} template style.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are an expert resume writer who creates professional {template_type} style resumes with HTML/CSS formatting."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating resume with template: {e}")
        return "Error generating resume with template. Please try again later."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['resume']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Extract text from the file
        resume_text = extract_text_from_file(file_path)
        
        if resume_text:
            # Analyze the resume
            analysis = analyze_resume(resume_text)
            
            # Generate improved resume if score is below threshold
            improved_resume = None
            if analysis['score'] < 70:  # Threshold for "good" resume
                improved_resume = generate_improved_resume(resume_text, analysis)
            
            return render_template(
                'results.html', 
                analysis=analysis, 
                original_text=resume_text,
                improved_resume=improved_resume
            )
        else:
            flash('Could not extract text from the file')
            return redirect(request.url)
    else:
        flash('File type not allowed')
        return redirect(request.url)

@app.route('/generate_template', methods=['POST'])
def generate_template():
    """Generate a resume with a specific template"""
    data = request.json
    original_text = data.get('original_text')
    analysis = json.loads(data.get('analysis'))
    template_type = data.get('template_type', 'modern')
    
    if not original_text or not analysis:
        return jsonify({"error": "Missing required data"}), 400
    
    # Generate resume with selected template
    template_resume = generate_resume_with_template(original_text, analysis, template_type)
    
    return jsonify({"template_resume": template_resume})

if __name__ == '__main__':
    app.run(debug=True)