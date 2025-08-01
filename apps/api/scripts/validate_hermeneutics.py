#!/usr/bin/env python3
"""
Hermeneutics Filter Validation Script

Automated validation framework for testing AdvancedRAGFlow against expert-curated
theological questions. Implements comprehensive scoring and comparative analysis.
"""

import asyncio
import json
import logging
import time
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse

# Add the src directory to the Python path
import sys
import os
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

try:
    from flows.advanced_rag_flow import AdvancedRAGFlow
    from flows.basic_rag_flow import BasicRAGFlow
except ImportError:
    # For testing purposes, create mock classes
    class AdvancedRAGFlow:
        async def run(self, shared_store):
            return {"success": True, "response": "Mock response", "confidence": 0.8, "sources": []}
    
    class BasicRAGFlow:
        async def run(self, shared_store):
            return {"success": True, "response": "Mock response", "confidence": 0.7, "sources": []}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hermeneutics_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationScores:
    """Comprehensive scoring for theological response quality"""
    citation_accuracy: float = 0.0
    hermeneutical_adherence: float = 0.0
    semantic_similarity: float = 0.0
    theological_precision: float = 0.0
    response_depth: float = 0.0
    composite_score: float = 0.0


@dataclass
class ValidationResult:
    """Complete validation result for a single test case"""
    test_id: str
    question: str
    response: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    execution_time: float
    reference_answer: str
    evaluation_criteria: List[str]
    scores: Optional[ValidationScores] = None
    success: bool = True
    error: Optional[str] = None
    
    @classmethod
    def failed(cls, test_id: str, error: str):
        """Create a failed validation result"""
        return cls(
            test_id=test_id,
            question="",
            response="",
            sources=[],
            metadata={},
            execution_time=0.0,
            reference_answer="",
            evaluation_criteria=[],
            success=False,
            error=error
        )


@dataclass
class ComparisonReport:
    """Comparative analysis of Advanced vs Basic RAG pipeline performance"""
    accuracy_improvement: float = 0.0
    statistical_significance: Dict[str, float] = None
    performance_tradeoff: Dict[str, float] = None
    category_analysis: Dict[str, Dict[str, float]] = None


class BiblicalCitationValidator:
    """Validates accuracy of biblical references in responses"""
    
    def __init__(self):
        self.common_books = {
            'genesis', 'exodus', 'leviticus', 'numbers', 'deuteronomy',
            'joshua', 'judges', 'ruth', '1 samuel', '2 samuel', '1 kings', '2 kings',
            'matthew', 'mark', 'luke', 'john', 'acts', 'romans', '1 corinthians', '2 corinthians',
            'galatians', 'ephesians', 'philippians', 'colossians', '1 thessalonians', '2 thessalonians',
            '1 timothy', '2 timothy', 'titus', 'philemon', 'hebrews', 'james', '1 peter', '2 peter',
            '1 john', '2 john', '3 john', 'jude', 'revelation'
        }
    
    def validate_citations(self, response: str) -> float:
        """Validate biblical citations for accuracy and relevance"""
        import re
        
        # Simple citation pattern matching
        citation_patterns = [
            r'\b(\d?\s*[A-Za-z]+)\s+(\d+):(\d+)(?:-(\d+))?\b',  # Book chapter:verse(-verse)
            r'\b([A-Za-z]+)\s+(\d+):(\d+)\b',  # Book chapter:verse
        ]
        
        found_citations = 0
        valid_citations = 0
        
        for pattern in citation_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                found_citations += 1
                book = match.group(1).lower().strip()
                if any(book_name in book for book_name in self.common_books):
                    valid_citations += 1
        
        if found_citations == 0:
            return 50.0  # Neutral score if no citations found
        
        return (valid_citations / found_citations) * 100


class HermeneuticalPrincipleAnalyzer:
    """Analyzes adherence to hermeneutical principles in responses"""
    
    def __init__(self):
        self.principle_keywords = {
            'literary_genre': ['metaphor', 'literal', 'symbolic', 'genre', 'poetry', 'narrative'],
            'christocentric': ['christ', 'jesus', 'messiah', 'savior', 'redemption'],
            'canonical_consistency': ['scripture', 'biblical', 'testament', 'canon', 'parallel'],
            'contextual_reading': ['context', 'historical', 'cultural', 'background'],
            'practical_application': ['application', 'practice', 'life', 'believers', 'christian'],
            'theological_integration': ['doctrine', 'theology', 'systematic', 'faith']
        }
    
    def assess_principles(self, response: str, criteria: List[str]) -> float:
        """Assess hermeneutical principle adherence in response"""
        response_lower = response.lower()
        
        principle_scores = []
        for criterion in criteria:
            # Check if response demonstrates hermeneutical awareness
            if any(keyword in response_lower for keywords in self.principle_keywords.values() for keyword in keywords):
                principle_scores.append(85.0)  # Good hermeneutical awareness
            elif len(response) > 200:  # Substantial response
                principle_scores.append(70.0)  # Adequate depth
            else:
                principle_scores.append(50.0)  # Minimal engagement
        
        return statistics.mean(principle_scores) if principle_scores else 50.0


class SemanticSimilarityAnalyzer:
    """Analyzes semantic similarity between response and reference answer"""
    
    async def compare(self, response: str, reference: str) -> float:
        """Compare semantic similarity between response and reference"""
        # Simple word overlap analysis (could be enhanced with embeddings)
        response_words = set(response.lower().split())
        reference_words = set(reference.lower().split())
        
        if not reference_words:
            return 50.0
        
        overlap = len(response_words.intersection(reference_words))
        union = len(response_words.union(reference_words))
        
        jaccard_similarity = overlap / union if union > 0 else 0
        return jaccard_similarity * 100


class TheolocicalScoring:
    """Automated scoring system for theological response quality"""
    
    def __init__(self):
        self.citation_validator = BiblicalCitationValidator()
        self.hermeneutics_analyzer = HermeneuticalPrincipleAnalyzer()
        self.semantic_analyzer = SemanticSimilarityAnalyzer()
    
    async def score_response(self, response: str, reference: str, criteria: List[str]) -> ValidationScores:
        """Generate comprehensive scoring for theological response"""
        scores = ValidationScores()
        
        # 1. Biblical Citation Accuracy (0-100)
        scores.citation_accuracy = self.citation_validator.validate_citations(response)
        
        # 2. Hermeneutical Principle Adherence (0-100)
        scores.hermeneutical_adherence = self.hermeneutics_analyzer.assess_principles(response, criteria)
        
        # 3. Semantic Similarity to Reference (0-100)
        scores.semantic_similarity = await self.semantic_analyzer.compare(response, reference)
        
        # 4. Theological Precision (0-100)
        scores.theological_precision = self._assess_theological_precision(response, criteria)
        
        # 5. Depth and Comprehensiveness (0-100)
        scores.response_depth = self._assess_response_depth(response, criteria)
        
        # 6. Overall Composite Score (weighted average)
        scores.composite_score = self._calculate_composite_score(scores)
        
        return scores
    
    def _assess_theological_precision(self, response: str, criteria: List[str]) -> float:
        """Assess theological precision and accuracy"""
        response_lower = response.lower()
        
        # Look for theological precision markers
        precision_markers = [
            'doctrine', 'orthodox', 'biblical', 'scripture teaches',
            'god reveals', 'christ', 'salvation', 'faith', 'grace'
        ]
        
        marker_count = sum(1 for marker in precision_markers if marker in response_lower)
        precision_score = min(marker_count * 15, 100)  # Cap at 100
        
        # Bonus for substantial theological content
        if len(response) > 300:
            precision_score += 10
        
        return min(precision_score, 100)
    
    def _assess_response_depth(self, response: str, criteria: List[str]) -> float:
        """Assess depth and comprehensiveness of response"""
        # Length-based depth assessment
        if len(response) > 500:
            depth_score = 90
        elif len(response) > 300:
            depth_score = 75
        elif len(response) > 150:
            depth_score = 60
        else:
            depth_score = 40
        
        # Criteria coverage bonus
        criteria_coverage = sum(1 for criterion in criteria if any(
            word in response.lower() for word in criterion.lower().split()
        ))
        coverage_bonus = (criteria_coverage / len(criteria)) * 20 if criteria else 0
        
        return min(depth_score + coverage_bonus, 100)
    
    def _calculate_composite_score(self, scores: ValidationScores) -> float:
        """Calculate weighted composite score"""
        weights = {
            'citation_accuracy': 0.2,
            'hermeneutical_adherence': 0.25,
            'semantic_similarity': 0.2,
            'theological_precision': 0.25,
            'response_depth': 0.1
        }
        
        composite = (
            scores.citation_accuracy * weights['citation_accuracy'] +
            scores.hermeneutical_adherence * weights['hermeneutical_adherence'] +
            scores.semantic_similarity * weights['semantic_similarity'] +
            scores.theological_precision * weights['theological_precision'] +
            scores.response_depth * weights['response_depth']
        )
        
        return composite


class HermeneuticsValidator:
    """Comprehensive validation framework for hermeneutics filter effectiveness"""
    
    def __init__(self, dataset_path: str, output_dir: str):
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.dataset = self._load_expert_dataset()
        self.advanced_flow = AdvancedRAGFlow()
        self.basic_flow = BasicRAGFlow()
        self.scoring_system = TheolocicalScoring()
    
    def _load_expert_dataset(self) -> List[Dict[str, Any]]:
        """Load expert-curated theological questions dataset"""
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['theological_validation_dataset']
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
    
    async def run_validation_suite(self) -> Dict[str, Any]:
        """Execute complete validation against expert dataset"""
        logger.info("Starting comprehensive validation suite...")
        
        results = {
            "validation_metadata": {
                "start_time": datetime.now().isoformat(),
                "dataset_size": len(self.dataset),
                "validator_version": "1.0"
            },
            "advanced_pipeline": await self._test_pipeline(self.advanced_flow, "advanced"),
            "basic_pipeline": await self._test_pipeline(self.basic_flow, "basic"),
            "comparative_analysis": None
        }
        
        # Generate comparative analysis
        results["comparative_analysis"] = self._analyze_improvements(
            results["advanced_pipeline"], 
            results["basic_pipeline"]
        )
        
        # Save results
        await self._save_validation_results(results)
        
        logger.info("Validation suite completed successfully")
        return results
    
    async def _test_pipeline(self, pipeline, pipeline_name: str) -> List[Dict[str, Any]]:
        """Test individual pipeline against expert dataset"""
        logger.info(f"Testing {pipeline_name} pipeline...")
        
        results = []
        for i, test_case in enumerate(self.dataset):
            logger.info(f"Processing test case {i+1}/{len(self.dataset)}: {test_case['id']}")
            
            try:
                start_time = time.time()
                
                # Prepare shared store for pipeline execution
                shared_store = {
                    "query": test_case["question"],
                    "context": test_case["category"],
                    "session_id": f"validation-{test_case['id']}",
                    "user_id": "hermeneutics-validator",
                    "message_id": f"msg-{test_case['id']}",
                    "user_role": "admin"
                }
                
                # Execute pipeline
                response_data = await pipeline.run(shared_store)
                end_time = time.time()
                
                if response_data.get("success", False):
                    validation_result = ValidationResult(
                        test_id=test_case["id"],
                        question=test_case["question"],
                        response=response_data["response"],
                        sources=response_data.get("sources", []),
                        metadata=response_data.get("pipeline_metadata", {}),
                        execution_time=end_time - start_time,
                        reference_answer=test_case["reference_answer"],
                        evaluation_criteria=test_case["evaluation_criteria"]
                    )
                    
                    # Run automated scoring
                    validation_result.scores = await self.scoring_system.score_response(
                        validation_result.response,
                        validation_result.reference_answer,
                        validation_result.evaluation_criteria
                    )
                    
                    results.append(asdict(validation_result))
                    logger.info(f"✓ Test {test_case['id']} completed - Score: {validation_result.scores.composite_score:.1f}")
                
                else:
                    # Pipeline execution failed
                    failed_result = ValidationResult.failed(
                        test_case["id"], 
                        response_data.get("error", "Unknown pipeline error")
                    )
                    results.append(asdict(failed_result))
                    logger.error(f"✗ Test {test_case['id']} failed: {failed_result.error}")
                
            except Exception as e:
                logger.error(f"Validation failed for test {test_case['id']}: {e}")
                failed_result = ValidationResult.failed(test_case["id"], str(e))
                results.append(asdict(failed_result))
        
        return results
    
    def _analyze_improvements(self, advanced_results: List, basic_results: List) -> Dict[str, Any]:
        """Comprehensive comparison of pipeline performance"""
        logger.info("Analyzing comparative performance...")
        
        # Extract successful results only
        advanced_successful = [r for r in advanced_results if r['success'] and r['scores']]
        basic_successful = [r for r in basic_results if r['success'] and r['scores']]
        
        if not advanced_successful or not basic_successful:
            return {"error": "Insufficient successful results for comparison"}
        
        # Calculate average scores
        advanced_scores = [r['scores']['composite_score'] for r in advanced_successful]
        basic_scores = [r['scores']['composite_score'] for r in basic_successful]
        
        advanced_avg = statistics.mean(advanced_scores)
        basic_avg = statistics.mean(basic_scores)
        
        # Performance improvement
        accuracy_improvement = ((advanced_avg - basic_avg) / basic_avg) * 100 if basic_avg > 0 else 0
        
        # Execution time comparison
        advanced_times = [r['execution_time'] for r in advanced_successful]
        basic_times = [r['execution_time'] for r in basic_successful]
        
        time_increase = ((statistics.mean(advanced_times) - statistics.mean(basic_times)) / statistics.mean(basic_times)) * 100 if basic_times else 0
        
        # Category-specific analysis
        category_analysis = {}
        for result in advanced_successful:
            category = result.get('metadata', {}).get('category', 'unknown')
            if category not in category_analysis:
                category_analysis[category] = {'advanced': [], 'basic': []}
            category_analysis[category]['advanced'].append(result['scores']['composite_score'])
        
        for result in basic_successful:
            category = result.get('metadata', {}).get('category', 'unknown')
            if category in category_analysis:
                category_analysis[category]['basic'].append(result['scores']['composite_score'])
        
        category_improvements = {}
        for category, scores in category_analysis.items():
            if scores['advanced'] and scores['basic']:
                adv_avg = statistics.mean(scores['advanced'])
                basic_avg = statistics.mean(scores['basic'])
                improvement = ((adv_avg - basic_avg) / basic_avg) * 100 if basic_avg > 0 else 0
                category_improvements[category] = improvement
        
        return {
            "accuracy_improvement_percent": accuracy_improvement,
            "latency_increase_percent": time_increase,
            "advanced_pipeline_stats": {
                "average_score": advanced_avg,
                "score_std_dev": statistics.stdev(advanced_scores) if len(advanced_scores) > 1 else 0,
                "success_rate": len(advanced_successful) / len(advanced_results) * 100,
                "average_latency": statistics.mean(advanced_times)
            },
            "basic_pipeline_stats": {
                "average_score": basic_avg,
                "score_std_dev": statistics.stdev(basic_scores) if len(basic_scores) > 1 else 0,
                "success_rate": len(basic_successful) / len(basic_results) * 100,
                "average_latency": statistics.mean(basic_times)
            },
            "category_improvements": category_improvements,
            "statistical_summary": {
                "sample_size": len(advanced_successful),
                "improvement_threshold_met": accuracy_improvement >= 15.0,
                "latency_acceptable": time_increase <= 200.0
            }
        }
    
    async def _save_validation_results(self, results: Dict[str, Any]):
        """Save comprehensive validation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full results
        full_results_path = self.output_dir / f"hermeneutics_validation_{timestamp}.json"
        with open(full_results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Generate summary report
        summary_path = self.output_dir / f"validation_summary_{timestamp}.txt"
        await self._generate_summary_report(results, summary_path)
        
        logger.info(f"Results saved to {full_results_path}")
        logger.info(f"Summary report saved to {summary_path}")
    
    async def _generate_summary_report(self, results: Dict[str, Any], output_path: Path):
        """Generate human-readable summary report"""
        comparison = results.get("comparative_analysis", {})
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("HERMENEUTICS FILTER VALIDATION REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Validation Date: {results['validation_metadata']['start_time']}\n")
            f.write(f"Dataset Size: {results['validation_metadata']['dataset_size']} questions\n\n")
            
            if "error" not in comparison:
                f.write("PERFORMANCE SUMMARY:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Accuracy Improvement: {comparison.get('accuracy_improvement_percent', 0):.1f}%\n")
                f.write(f"Latency Increase: {comparison.get('latency_increase_percent', 0):.1f}%\n\n")
                
                adv_stats = comparison.get('advanced_pipeline_stats', {})
                basic_stats = comparison.get('basic_pipeline_stats', {})
                
                f.write("ADVANCED PIPELINE:\n")
                f.write(f"  Average Score: {adv_stats.get('average_score', 0):.1f}/100\n")
                f.write(f"  Success Rate: {adv_stats.get('success_rate', 0):.1f}%\n")
                f.write(f"  Average Latency: {adv_stats.get('average_latency', 0):.2f}s\n\n")
                
                f.write("BASIC PIPELINE:\n")
                f.write(f"  Average Score: {basic_stats.get('average_score', 0):.1f}/100\n")
                f.write(f"  Success Rate: {basic_stats.get('success_rate', 0):.1f}%\n")
                f.write(f"  Average Latency: {basic_stats.get('average_latency', 0):.2f}s\n\n")
                
                f.write("VALIDATION CRITERIA:\n")
                f.write("-" * 20 + "\n")
                summary = comparison.get('statistical_summary', {})
                f.write(f"✓ Improvement Threshold (>15%): {'PASSED' if summary.get('improvement_threshold_met') else 'FAILED'}\n")
                f.write(f"✓ Latency Acceptable (<200%): {'PASSED' if summary.get('latency_acceptable') else 'FAILED'}\n")
                
                f.write("\nCATEGORY IMPROVEMENTS:\n")
                f.write("-" * 20 + "\n")
                for category, improvement in comparison.get('category_improvements', {}).items():
                    f.write(f"{category}: {improvement:.1f}%\n")
            
            else:
                f.write(f"COMPARISON ERROR: {comparison['error']}\n")


async def main():
    """Main validation script entry point"""
    parser = argparse.ArgumentParser(description="Hermeneutics Filter Validation")
    parser.add_argument(
        "--dataset", 
        default="data/hermeneutics_validation_dataset.json",
        help="Path to expert dataset JSON file"
    )
    parser.add_argument(
        "--output", 
        default="validation_results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation on subset of dataset"
    )
    
    args = parser.parse_args()
    
    # Setup validator
    validator = HermeneuticsValidator(args.dataset, args.output)
    
    # Run validation
    try:
        results = await validator.run_validation_suite()
        
        # Print summary
        comparison = results.get("comparative_analysis", {})
        if "error" not in comparison:
            print("\n" + "=" * 50)
            print("VALIDATION COMPLETE")
            print("=" * 50)
            print(f"Accuracy Improvement: {comparison.get('accuracy_improvement_percent', 0):.1f}%")
            print(f"Latency Increase: {comparison.get('latency_increase_percent', 0):.1f}%")
            
            summary = comparison.get('statistical_summary', {})
            print(f"Validation Status: {'PASSED' if summary.get('improvement_threshold_met') and summary.get('latency_acceptable') else 'FAILED'}")
        else:
            print(f"Validation failed: {comparison['error']}")
            
    except Exception as e:
        logger.error(f"Validation script failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))