"""
Complete Test Script with Enhanced GEval Evaluation
Sends a question and waits for evaluation results
Supports both Ollama and OpenAI models
"""
import json
import uuid
import time
import os
from kafka import KafkaProducer, KafkaConsumer
from datetime import datetime

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

def send_question(question):
    """Send a question to the inbox topic"""
    request_id = str(uuid.uuid4())[:8]
    
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    message = {
        "id": request_id,
        "question": question,
        "timestamp": datetime.now().isoformat()
    }
    
    print("="*80)
    print("📤 SENDING QUESTION TO AGENT SYSTEM WITH GEVAL EVALUATION")
    print("="*80)
    print(f"\n📋 Request ID: {request_id}")
    print(f"❓ Question: {question}\n")
    
    producer.send('inbox', value=message)
    producer.flush()
    producer.close()
    
    print("✅ Question sent to 'inbox' topic")
    print(f"⏳ Agents processing... (Planner → Writer → Reviewer → Evaluator)\n")
    
    return request_id

def wait_for_evaluation(request_id, timeout=180):
    """Wait for the evaluation results"""
    print("="*80)
    print("⏳ WAITING FOR GEVAL EVALUATION RESULTS")
    print("="*80)
    print(f"Monitoring evaluation files for request: {request_id}\n")
    
    start_time = time.time()
    last_status_time = start_time
    
    while time.time() - start_time < timeout:
        # Check if evaluation file exists
        try:
            filename = f"evaluation_results_{request_id}.json"
            with open(filename, 'r') as f:
                results = json.load(f)
                
            print("\n" + "="*80)
            print("✅ GEVAL EVALUATION COMPLETED!")
            print("="*80)
            
            # Display results
            print(f"\n❓ Question: {results.get('question', 'N/A')[:100]}...")
            print(f"🤖 Model Used: {results.get('model_used', 'N/A')}")
            
            print("\n📊 EVALUATION SCORES:")
            print("─"*80)
            
            # Plan Quality
            if 'plan_quality' in results:
                pq = results['plan_quality']
                status = "✓ PASS" if pq['passed'] else "✗ FAIL"
                print(f"\n1️⃣  PLAN QUALITY: {pq['score']:.3f}/1.0 {status}")
                print(f"    📝 {pq['reason'][:200]}...")
            
            # Draft Helpfulness
            if 'draft_helpfulness' in results:
                dh = results['draft_helpfulness']
                status = "✓ PASS" if dh['passed'] else "✗ FAIL"
                print(f"\n2️⃣  DRAFT HELPFULNESS: {dh['score']:.3f}/1.0 {status}")
                print(f"    📝 {dh['reason'][:200]}...")
            
            # Final Quality
            if 'final_quality' in results:
                fq = results['final_quality']
                status = "✓ PASS" if fq['passed'] else "✗ FAIL"
                print(f"\n3️⃣  FINAL ANSWER QUALITY: {fq['score']:.3f}/1.0 {status}")
                print(f"    📝 {fq['reason'][:200]}...")
            
            # Improvement
            if 'improvement' in results:
                imp = results['improvement']
                status = "✓ PASS" if imp['passed'] else "✗ FAIL"
                print(f"\n4️⃣  DRAFT-TO-FINAL IMPROVEMENT: {imp['score']:.3f}/1.0 {status}")
                print(f"    📝 {imp['reason'][:200]}...")
            
            # Overall Statistics
            if 'overall' in results:
                overall = results['overall']
                print(f"\n{'='*80}")
                print("📈 OVERALL STATISTICS")
                print("="*80)
                print(f"  Average Score:     {overall['average_score']:.3f}/1.0")
                print(f"  Minimum Score:     {overall['min_score']:.3f}/1.0")
                print(f"  Maximum Score:     {overall['max_score']:.3f}/1.0")
                print(f"  All Tests Passed:  {'✅ YES' if overall['all_passed'] else '❌ NO'}")
                
                # Quality Assessment
                avg = overall['average_score']
                if avg >= 0.8:
                    quality = "🌟 EXCELLENT"
                elif avg >= 0.7:
                    quality = "👍 GOOD"
                elif avg >= 0.6:
                    quality = "✓ ACCEPTABLE"
                elif avg >= 0.5:
                    quality = "⚠️ NEEDS IMPROVEMENT"
                else:
                    quality = "❌ POOR"
                print(f"  Quality Rating:    {quality}")
            
            print("\n" + "="*80)
            return results
            
        except FileNotFoundError:
            # File doesn't exist yet, wait
            current_time = time.time()
            elapsed = int(current_time - start_time)
            
            # Print status every 5 seconds
            if current_time - last_status_time >= 5:
                print(f"⏳ Waiting... ({elapsed}s elapsed)")
                last_status_time = current_time
            
            time.sleep(2)
    
    print(f"\n⚠️ Timeout: No evaluation results after {timeout} seconds")
    print("\n🔍 Troubleshooting:")
    print("  1. Ensure all agents are running:")
    print("     Terminal 1: python planner.py")
    print("     Terminal 2: python writer.py")
    print("     Terminal 3: python reviewer.py")
    print("     Terminal 4: python evaluator_enhanced.py")
    print("\n  2. Check Kafka is running:")
    print("     docker ps | grep kafka")
    print("\n  3. For Ollama, ensure it's running:")
    print("     ollama serve")
    print("     ollama list  # Check models")
    return None

def display_instructions():
    """Display setup instructions"""
    print("\n" + "="*80)
    print("🤖 KAFKA MULTI-AGENT SYSTEM WITH GEVAL EVALUATION")
    print("="*80)
    
    print("\n📋 PREREQUISITES:")
    print("  1. Kafka running (docker-compose up -d)")
    print("  2. All agent scripts running in separate terminals")
    print("  3. LLM backend configured (.env file)")
    
    print("\n🔧 CONFIGURATION OPTIONS:")
    print("  • Ollama (default): Set USE_OLLAMA=true in .env")
    print("    - Install: https://ollama.ai")
    print("    - Pull model: ollama pull llama3.2")
    print("    - Start server: ollama serve")
    print("\n  • OpenAI: Set USE_OLLAMA=false in .env")
    print("    - Set OPENAI_API_KEY in .env")
    
    print("\n📊 EVALUATION METRICS:")
    print("  1. Plan Quality (Planner)")
    print("  2. Draft Helpfulness (Writer)")
    print("  3. Final Answer Quality (Reviewer)")
    print("  4. Draft-to-Final Improvement (Comparison)")

def main():
    display_instructions()
    
    # Test questions
    questions = [
        "What are the benefits of using Kafka for microservices?",
        "Explain the concept of event-driven architecture",
        "How does machine learning work in natural language processing?",
        "What is the difference between SQL and NoSQL databases?"
    ]
    
    print("\n" + "="*80)
    print("📝 AVAILABLE TEST QUESTIONS:")
    print("="*80)
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")
    
    # Allow user to select or use first question
    print("\n💡 Using first question for demo...")
    selected_question = questions[0]
    
    print(f"\n🎯 Selected Question:")
    print(f"   {selected_question}")
    
    # Confirm before proceeding
    input("\n⏸️  Press Enter to send question and start evaluation...")
    
    # Send the question
    request_id = send_question(selected_question)
    
    # Wait for agents to process (Planner → Writer → Reviewer)
    print("\n⏳ Waiting for agent pipeline to complete...")
    print("   Stage 1/4: Planner creating plan...")
    time.sleep(3)
    print("   Stage 2/4: Writer drafting answer...")
    time.sleep(5)
    print("   Stage 3/4: Reviewer approving...")
    time.sleep(3)
    print("   Stage 4/4: GEval evaluating...")
    
    # Wait for evaluation
    results = wait_for_evaluation(request_id, timeout=180)
    
    if results:
        print("\n✅ EVALUATION COMPLETED SUCCESSFULLY!")
        print(f"\n💾 Detailed results saved in: evaluation_results_{request_id}.json")
        
        # Provide insights
        if 'overall' in results:
            avg_score = results['overall']['average_score']
            print(f"\n💡 INSIGHTS:")
            if avg_score >= 0.8:
                print("   🌟 Excellent pipeline performance! All agents working well.")
            elif avg_score >= 0.7:
                print("   👍 Good performance with room for optimization.")
            elif avg_score >= 0.6:
                print("   ✓ Acceptable but consider improving lower-scoring stages.")
            else:
                print("   ⚠️ Pipeline needs improvement. Review failing metrics.")
    else:
        print("\n❌ EVALUATION INCOMPLETE")
        print("   Check agent logs for errors")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n🔍 TROUBLESHOOTING GUIDE:")
        print("1. Kafka Issues:")
        print("   docker-compose ps")
        print("   docker-compose logs kafka")
        print("\n2. Agent Issues:")
        print("   Check each agent terminal for error messages")
        print("\n3. LLM Issues:")
        print("   Ollama: curl http://localhost:11434/api/tags")
        print("   OpenAI: Check OPENAI_API_KEY in .env")
        print("\n4. Network Issues:")
        print("   netstat -an | grep 9092  # Kafka")
        print("   netstat -an | grep 11434  # Ollama")