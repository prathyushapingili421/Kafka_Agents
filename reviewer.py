"""
Reviewer Agent (Updated) - Reads drafts and includes draft in final message
Sends approved answers to 'final' topic with draft preserved for evaluation
"""
import json
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime

KAFKA_BOOTSTRAP = 'localhost:9092'

def review_answer(draft):
    """Review the draft answer and approve or suggest improvements"""
    answer = draft.get('answer', '')
    word_count = draft.get('word_count', 0)
    
    # Simple quality checks
    issues = []
    
    if word_count < 20:
        issues.append("Answer seems too short")
    
    if word_count > 300:
        issues.append("Answer might be too long")
    
    if len(answer) < 50:
        issues.append("Answer lacks detail")
    
    if "Error" in answer or "error" in answer:
        issues.append("Answer contains error message")
    
    # Determine approval status
    if len(issues) == 0:
        status = "approved"
        feedback = "Answer meets quality standards. Approved for delivery."
    else:
        status = "approved_with_notes"
        feedback = f"Approved with minor notes: {'; '.join(issues)}"
    
    return status, feedback, issues

def main():
    print("="*60)
    print("🔍 REVIEWER AGENT (UPDATED) - Starting...")
    print("="*60)
    
    # Consumer: reads from drafts
    consumer = KafkaConsumer(
        'drafts',
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='reviewer-group'
    )
    
    # Producer: sends to final
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    print("✓ Reviewer is ready and listening on 'drafts' topic")
    print("📥 Waiting for drafts to review...\n")
    
    try:
        for message in consumer:
            draft = message.value
            request_id = draft.get('id', 'unknown')
            question = draft.get('question', '')
            answer = draft.get('answer', '')
            
            print(f"\n{'─'*60}")
            print(f"📨 RECEIVED from drafts:")
            print(f"   ID: {request_id}")
            print(f"   Question: {question}")
            print(f"   Answer preview: {answer[:80]}...")
            
            # Review the answer
            print(f"\n🔍 Reviewing answer...")
            status, feedback, issues = review_answer(draft)
            
            # Package final result - IMPORTANT: Include draft_answer for GEval
            final_result = {
                "id": request_id,
                "question": question,
                "answer": answer,
                "draft_answer": answer,  # Keep original draft for evaluation
                "status": status,
                "review_feedback": feedback,
                "issues": issues,
                "plan": draft.get('plan', {}),
                "writer_timestamp": draft.get('writer_timestamp'),
                "reviewer_timestamp": datetime.now().isoformat(),
                "word_count": draft.get('word_count', 0)
            }
            
            # Send to final topic
            producer.send('final', value=final_result)
            producer.flush()
            
            print(f"✅ SENT to final:")
            print(f"   Status: {status}")
            print(f"   Feedback: {feedback}")
            if issues:
                print(f"   Issues noted: {len(issues)}")
            print(f"{'─'*60}\n")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Reviewer agent stopped by user")
    finally:
        consumer.close()
        producer.close()
        print("✓ Reviewer agent shutdown complete")

if __name__ == "__main__":
    main()