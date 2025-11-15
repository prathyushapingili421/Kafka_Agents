from kafka import KafkaProducer
import json
import time
import sys

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("📮 Question Sender")
print("-" * 60)

default_question = "What is machine learning and how does it work?"

if len(sys.argv) > 1:
    question = " ".join(sys.argv[1:])
else:
    question = default_question
    print(f"ℹ️  No question provided, using default.")

print(f"\n❓ Question to send:")
print(f"   {question}")

message = {
    "type": "question",
    "question": question,
    "sent_at": time.time(),
    "sender": "user"
}

try:
    print(f"\n📤 Sending question to 'inbox' topic...")
    producer.send('inbox', message)
    producer.flush()
    print(f"✅ Question sent successfully!")
    print(f"   Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n💡 The agents will process this question through:")
    print(f"   1. Planner (inbox → tasks)")
    print(f"   2. Writer (tasks → drafts)")
    print(f"   3. Reviewer (drafts → final)")
    print(f"\n📖 To read the final answer, run: python read_final.py")
    print("-" * 60)
except Exception as e:
    print(f"\n❌ Error sending question: {e}")
finally:
    producer.close()
    print("\n✅ Sender closed")
