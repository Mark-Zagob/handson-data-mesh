# consume_safe_decoding.py
from confluent_kafka import Consumer, KafkaError, KafkaException
import json
import sys
import time
import binascii

def safe_decode_message(raw_bytes):
    """Safely decode message with multiple strategies"""
    if raw_bytes is None:
        return None
    
    # Strategy 1: UTF-8
    try:
        return raw_bytes.decode('utf-8')
    except UnicodeDecodeError:
        pass
    
    # Strategy 2: Latin-1 (can decode any byte sequence)
    try:
        decoded = raw_bytes.decode('latin-1')
        # Check if it looks like text
        if decoded.isprintable():
            return decoded
    except:
        pass
    
    # Strategy 3: Try common encodings
    for encoding in ['utf-16', 'utf-32', 'ascii', 'cp1252']:
        try:
            return raw_bytes.decode(encoding)
        except:
            continue
    
    # Strategy 4: Return hex representation for binary data
    return f"[BINARY: {binascii.hexlify(raw_bytes).decode('ascii')}]"

def analyze_message_encoding(raw_bytes):
    """Analyze what type of encoding the message might be"""
    if raw_bytes is None:
        return "NULL"
    
    # Check if it's Avro magic bytes
    if len(raw_bytes) >= 5 and raw_bytes[0] == 0x00:
        return "AVRO_BINARY"
    
    # Check if it starts with common JSON chars
    if raw_bytes.startswith(b'{') or raw_bytes.startswith(b'['):
        return "JSON_LIKE"
    
    # Check if it's mostly printable ASCII
    try:
        decoded = raw_bytes.decode('utf-8')
        if decoded.isprintable():
            return "UTF8_TEXT"
    except:
        pass
    
    # Check for common binary patterns
    if b'\x00' in raw_bytes:
        return "BINARY_WITH_NULL"
    
    return "UNKNOWN"

def consume_all_messages_safe(topic_name):
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': f'temp-consumer-{int(time.time())}',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
        'session.timeout.ms': 30000,
        'max.poll.interval.ms': 300000
    }
    
    consumer = Consumer(conf)
    consumer.subscribe([topic_name])
    
    print(f"🚀 Consuming all messages from topic: {topic_name}")
    
    messages = []
    message_count = 0
    consecutive_empty_polls = 0
    max_empty_polls = 5
    encoding_stats = {}
    
    try:
        while consecutive_empty_polls < max_empty_polls:
            msg = consumer.poll(timeout=2.0)
            
            if msg is None:
                consecutive_empty_polls += 1
                print(f"⏳ Empty poll {consecutive_empty_polls}/{max_empty_polls}")
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"✅ Reached end of partition {msg.partition()}")
                    consecutive_empty_polls += 1
                    continue
                else:
                    raise KafkaException(msg.error())
            
            consecutive_empty_polls = 0
            message_count += 1
            
            # Analyze raw bytes
            raw_key = msg.key()
            raw_value = msg.value()
            
            # Detect encoding type
            encoding_type = analyze_message_encoding(raw_value)
            encoding_stats[encoding_type] = encoding_stats.get(encoding_type, 0) + 1
            
            # Safe decode
            decoded_key = safe_decode_message(raw_key) if raw_key else None
            decoded_value = safe_decode_message(raw_value) if raw_value else None
            
            message_data = {
                'topic': msg.topic(),
                'partition': msg.partition(),
                'offset': msg.offset(),
                'timestamp': msg.timestamp(),
                'encoding_type': encoding_type,
                'key': decoded_key,
                'value': decoded_value,
                'raw_value_length': len(raw_value) if raw_value else 0
            }
            
            messages.append(message_data)
            
            # Display message based on type
            if encoding_type in ['UTF8_TEXT', 'JSON_LIKE']:
                print(f"📝 Message {message_count} ({encoding_type}): {decoded_value}")
            else:
                print(f"🔧 Message {message_count} ({encoding_type}): {decoded_value[:100]}...")
                
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        consumer.close()
    
    # Print statistics
    print(f"\n📊 CONSUMPTION SUMMARY:")
    print(f"Total messages: {message_count}")
    print(f"Encoding distribution:")
    for enc_type, count in encoding_stats.items():
        print(f"  {enc_type}: {count} messages")
        
    return messages, encoding_stats

if __name__ == "__main__":
    topic = 'user-activity'
    all_messages, stats = consume_all_messages_safe(topic)
    
    # Save with encoding info
    output_file = f'{topic}_messages_analyzed.json'
    result = {
        'messages': all_messages,
        'encoding_stats': stats,
        'total_count': len(all_messages)
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Messages saved to {output_file}")
    
    # Show sample of different encoding types
    print(f"\n🔍 SAMPLE MESSAGES BY TYPE:")
    for encoding_type in stats.keys():
        sample_msg = next((msg for msg in all_messages if msg['encoding_type'] == encoding_type), None)
        if sample_msg:
            print(f"\n{encoding_type} example:")
            print(f"  Value: {sample_msg['value'][:200]}...")
            print(f"  Length: {sample_msg['raw_value_length']} bytes")