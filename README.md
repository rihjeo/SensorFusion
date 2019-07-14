### README.md

- Sensor Fusion Code Repository
- Lambda는 AWS Greengrass가 Python2.7버전으로 제공하였기 때문에 2.7버전 Code이다.
- Sensing.py 실행 명령어 형식은 아래와 같다.
#### python Sensing.py --endpoint AWS_IOT_ENDPOINT --rootCA root-ca-cert.pem --cert publisher.cert.pem --key publisher.private.key --thingName HelloWorld_Publisher --topic 'hello/world/pubsub' --mode publish
