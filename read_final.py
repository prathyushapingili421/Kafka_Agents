from kafka import KafkaConsumer
import json
import time

consumer = KafkaConsumer(
    'final',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='latest',
    enable_auto_commit=True,
    group_id='final-reader-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    consumer_timeout_ms=10000
)

print("📖 Reading from 'final' topic...")
print("Waiting for messages (will timeout after 10 seconds)...")
print("-" * 60)

message_count = 0

try:
    for message in consumer:
        message_count += 1
        data = message.value
        
        print(f"\n{'=' * 60}")
        print(f"📨 MESSAGE #{message_count}")
        print(f"{'=' * 60}")
        
        print(f"\n📋 Status: {data.get('status', 'N/A').upper()}")
        print(f"\n❓ Original Question:")
        print(f"   {data.get('original_question', 'N/A')}")
        
        print(f"\n📝 Answer:")
        answer = data.get('answer', 'N/A')
        print(f"   {answer}")
        
        if 'review' in data:
            review = data['review']
            print(f"\n🔍 Review Details:")
            print(f"   Approved: {review.get('approved', 'N/A')}")
            if 'feedback' in review:
                print(f"   Feedback:")
                for item in review['feedback']:
                    print(f"      - {item}")
        
        print(f"\n🕐 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('timestamp', time.time())))}")
        print(f"🤖 From Agent: {data.get('from_agent', 'unknown')}")
        
        print(f"\n{'=' * 60}")
        print(f"\n📄 Raw JSON (for screenshot):")
        print(json.dumps(data, indent=2))
        print(f"\n{'=' * 60}\n")

except KeyboardInterrupt:
    print("\n\n🛑 Stopping reader...")
except Exception as e:
    if "timeout" not in str(e).lower():
        print(f"\n❌ Error: {e}")
finally:
    consumer.close()
    
    if message_count == 0:
        print("\n⚠️  No messages received.")
        print("Make sure:")
        print("   1. All agents are running")
        print("   2. You sent a question using send_question.py")
        print("   3. Wait a few seconds for the pipeline to complete")
    else:
        print(f"\n✅ Read {message_count} message(s) from 'final' topic")
    
    print("✅ Reader closed")
