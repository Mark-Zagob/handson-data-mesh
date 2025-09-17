# Kafka CLI command
## topic
kafka-topics --bootstrap-server localhost:9092 --create --topic <topic-name> --partitions 1 --replication-factor 1
kafka-topics --bootstrap-server localhost:9092 --list
kafka-topics --bootstrap-server localhost:9092 --describe --topic <topic-name>

## send sample message to topic
echo "Hello Data Mesh" | kafka-console-producer --bootstrap-server localhost:9092 --topic my-topic-001
kafka-console-consumer --bootstrap-server localhost:9092 --topic my-topic-001 --from-beginning

## load data from file to kafka docker
cat event.json | docker exec -i kafka kafka-console-producer \
  --bootstrap-server kafka:29092 \
  --topic <tomic-name>


## use avro schema
docker exec -ti schema-registry kafka-avro-console-producer \
	--bootstrap-server kafka:9092 \
	--topic user-activity \
	--property "schema.registry.url=http://schema-registry:8081"  \
	--property "parse.key=false" \
	--property "value.schema=$(cat login_event.json)" \
	--property "value.subject.name.strategy=io.confluent.kafka.serializers.subject.TopicRecordNameStrategy"

## schema registry
### view subjects
curl -X GET http://localhost:8081/subjects | jq . #localhost:8081 is url of schema registry
curl -X GET http://localhost:8081/subjects/orders-us-com.company.eco.Order | jq .
### delete subjects
curl -X DELETE http://localhost:8081/subjects/user_activity-value
### check schema of specific topic with specific version
curl -s http://localhost:8081/subjects/orders-us-com.company.eco.Order/versions/1 | jq . #topic orders-us with version 1
