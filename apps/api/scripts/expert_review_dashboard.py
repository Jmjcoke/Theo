#!/usr/bin/env python3
"""
Expert Review Dashboard for Hermeneutics Validation

A simple web interface for theological experts to review and score
validation results from the hermeneutics filter validation system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExpertScores:
    """Expert evaluation scoring model"""
    theological_accuracy: int = Field(ge=1, le=10, description="Theological accuracy (1-10)")
    hermeneutical_soundness: int = Field(ge=1, le=10, description="Hermeneutical method (1-10)")
    biblical_fidelity: int = Field(ge=1, le=10, description="Faithfulness to Scripture (1-10)")
    clarity_and_precision: int = Field(ge=1, le=10, description="Clarity of explanation (1-10)")
    practical_application: int = Field(ge=1, le=10, description="Practical relevance (1-10)")
    overall_assessment: int = Field(ge=1, le=10, description="Overall quality (1-10)")
    
    detailed_feedback: str = Field(description="Detailed expert commentary")
    improvement_suggestions: List[str] = Field(description="Specific improvement recommendations")
    theological_concerns: List[str] = Field(default=[], description="Any doctrinal concerns")


class ExpertReviewDashboard:
    """Web interface for theological experts to review validation results"""
    
    def __init__(self, validation_results_dir: str):
        self.results_dir = Path(validation_results_dir)
        self.expert_reviews_dir = self.results_dir / "expert_reviews"
        self.expert_reviews_dir.mkdir(exist_ok=True)
        
        self.app = FastAPI(title="Hermeneutics Expert Review Dashboard")
        self.templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes for the dashboard"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard showing available validation results"""
            validation_files = list(self.results_dir.glob("hermeneutics_validation_*.json"))
            validation_sessions = []
            
            for file_path in validation_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    metadata = data.get("validation_metadata", {})
                    comparison = data.get("comparative_analysis", {})
                    
                    session_info = {
                        "filename": file_path.name,
                        "start_time": metadata.get("start_time", "Unknown"),
                        "dataset_size": metadata.get("dataset_size", 0),
                        "accuracy_improvement": comparison.get("accuracy_improvement_percent", 0),
                        "advanced_count": len(data.get("advanced_pipeline", [])),
                        "basic_count": len(data.get("basic_pipeline", []))
                    }
                    validation_sessions.append(session_info)
                    
                except Exception as e:
                    logger.error(f"Error reading validation file {file_path}: {e}")
            
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "validation_sessions": validation_sessions
            })
        
        @self.app.get("/review/{filename}", response_class=HTMLResponse)
        async def review_session(request: Request, filename: str):
            """Review interface for a specific validation session"""
            file_path = self.results_dir / filename
            
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Validation file not found")
            
            try:
                with open(file_path, 'r') as f:
                    validation_data = json.load(f)
                
                # Combine advanced and basic results for comparison
                advanced_results = validation_data.get("advanced_pipeline", [])
                basic_results = validation_data.get("basic_pipeline", [])
                
                # Create combined review data
                review_items = []
                for i, adv_result in enumerate(advanced_results):
                    if i < len(basic_results):
                        basic_result = basic_results[i]
                        
                        review_item = {
                            "test_id": adv_result.get("test_id"),
                            "question": adv_result.get("question"),
                            "reference_answer": adv_result.get("reference_answer"),
                            "evaluation_criteria": adv_result.get("evaluation_criteria", []),
                            "advanced_response": {
                                "text": adv_result.get("response"),
                                "confidence": adv_result.get("metadata", {}).get("confidence", 0),
                                "execution_time": adv_result.get("execution_time", 0),
                                "scores": adv_result.get("scores", {})
                            },
                            "basic_response": {
                                "text": basic_result.get("response"),
                                "confidence": basic_result.get("metadata", {}).get("confidence", 0),
                                "execution_time": basic_result.get("execution_time", 0),
                                "scores": basic_result.get("scores", {})
                            }
                        }
                        review_items.append(review_item)
                
                comparison = validation_data.get("comparative_analysis", {})
                
                return self.templates.TemplateResponse("review_session.html", {
                    "request": request,
                    "filename": filename,
                    "review_items": review_items,
                    "comparison": comparison,
                    "metadata": validation_data.get("validation_metadata", {})
                })
                
            except Exception as e:
                logger.error(f"Error loading validation data: {e}")
                raise HTTPException(status_code=500, detail="Error loading validation data")
        
        @self.app.get("/review/{filename}/question/{test_id}", response_class=HTMLResponse)
        async def review_question(request: Request, filename: str, test_id: str):
            """Detailed review interface for a specific question"""
            file_path = self.results_dir / filename
            
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Validation file not found")
            
            try:
                with open(file_path, 'r') as f:
                    validation_data = json.load(f)
                
                # Find the specific test case
                advanced_result = None
                basic_result = None
                
                for result in validation_data.get("advanced_pipeline", []):
                    if result.get("test_id") == test_id:
                        advanced_result = result
                        break
                
                for result in validation_data.get("basic_pipeline", []):
                    if result.get("test_id") == test_id:
                        basic_result = result
                        break
                
                if not advanced_result:
                    raise HTTPException(status_code=404, detail="Test case not found")
                
                # Load existing expert review if available
                expert_review_file = self.expert_reviews_dir / f"{filename}_{test_id}.json"
                existing_review = {}
                if expert_review_file.exists():
                    with open(expert_review_file, 'r') as f:
                        existing_review = json.load(f)
                
                return self.templates.TemplateResponse("question_review.html", {
                    "request": request,
                    "filename": filename,
                    "test_id": test_id,
                    "advanced_result": advanced_result,
                    "basic_result": basic_result,
                    "existing_review": existing_review
                })
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error loading question data: {e}")
                raise HTTPException(status_code=500, detail="Error loading question data")
        
        @self.app.post("/review/{filename}/question/{test_id}/submit")
        async def submit_expert_review(
            request: Request,
            filename: str,
            test_id: str,
            theological_accuracy: int = Form(...),
            hermeneutical_soundness: int = Form(...),
            biblical_fidelity: int = Form(...),
            clarity_and_precision: int = Form(...),
            practical_application: int = Form(...),
            overall_assessment: int = Form(...),
            detailed_feedback: str = Form(...),
            improvement_suggestions: str = Form(""),
            theological_concerns: str = Form("")
        ):
            """Submit expert evaluation scores"""
            
            try:
                # Parse multi-line inputs
                improvement_list = [s.strip() for s in improvement_suggestions.split('\n') if s.strip()]
                concerns_list = [s.strip() for s in theological_concerns.split('\n') if s.strip()]
                
                expert_review = {
                    "test_id": test_id,
                    "filename": filename,
                    "review_timestamp": datetime.now().isoformat(),
                    "scores": {
                        "theological_accuracy": theological_accuracy,
                        "hermeneutical_soundness": hermeneutical_soundness,
                        "biblical_fidelity": biblical_fidelity,
                        "clarity_and_precision": clarity_and_precision,
                        "practical_application": practical_application,
                        "overall_assessment": overall_assessment,
                        "average_score": (theological_accuracy + hermeneutical_soundness + 
                                        biblical_fidelity + clarity_and_precision + 
                                        practical_application + overall_assessment) / 6
                    },
                    "feedback": {
                        "detailed_feedback": detailed_feedback,
                        "improvement_suggestions": improvement_list,
                        "theological_concerns": concerns_list
                    }
                }
                
                # Save expert review
                review_file = self.expert_reviews_dir / f"{filename}_{test_id}.json"
                with open(review_file, 'w') as f:
                    json.dump(expert_review, f, indent=2)
                
                logger.info(f"Expert review saved for {test_id}: Average score {expert_review['scores']['average_score']:.1f}")
                
                return RedirectResponse(
                    url=f"/review/{filename}?submitted={test_id}",
                    status_code=303
                )
                
            except Exception as e:
                logger.error(f"Error saving expert review: {e}")
                raise HTTPException(status_code=500, detail="Error saving expert review")
        
        @self.app.get("/summary/{filename}", response_class=HTMLResponse)
        async def expert_summary(request: Request, filename: str):
            """Summary of all expert reviews for a validation session"""
            
            try:
                # Load all expert reviews for this session
                review_files = list(self.expert_reviews_dir.glob(f"{filename}_*.json"))
                expert_reviews = []
                
                for review_file in review_files:
                    with open(review_file, 'r') as f:
                        review_data = json.load(f)
                    expert_reviews.append(review_data)
                
                # Calculate summary statistics
                if expert_reviews:
                    all_scores = [review["scores"]["average_score"] for review in expert_reviews]
                    summary_stats = {
                        "total_reviews": len(expert_reviews),
                        "average_expert_score": sum(all_scores) / len(all_scores),
                        "min_score": min(all_scores),
                        "max_score": max(all_scores),
                        "passing_threshold": 8.0,
                        "passing_count": sum(1 for score in all_scores if score >= 8.0),
                        "passing_rate": sum(1 for score in all_scores if score >= 8.0) / len(all_scores) * 100
                    }
                else:
                    summary_stats = {
                        "total_reviews": 0,
                        "average_expert_score": 0,
                        "passing_rate": 0
                    }
                
                return self.templates.TemplateResponse("expert_summary.html", {
                    "request": request,
                    "filename": filename,
                    "expert_reviews": expert_reviews,
                    "summary_stats": summary_stats
                })
                
            except Exception as e:
                logger.error(f"Error generating expert summary: {e}")
                raise HTTPException(status_code=500, detail="Error generating summary")

    def create_templates(self):
        """Create HTML templates for the dashboard"""
        templates_dir = Path(__file__).parent / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # Main dashboard template
        dashboard_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Hermeneutics Expert Review Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .session { border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 5px; }
        .stats { background: #f5f5f5; padding: 10px; border-radius: 3px; margin: 10px 0; }
        .button { background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; }
        .button:hover { background: #005a87; }
    </style>
</head>
<body>
    <h1>Hermeneutics Expert Review Dashboard</h1>
    <p>Review and evaluate validation results from the advanced RAG pipeline.</p>
    
    {% for session in validation_sessions %}
    <div class="session">
        <h3>Validation Session: {{ session.start_time }}</h3>
        <div class="stats">
            <p><strong>Dataset Size:</strong> {{ session.dataset_size }} questions</p>
            <p><strong>Accuracy Improvement:</strong> {{ "%.1f"|format(session.accuracy_improvement) }}%</p>
            <p><strong>Results:</strong> {{ session.advanced_count }} advanced, {{ session.basic_count }} basic</p>
        </div>
        <a href="/review/{{ session.filename }}" class="button">Review Session</a>
        <a href="/summary/{{ session.filename }}" class="button">Expert Summary</a>
    </div>
    {% endfor %}
    
    {% if not validation_sessions %}
    <p>No validation sessions found. Run the validation script first.</p>
    {% endif %}
</body>
</html>'''
        
        with open(templates_dir / "dashboard.html", 'w') as f:
            f.write(dashboard_html)
        
        # Question review template  
        question_review_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Expert Review: {{ test_id }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; max-width: 1200px; }
        .comparison { display: flex; gap: 20px; }
        .response-box { border: 1px solid #ddd; padding: 20px; flex: 1; border-radius: 5px; }
        .advanced { border-color: #28a745; }
        .basic { border-color: #6c757d; }
        .scores { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 3px; }
        .form-group { margin: 15px 0; }
        .form-group label { display: block; font-weight: bold; margin-bottom: 5px; }
        .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }
        .form-group textarea { height: 100px; }
        .submit-btn { background: #28a745; color: white; padding: 12px 24px; border: none; border-radius: 3px; font-size: 16px; }
        .submit-btn:hover { background: #218838; }
        .back-link { color: #007cba; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <a href="/review/{{ filename }}" class="back-link">← Back to Session</a>
    
    <h1>Expert Review: {{ test_id }}</h1>
    
    <div style="background: #e9ecef; padding: 20px; margin: 20px 0; border-radius: 5px;">
        <h3>Question:</h3>
        <p>{{ advanced_result.question }}</p>
        
        <h3>Reference Answer:</h3>
        <p>{{ advanced_result.reference_answer }}</p>
        
        <h3>Evaluation Criteria:</h3>
        <ul>
        {% for criterion in advanced_result.evaluation_criteria %}
            <li>{{ criterion }}</li>
        {% endfor %}
        </ul>
    </div>
    
    <div class="comparison">
        <div class="response-box advanced">
            <h3>Advanced Pipeline Response</h3>
            <p>{{ advanced_result.response }}</p>
            <div class="scores">
                <p><strong>Confidence:</strong> {{ "%.1f"|format(advanced_result.metadata.confidence * 100) }}%</p>
                <p><strong>Execution Time:</strong> {{ "%.2f"|format(advanced_result.execution_time) }}s</p>
                {% if advanced_result.scores %}
                <p><strong>Automated Score:</strong> {{ "%.1f"|format(advanced_result.scores.composite_score) }}/100</p>
                {% endif %}
            </div>
        </div>
        
        {% if basic_result %}
        <div class="response-box basic">
            <h3>Basic Pipeline Response</h3>
            <p>{{ basic_result.response }}</p>
            <div class="scores">
                <p><strong>Confidence:</strong> {{ "%.1f"|format(basic_result.metadata.confidence * 100) }}%</p>
                <p><strong>Execution Time:</strong> {{ "%.2f"|format(basic_result.execution_time) }}s</p>
                {% if basic_result.scores %}
                <p><strong>Automated Score:</strong> {{ "%.1f"|format(basic_result.scores.composite_score) }}/100</p>
                {% endif %}
            </div>
        </div>
        {% endif %}
    </div>
    
    <h2>Expert Evaluation</h2>
    <form method="post" action="/review/{{ filename }}/question/{{ test_id }}/submit">
        <div class="form-group">
            <label>Theological Accuracy (1-10):</label>
            <select name="theological_accuracy" required>
                <option value="">Select Score</option>
                {% for i in range(1, 11) %}
                <option value="{{ i }}" {% if existing_review.scores and existing_review.scores.theological_accuracy == i %}selected{% endif %}>{{ i }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label>Hermeneutical Soundness (1-10):</label>
            <select name="hermeneutical_soundness" required>
                <option value="">Select Score</option>
                {% for i in range(1, 11) %}
                <option value="{{ i }}" {% if existing_review.scores and existing_review.scores.hermeneutical_soundness == i %}selected{% endif %}>{{ i }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label>Biblical Fidelity (1-10):</label>
            <select name="biblical_fidelity" required>
                <option value="">Select Score</option>
                {% for i in range(1, 11) %}
                <option value="{{ i }}" {% if existing_review.scores and existing_review.scores.biblical_fidelity == i %}selected{% endif %}>{{ i }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label>Clarity and Precision (1-10):</label>
            <select name="clarity_and_precision" required>
                <option value="">Select Score</option>
                {% for i in range(1, 11) %}
                <option value="{{ i }}" {% if existing_review.scores and existing_review.scores.clarity_and_precision == i %}selected{% endif %}>{{ i }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label>Practical Application (1-10):</label>
            <select name="practical_application" required>
                <option value="">Select Score</option>
                {% for i in range(1, 11) %}
                <option value="{{ i }}" {% if existing_review.scores and existing_review.scores.practical_application == i %}selected{% endif %}>{{ i }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label>Overall Assessment (1-10):</label>
            <select name="overall_assessment" required>
                <option value="">Select Score</option>
                {% for i in range(1, 11) %}
                <option value="{{ i }}" {% if existing_review.scores and existing_review.scores.overall_assessment == i %}selected{% endif %}>{{ i }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label>Detailed Feedback:</label>
            <textarea name="detailed_feedback" required placeholder="Provide detailed commentary on the theological accuracy, hermeneutical approach, and overall quality...">{{ existing_review.feedback.detailed_feedback if existing_review.feedback else '' }}</textarea>
        </div>
        
        <div class="form-group">
            <label>Improvement Suggestions (one per line):</label>
            <textarea name="improvement_suggestions" placeholder="List specific suggestions for improvement...">{% if existing_review.feedback and existing_review.feedback.improvement_suggestions %}{% for suggestion in existing_review.feedback.improvement_suggestions %}{{ suggestion }}
{% endfor %}{% endif %}</textarea>
        </div>
        
        <div class="form-group">
            <label>Theological Concerns (one per line):</label>
            <textarea name="theological_concerns" placeholder="List any doctrinal or theological concerns...">{% if existing_review.feedback and existing_review.feedback.theological_concerns %}{% for concern in existing_review.feedback.theological_concerns %}{{ concern }}
{% endfor %}{% endif %}</textarea>
        </div>
        
        <button type="submit" class="submit-btn">Submit Expert Review</button>
    </form>
</body>
</html>'''
        
        with open(templates_dir / "question_review.html", 'w') as f:
            f.write(question_review_html)
        
        logger.info(f"Templates created in {templates_dir}")

    def run(self, host: str = "127.0.0.1", port: int = 8001):
        """Run the expert review dashboard"""
        self.create_templates()
        logger.info(f"Starting expert review dashboard at http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


def main():
    """Main entry point for expert review dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Expert Review Dashboard for Hermeneutics Validation")
    parser.add_argument(
        "--results-dir",
        default="validation_results",
        help="Directory containing validation results"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to run the dashboard on"
    )
    
    args = parser.parse_args()
    
    dashboard = ExpertReviewDashboard(args.results_dir)
    dashboard.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()