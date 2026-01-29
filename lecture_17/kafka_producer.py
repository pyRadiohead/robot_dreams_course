import time
import random
from kafka import KafkaProducer
from fastavro import parse_schema, schemaless_writer, writer
import io

#Define Avro weather sensor schema
avro_schema_dict = {
    "type": "record",
    "name": "SensorReading",
    "namespace": "com.example",
    "fields": [
        {"name": "timestamp", "type": "long"},
        {"name": "sensor_id", "type": "string"},
        {"name": "temperature", "type": "double"},
        {"name": "humidity", "type": "double"},
        {"name": "location", "type": "string"}
    ]
}

# Parse the schema
parsed_schema = parse_schema(avro_schema_dict)


def serialize_avro(data: dict, schema) -> bytes:
    """
    Serialize data to Avro bytes
    """
    # Create a buffer to hold the serialized data
    out = io.BytesIO()

    # The issue is that fastavro.writer() creates an Avro Object Container File format (with headers),
    # but Spark's from_avro() expects raw Avro binary without the container wrapper.

    # writer(out, schema, [data])
    schemaless_writer(out, schema, data)

    # Get the serialized bytes from the buffer
    return out.getvalue()

class SensorDataProducer:
    def __init__(self, bootstrap_servers="localhost:9092", topic="sensor-data"):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: serialize_avro(v, parsed_schema)
        )
        self.topic = topic
        self.locations = ["Kyiv", "London", "Tokyo", "New York", "Sydney"]

    def generate_reading(self):
        return {
            "timestamp": int(time.time()),
            "sensor_id": f"sensor_{random.randint(1, 100)}",
            "temperature": random.uniform(10, 30),
            "humidity": random.uniform(30, 70),
            "location": random.choice(self.locations)
        }
    def produce_data(self, num_messages=100, interval=1):
        for _ in range(num_messages):
            reading = self.generate_reading()
            self.producer.send(self.topic, value=reading)

            if (_ + 1) % 10 == 0:
                print(f"Sent {str(_ + 1)} messages")
            time.sleep(interval)

            self.producer.flush()
            print(f"Sent total {num_messages} messages")

    def close(self):
        self.producer.close()
if __name__ == "__main__":
    producer = SensorDataProducer(bootstrap_servers="localhost:9092", topic="sensor-data")
    try:
        producer.produce_data(num_messages=100, interval=1)
    except KeyboardInterrupt:
        pass
    finally:
        producer.close()