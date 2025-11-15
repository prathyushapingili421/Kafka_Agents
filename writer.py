"""
Writer Agent - Reads tasks from 'tasks' topic and writes answers using LangChain
Sends drafts to 'drafts' topic
Updated to use .env file for configuration
"""
import json
import os
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

def write_answer(question, plan):
    """Use LangChain to write an answer"""
    
    # Initialize OpenAI
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return "Error: OPENAI_API_KEY not set in .env file"
    
    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )
    
    # Handle different plan formats from planner.py
    if isinstance(plan, dict):
        if 'plan' in plan:
            # Planner sends: {"plan": [...], "context": ...}
            plan_steps = plan['plan']
        elif 'steps' in plan:
            # Alternative format: {"steps": [...]}
            plan_steps = plan['steps']
        else:
            plan_steps = ["Analyze and answer the question comprehensively"]
    else:
        plan_steps = ["Analyze and answer the question comprehensively"]
    
    # Create system prompt based on plan
    system_prompt = f"""You are a helpful assistant that provides clear, concise answers.
Based on this plan:
{json.dumps(plan_steps, indent=2)}

Provide a well-structured answer to the user's question.
Keep your response under 200 words but make it informative."""
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]
        
        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        return f"Error generating answer: {str(e)}"

def main():
    print("="*60)
    print("✍️  WRITER AGENT - Starting...")
    print("="*60)
    
    # Consumer: reads from tasks
    consumer = KafkaConsumer(
        'tasks',
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='writer-group'
    )
    
    # Producer: sends to drafts
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    print("✓ Writer is ready and listening on 'tasks' topic")
    print(f"✓ Using model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    print("📥 Waiting for tasks...\n")
    
    try:
        for message in consumer:
            task = message.value
            
            # Extract data - handle both formats
            request_id = task.get('id', 'unknown')
            question = task.get('question', task.get('original_question', ''))
            plan = task.get('plan', {})
            
            print(f"\n{'─'*60}")
            print(f"📨 RECEIVED from tasks:")
            print(f"   ID: {request_id}")
            print(f"   Question: {question}")
            
            # Show plan preview
            if isinstance(plan, dict):
                if 'plan' in plan:
                    print(f"   Plan steps: {len(plan['plan'])}")
                elif 'steps' in plan:
                    print(f"   Plan steps: {len(plan['steps'])}")
                if 'context' in plan:
                    print(f"   Context: {plan.get('context', 'N/A')[:50]}...")
            
            # Write the answer using LangChain
            print(f"\n✍️  Writing answer using LangChain...")
            answer = write_answer(question, plan)
            
            # Package draft for reviewer
            draft = {
                "id": request_id,
                "question": question,
                "answer": answer,
                "plan": plan,
                "writer_timestamp": datetime.now().isoformat(),
                "word_count": len(answer.split())
            }
            
            # Send to drafts topic
            producer.send('drafts', value=draft)
            producer.flush()
            
            print(f"✅ SENT to drafts:")
            print(f"   Answer length: {len(answer)} chars")
            print(f"   Word count: {draft['word_count']}")
            print(f"   Preview: {answer[:100]}...")
            print(f"{'─'*60}\n")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Writer agent stopped by user")
    finally:
        consumer.close()
        producer.close()
        print("✓ Writer agent shutdown complete")

if __name__ == "__main__":
    main()