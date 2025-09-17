#!/usr/bin/env python3
"""
Kiểm tra kết nối tới Kafka broker bằng confluent-kafka.
Usage: python check_kafka_confluent.py broker:9092
"""
import sys
from confluent_kafka.admin import AdminClient

def check_kafka(broker, timeout=5.0):
    conf = {'bootstrap.servers': broker}
    client = AdminClient(conf)
    try:
        md = client.list_topics(timeout=timeout)  # metadata
        brokers = [f"{b.id}:{b.host}:{b.port}" for b in md.brokers.values()]
        topics = list(md.topics.keys())
        print(f"✅ Connected to Kafka broker {broker}")
        print("Brokers in cluster:", brokers)
        print("Sample topics (up to 20):", topics[:20])
        return True
    except Exception as e:
        print(f"❌ Không thể kết nối tới {broker}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_kafka_confluent.py broker:9092")
        sys.exit(2)
    broker = sys.argv[1]
    ok = check_kafka(broker)
    sys.exit(0 if ok else 1)