"""
Enhanced GEval Evaluator Agent - Evaluates agent outputs using DeepEval with Ollama
Consumes from 'final' topic and evaluates the complete pipeline
Uses Ollama (llama3.2 or other local models) as the judge
"""
import json
import os
from datetime import datetime
from kafka import KafkaConsumer
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.models import DeepEvalBaseLLM
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')


class OllamaModel(DeepEvalBaseLLM):
    """Custom Ollama wrapper for DeepEval"""
    
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.base_url = OLLAMA_BASE_URL
    
    def load_model(self):
        """Model loading handled by Ollama server"""
        return self
    
    def generate(self, prompt: str) -> str:
        """Generate response using Ollama API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            print(f"⚠️ Ollama generation error: {e}")
            return f"Error: {str(e)}"
    
    async def a_generate(self, prompt: str) -> str:
        """Async generation (fallback to sync)"""
        return self.generate(prompt)
    
    def get_model_name(self) -> str:
        """Return model identifier"""
        return f"ollama-{self.model_name}"


class AgentEvaluator:
    """Evaluates the quality of agent outputs using GEval with Ollama"""
    
    def __init__(self, use_ollama=True):
        """
        Initialize evaluator with either Ollama or OpenAI
        Args:
            use_ollama: If True, use Ollama; if False, use OpenAI
        """
        self.use_ollama = use_ollama
        
        if use_ollama:
            print(f"🤖 Initializing with Ollama model: {OLLAMA_MODEL}")
            self.model = OllamaModel(model_name=OLLAMA_MODEL)
            # Test Ollama connection
            self._test_ollama_connection()
        else:
            print("🤖 Initializing with OpenAI model: gpt-4o-mini")
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            os.environ['OPENAI_API_KEY'] = api_key
            self.model = "gpt-4o-mini"
        
        self.setup_metrics()
    
    def _test_ollama_connection(self):
        """Test if Ollama is running and model is available"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if OLLAMA_MODEL not in model_names and f"{OLLAMA_MODEL}:latest" not in model_names:
                print(f"⚠️ Warning: Model {OLLAMA_MODEL} not found in Ollama")
                print(f"Available models: {model_names}")
                print(f"\nTo download: ollama pull {OLLAMA_MODEL}")
            else:
                print(f"✅ Ollama connection successful, model {OLLAMA_MODEL} available")
        except Exception as e:
            print(f"⚠️ Warning: Cannot connect to Ollama: {e}")
            print("Make sure Ollama is running: ollama serve")
    
    def setup_metrics(self):
        """Setup GEval metrics for different aspects"""
        
        # Metric 1: Plan Quality - Evaluates the Planner's output
        self.plan_quality_metric = GEval(
            name="Plan Quality",
            criteria="""Evaluate the quality and completeness of the planning steps. 
            A good plan should be:
            1. Clear and well-structured
            2. Actionable and specific
            3. Comprehensive enough to guide answer creation
            4. Relevant to the question asked
            
            Score from 0 to 1, where 1 is excellent planning.""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT
            ],
            model=self.model,
            threshold=0.5
        )
        
        # Metric 2: Draft Helpfulness - Evaluates the Writer's draft
        self.helpfulness_metric = GEval(
            name="Draft Helpfulness",
            criteria="""Evaluate how helpful and informative the draft answer is.
            A helpful answer should:
            1. Be accurate and factually correct
            2. Be comprehensive yet concise
            3. Be well-structured and easy to understand
            4. Directly address the question
            5. Provide examples or explanations where appropriate
            
            Score from 0 to 1, where 1 is exceptionally helpful.""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT
            ],
            model=self.model,
            threshold=0.5
        )
        
        # Metric 3: Final Answer Quality - Evaluates the Reviewer's final output
        self.final_quality_metric = GEval(
            name="Final Answer Quality",
            criteria="""Evaluate the overall quality of the final answer.
            Consider:
            1. Accuracy and correctness
            2. Clarity and readability
            3. Completeness and thoroughness
            4. Professional presentation
            5. Appropriate length and detail
            
            Score from 0 to 1, where 1 is publication-ready quality.""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT
            ],
            model=self.model,
            threshold=0.5
        )
        
        # Metric 4: Improvement Assessment - Compares draft vs final
        self.improvement_metric = GEval(
            name="Draft-to-Final Improvement",
            criteria="""Evaluate whether the final answer is an improvement over the draft.
            Consider if the reviewer added value through:
            1. Better clarity and organization
            2. Improved accuracy or additional details
            3. Better structure or formatting
            4. Removal of errors or unclear statements
            5. Enhanced professionalism
            
            Score from 0 to 1, where 1 means significant improvement and 0.5 means no change.""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.EXPECTED_OUTPUT
            ],
            model=self.model,
            threshold=0.5
        )
    
    def evaluate_plan(self, question, plan):
        """Evaluate the Planner's plan quality"""
        print("\n" + "="*80)
        print("📊 EVALUATING: Plan Quality")
        print("="*80)
        
        # Convert plan to readable format
        if isinstance(plan, dict):
            if 'plan' in plan:
                plan_text = "Plan Steps:\n" + "\n".join(plan['plan'])
            elif 'steps' in plan:
                plan_text = f"Approach: {plan.get('approach', 'N/A')}\n"
                plan_text += "Steps:\n" + "\n".join(plan['steps'])
            else:
                plan_text = json.dumps(plan, indent=2)
        else:
            plan_text = str(plan)
        
        test_case = LLMTestCase(
            input=question,
            actual_output=plan_text
        )
        
        print("⏳ Measuring plan quality...")
        self.plan_quality_metric.measure(test_case)
        
        print(f"✓ Plan Quality Score: {self.plan_quality_metric.score:.2f}/1.0")
        print(f"  Reason: {self.plan_quality_metric.reason}")
        
        return {
            "metric": "Plan Quality",
            "score": self.plan_quality_metric.score,
            "reason": self.plan_quality_metric.reason,
            "passed": self.plan_quality_metric.is_successful()
        }
    
    def evaluate_draft(self, question, draft_answer):
        """Evaluate the Writer's draft for helpfulness"""
        print("\n" + "="*80)
        print("📊 EVALUATING: Draft Helpfulness")
        print("="*80)
        
        test_case = LLMTestCase(
            input=question,
            actual_output=draft_answer
        )
        
        print("⏳ Measuring draft helpfulness...")
        self.helpfulness_metric.measure(test_case)
        
        print(f"✓ Helpfulness Score: {self.helpfulness_metric.score:.2f}/1.0")
        print(f"  Reason: {self.helpfulness_metric.reason}")
        
        return {
            "metric": "Helpfulness",
            "score": self.helpfulness_metric.score,
            "reason": self.helpfulness_metric.reason,
            "passed": self.helpfulness_metric.is_successful()
        }
    
    def evaluate_final(self, question, final_answer):
        """Evaluate the Reviewer's final answer quality"""
        print("\n" + "="*80)
        print("📊 EVALUATING: Final Answer Quality")
        print("="*80)
        
        test_case = LLMTestCase(
            input=question,
            actual_output=final_answer
        )
        
        print("⏳ Measuring final answer quality...")
        self.final_quality_metric.measure(test_case)
        
        print(f"✓ Final Answer Quality Score: {self.final_quality_metric.score:.2f}/1.0")
        print(f"  Reason: {self.final_quality_metric.reason}")
        
        return {
            "metric": "Final Answer Quality",
            "score": self.final_quality_metric.score,
            "reason": self.final_quality_metric.reason,
            "passed": self.final_quality_metric.is_successful()
        }
    
    def evaluate_improvement(self, question, draft_answer, final_answer):
        """Evaluate improvement from draft to final"""
        print("\n" + "="*80)
        print("📊 EVALUATING: Draft-to-Final Improvement")
        print("="*80)
        
        test_case = LLMTestCase(
            input=question,
            actual_output=final_answer,
            expected_output=draft_answer  # Use draft as baseline
        )
        
        print("⏳ Measuring improvement...")
        self.improvement_metric.measure(test_case)
        
        print(f"✓ Improvement Score: {self.improvement_metric.score:.2f}/1.0")
        print(f"  Reason: {self.improvement_metric.reason}")
        
        return {
            "metric": "Draft-to-Final Improvement",
            "score": self.improvement_metric.score,
            "reason": self.improvement_metric.reason,
            "passed": self.improvement_metric.is_successful()
        }
    
    def evaluate_complete_pipeline(self, message_data):
        """Evaluate the complete agent pipeline"""
        question = message_data.get('question', '')
        plan = message_data.get('plan', {})
        draft_answer = message_data.get('draft_answer', message_data.get('answer', ''))
        final_answer = message_data.get('answer', '')
        
        print("\n" + "="*80)
        print("🔍 COMPLETE PIPELINE EVALUATION")
        print("="*80)
        print(f"\n❓ Question: {question}")
        print(f"\n📋 Plan Preview: {str(plan)[:100]}...")
        print(f"\n✏️  Draft Preview: {draft_answer[:100]}...")
        print(f"\n✅ Final Preview: {final_answer[:100]}...")
        
        results = {}
        
        # Evaluate each component
        try:
            results['plan_quality'] = self.evaluate_plan(question, plan)
            results['draft_helpfulness'] = self.evaluate_draft(question, draft_answer)
            results['final_quality'] = self.evaluate_final(question, final_answer)
            results['improvement'] = self.evaluate_improvement(question, draft_answer, final_answer)
            
            # Calculate overall statistics
            scores = [
                results['plan_quality']['score'],
                results['draft_helpfulness']['score'],
                results['final_quality']['score'],
                results['improvement']['score']
            ]
            
            results['overall'] = {
                'average_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'all_passed': all(r['passed'] for r in results.values() if isinstance(r, dict) and 'passed' in r)
            }
            
            self.print_summary(results)
            
        except Exception as e:
            print(f"\n❌ Error during evaluation: {e}")
            import traceback
            traceback.print_exc()
            results['error'] = str(e)
        
        return results
    
    def print_summary(self, results):
        """Print evaluation summary"""
        print("\n" + "="*80)
        print("📊 EVALUATION SUMMARY")
        print("="*80)
        
        print("\n📈 Individual Scores:")
        print(f"  1. Plan Quality:           {results['plan_quality']['score']:.2f} {'✓' if results['plan_quality']['passed'] else '✗'}")
        print(f"  2. Draft Helpfulness:      {results['draft_helpfulness']['score']:.2f} {'✓' if results['draft_helpfulness']['passed'] else '✗'}")
        print(f"  3. Final Answer Quality:   {results['final_quality']['score']:.2f} {'✓' if results['final_quality']['passed'] else '✗'}")
        print(f"  4. Draft-to-Final Improve: {results['improvement']['score']:.2f} {'✓' if results['improvement']['passed'] else '✗'}")
        
        print("\n📊 Overall Statistics:")
        overall = results['overall']
        print(f"  Average Score:  {overall['average_score']:.2f}/1.0")
        print(f"  Min Score:      {overall['min_score']:.2f}/1.0")
        print(f"  Max Score:      {overall['max_score']:.2f}/1.0")
        print(f"  All Passed:     {'✓ YES' if overall['all_passed'] else '✗ NO'}")
        
        print("\n" + "="*80)


def main():
    """Main evaluation loop"""
    print("="*80)
    print("🔍 GEVAL EVALUATOR AGENT - Starting...")
    print("="*80)
    
    # Determine which model to use
    use_ollama = os.getenv('USE_OLLAMA', 'true').lower() == 'true'
    
    # Initialize evaluator
    print(f"\n🔧 Initializing GEval metrics with {'Ollama' if use_ollama else 'OpenAI'}...")
    try:
        evaluator = AgentEvaluator(use_ollama=use_ollama)
        print("✓ GEval evaluator ready")
    except Exception as e:
        print(f"❌ Failed to initialize evaluator: {e}")
        return
    
    # Consumer: reads from final topic
    print(f"\n📥 Connecting to Kafka 'final' topic...")
    consumer = KafkaConsumer(
        'final',
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='evaluator-group'
    )
    
    print("✓ Evaluator is ready and listening on 'final' topic")
    print("⏳ Waiting for completed answers to evaluate...\n")
    
    evaluation_results = []
    
    try:
        for message in consumer:
            final_data = message.value
            request_id = final_data.get('id', 'unknown')
            
            print(f"\n{'='*80}")
            print(f"📨 RECEIVED FINAL ANSWER: {request_id}")
            print(f"{'='*80}")
            
            # Evaluate the complete pipeline
            results = evaluator.evaluate_complete_pipeline(final_data)
            
            # Store results
            results['id'] = request_id
            results['timestamp'] = datetime.now().isoformat()
            results['model_used'] = evaluator.model.get_model_name() if use_ollama else "gpt-4o-mini"
            evaluation_results.append(results)
            
            # Save results to file
            output_file = f"evaluation_results_{request_id}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Results saved to: {output_file}")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Evaluator stopped by user")
    finally:
        consumer.close()
        print("\n✓ Evaluator shutdown complete")
        
        if evaluation_results:
            print(f"\n📊 Total evaluations completed: {len(evaluation_results)}")


if __name__ == "__main__":
    main()