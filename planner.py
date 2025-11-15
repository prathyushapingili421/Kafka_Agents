"""
Planner Agent - Reads questions from 'inbox' and creates structured plans
Sends plans to 'tasks' topic
"""
from kafka import KafkaConsumer, KafkaProducer
import json
import time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

consumer = KafkaConsumer(
    'inbox',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='latest',
    enable_auto_commit=True,
    group_id='planner-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("🎯 Planner Agent Started")
print("Listening to 'inbox' topic...")
print("-" * 60)

def create_plan(question):
    """Create a detailed, question-specific plan"""
    plan_steps = [
        "1. Identify the core concepts in the question",
        "2. Research and gather relevant technical details",
        "3. Structure the answer with clear examples",
        "4. Explain benefits, use cases, and comparisons",
        "5. Conclude with practical recommendations"
    ]
    
    return {
        "steps": plan_steps,
        "approach": "analytical and comprehensive",
        "context": f"Detailed analysis required for: {question[:50]}...",
        "timestamp": time.time()
    }

try:
    for message in consumer:
        data = message.value
        print(f"\n📨 Received question from inbox:")
        print(f"   Question: {data.get('question', 'N/A')}")
        print(f"   Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        question = data.get('question', '')
        plan = create_plan(question)
        
        print(f"\n📝 Created plan:")
        # Access 'steps' key instead of 'plan'
        for step in plan['steps']:
            print(f"   {step}")
        
        # Create task message with all necessary data
        task_message = {
            "id": data.get('id', 'unknown'),  # Pass through the request ID
            "type": "task",
            "question": question,  # Include question directly
            "original_question": question,  # Also as original_question for compatibility
            "plan": plan,
            "from_agent": "planner",
            "timestamp": time.time()
        }
        
        producer.send('tasks', task_message)
        producer.flush()
        
        print(f"\n✅ Sent plan to 'tasks' topic")
        print("-" * 60)

except KeyboardInterrupt:
    print("\n\n🛑 Planner Agent shutting down...")
finally:
    consumer.close()
    producer.close()
    print("✅ Planner Agent stopped")