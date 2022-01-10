# Longest Path (i.e., Critical Path)

Using the debug instrumentation when iterating over the longest path:

```python
out = []
out.append({'id': doc['id'], 'name': doc['name'], 'start_time': doc['start_time'], 'origin': doc.get('origin', None)})
```

```
{'id': '7727af9f20ffa9ff', 'name': 'production-thumbnail-generator/production', 'start_time': 1606220832.0, 'origin': 'AWS::ApiGateway::Stage'}
{'id': '136a17265b0ba125', 'name': 'Lambda', 'start_time': 1606220832.004, 'origin': None}
{'id': '09cf64b5fc54574f', 'name': 'thumbnail-generator-production-upload', 'start_time': 1606220832.037, 'origin': 'AWS::Lambda'}
{'id': '6fc3c3c212df370e', 'name': 'thumbnail-generator-production-upload', 'start_time': 1606220835.429, 'origin': 'AWS::Lambda::Function'}
{'id': '554ab0426b358e6b', 'name': 'Initialization', 'start_time': 1606220832.471, 'origin': None}
{'id': '632eaa39499ace4e', 'name': 'S3', 'start_time': 1606220835.696, 'origin': None}
{'id': '22df469b17cec908', 'name': 'S3', 'start_time': 1606220835.696, 'origin': 'AWS::S3::Bucket'}
{'id': '7afdc379e1199035', 'name': 'S3', 'start_time': 1606220837.335, 'origin': None}
{'id': '21378a100add4857', 'name': 'S3', 'start_time': 1606220837.335, 'origin': 'AWS::S3::Bucket'}
{'id': '1bd28856f2142fa1', 'name': 'thumbnail-generator-production-thumbnail-generator', 'start_time': 1606220838.776, 'origin': 'AWS::Lambda'}
{'id': '64838b5f69be8e41', 'name': 'Dwell Time', 'start_time': 1606220838.776, 'origin': None}
{'id': '1a4bad45b9acd2a6', 'name': 'Attempt #1', 'start_time': 1606220838.835, 'origin': None}
{'id': '25b1475b605b5ae7', 'name': 'thumbnail-generator-production-thumbnail-generator', 'start_time': 1606220840.361, 'origin': 'AWS::Lambda::Function'}
{'id': '7fdf67c6090e62ba', 'name': 'Initialization', 'start_time': 1606220839.172, 'origin': None}
```

# Latency Breakdown

```python
G.graph['critical_path']
```

```
{'start_time': 1606220832.0,   'end_time': 1606220832.004, 'duration': datetime.timedelta(microseconds=4000), 'resource': '7727af9f20ffa9ff', 'source': '7727af9f20ffa9ff', 'target': '136a17265b0ba125', 'type': 'sync-send', 'category': 'orchestration'}
{'start_time': 1606220832.004, 'end_time': 1606220832.037, 'duration': datetime.timedelta(microseconds=33000), 'resource': '136a17265b0ba125', 'source': '136a17265b0ba125', 'target': '09cf64b5fc54574f', 'type': 'sync-send', 'category': 'orchestration'}
{'start_time': 1606220832.037, 'end_time': 1606220832.471, 'duration': datetime.timedelta(microseconds=434000), 'resource': '09cf64b5fc54574f', 'type': 'span-parent', 'category': 'container_initialization'}
{'start_time': 1606220832.471, 'end_time': 1606220835.427, 'duration': datetime.timedelta(seconds=2, microseconds=956000), 'resource': '554ab0426b358e6b', 'type': 'span', 'category': 'runtime_initialization'}
{'start_time': 1606220835.427, 'end_time': 1606220835.429, 'duration': datetime.timedelta(microseconds=2000), 'resource': '09cf64b5fc54574f', 'source': '554ab0426b358e6b', 'target': '6fc3c3c212df370e', 'type': 'span-parent', 'category': 'orchestration'}
{'start_time': 1606220835.429, 'end_time': 1606220835.696, 'duration': datetime.timedelta(microseconds=267000), 'resource': '6fc3c3c212df370e', 'source': '6fc3c3c212df370e', 'target': '632eaa39499ace4e', 'type': 'sync-send', 'category': 'computation'}
{'start_time': 1606220835.696, 'end_time': 1606220835.696, 'duration': datetime.timedelta(0), 'resource': '632eaa39499ace4e', 'source': '632eaa39499ace4e', 'target': '22df469b17cec908', 'type': 'sync-send', 'category': 'unclassified'}
{'start_time': 1606220835.696, 'end_time': 1606220837.175, 'duration': datetime.timedelta(seconds=1, microseconds=479000), 'resource': '22df469b17cec908', 'type': 'span', 'category': 'external_service'}
{'start_time': 1606220837.175, 'end_time': 1606220837.175, 'duration': datetime.timedelta(0), 'resource': '632eaa39499ace4e', 'source': '22df469b17cec908', 'target': '632eaa39499ace4e', 'type': 'sync-receive', 'category': 'unclassified'}
{'start_time': 1606220837.175, 'end_time': 1606220837.335, 'duration': datetime.timedelta(microseconds=160000), 'resource': '6fc3c3c212df370e', 'source': '632eaa39499ace4e', 'target': '7afdc379e1199035', 'type': 'span-parent', 'category': 'computation'}
{'start_time': 1606220837.335, 'end_time': 1606220837.335, 'duration': datetime.timedelta(0), 'resource': '7afdc379e1199035', 'source': '7afdc379e1199035', 'target': '21378a100add4857', 'type': 'sync-send', 'category': 'unclassified'}
{'start_time': 1606220837.335, 'end_time': 1606220837.677, 'duration': datetime.timedelta(microseconds=342000), 'resource': '21378a100add4857', 'type': 'span', 'category': 'external_service'}
{'start_time': 1606220837.677, 'end_time': 1606220838.776, 'duration': datetime.timedelta(seconds=1, microseconds=99000), 'resource': None, 'source': '21378a100add4857', 'target': '1bd28856f2142fa1', 'type': 'async-send', 'category': 'trigger'}
{'start_time': 1606220838.776, 'end_time': 1606220838.776, 'duration': datetime.timedelta(0), 'resource': '1bd28856f2142fa1', 'type': 'span', 'category': 'orchestration'}
{'start_time': 1606220838.776, 'end_time': 1606220838.776, 'duration': datetime.timedelta(0), 'resource': None, 'source': '1bd28856f2142fa1', 'target': '64838b5f69be8e41', 'type': 'async-send', 'category': 'trigger'}
{'start_time': 1606220838.776, 'end_time': 1606220838.835, 'duration': datetime.timedelta(microseconds=59000), 'resource': '64838b5f69be8e41', 'type': 'span', 'category': 'queing'}
{'start_time': 1606220838.835, 'end_time': 1606220838.835, 'duration': datetime.timedelta(0), 'resource': None, 'source': '64838b5f69be8e41', 'target': '1a4bad45b9acd2a6', 'type': 'async-send', 'category': 'trigger'}
{'start_time': 1606220838.835, 'end_time': 1606220839.172, 'duration': datetime.timedelta(microseconds=337000), 'resource': '1a4bad45b9acd2a6', 'type': 'span-parent', 'category': 'container_initialization'}
```
