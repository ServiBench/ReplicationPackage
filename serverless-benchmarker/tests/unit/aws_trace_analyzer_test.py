import json
import csv
import sys
from pathlib import Path
import datetime
import pytest
import networkx as nx

from sb.aws_trace_analyzer import CSV_FIELDS, extract_trace_breakdown, longest_path, create_span_graph, duration, get_sorted_children, is_async_call, call_stack  # noqa: E501


def test_get_sorted_children():
    G = nx.DiGraph()
    # Example inspired from the matrix multiplication app
    # where two spans (sub1, sub2) have the same end_time (end) but
    # sub1 just starts 1ms earlier (start1). Timeline: start1<end1=start2=end2
    start1 = 1613573901.68
    start2 = 1613573901.681
    end = 1613573901.681
    root_id = 'root_id'
    sub1_id = 'sub1'
    sub2_id = 'sub2'
    G.add_node(root_id)
    # Adding sub2 first
    G.add_node('sub2', **{'doc': {'start_time': start2, 'end_time': end}})
    G.add_edge(root_id, sub2_id)
    # Adding sub1 second
    G.add_node('sub1', **{'doc': {'start_time': start1, 'end_time': end}})
    G.add_edge(root_id, sub1_id)
    succ_ids = list(G.successors(root_id))
    # Should have wrong order by default
    assert succ_ids == [sub2_id, sub1_id]
    assert get_sorted_children(G, root_id) == ['sub1', 'sub2']


def test_is_async_call_async():
    parent = {'end_time': 1624353531.865}
    child = {'end_time': 1624353532.865}
    assert is_async_call(parent, child)


def test_is_async_call_sync():
    parent = {'end_time': 1624353531.865}
    child = {'end_time': 1624353531.865}
    assert not is_async_call(parent, child)


def test_is_async_call_sync_with_margin():
    """Case of 999 microsecond margin.
    Source: exp31/realworld-dynamodb-lambda/logs/2021-04-30_14-52-50"""
    parent = {'end_time': 1624353531.865}
    child = {'end_time': 1624353531.8654525}
    assert not is_async_call(parent, child)


def test_is_async_call_sync_with_margin_larger():
    """Case of 1001 microsecond margin.
    Source: exp31/faas-migration-go/aws/logs/2021-04-30_09-06-52"""
    parent = {'end_time': 1619774396.626}
    child = {'end_time': 1619774396.627}
    assert not is_async_call(parent, child)


def test_is_async_call_async_with_margin():
    """Edge case beyond the 1001 microsecond margin.
    It should detect an async call when exceeding the margin."""
    parent = {'end_time': 1619774396.626}
    child = {'end_time': 1619774396.6271}
    assert is_async_call(parent, child)


def traces_path(app):
    """Returns the path to the traces.json for a given app name."""
    tests_path = Path(__file__).parent.parent
    sub_path = f"fixtures/aws_trace_analyzer/{app}/traces.json"
    return (tests_path / sub_path).resolve()


def assert_trace_breakdown(t_path, expected_breakdown):
    """Compares the trace breakdown from a single trace against
    a given expected_breakdown.
    Caveat: Supports only a single trace"""
    with open(t_path) as json_file:
        trace = json.load(json_file)
        trace_breakdown = extract_trace_breakdown(trace)
        assert trace_breakdown == expected_breakdown


def print_csv(trace_breakdown):
    """Debugging helper that prints a trace breakdown as CSV output"""
    trace_writer = csv.writer(sys.stdout, quoting=csv.QUOTE_MINIMAL)
    headers = CSV_FIELDS
    trace_writer.writerow(headers)
    trace_writer.writerow(trace_breakdown)


def test_extract_trace_breakdown_thumbnail_app():
    """Tests the most studied execution of the thumbnail app.
    See fixtures/thumbnail_app for additional visualizations.
    """
    expected_breakdown = ['1-5fbcfc1f-4d2e9bed6dc0c41c39dfdb2f', 1606220832.0, 1606220846.963, datetime.timedelta(seconds=14, microseconds=963000), 'https://gcz7l3ixlb.execute-api.us-east-1.amazonaws.com/production/upload', 2, 0, 0, 0, ['AWS::ApiGateway::Stage', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket'], ['production-thumbnail-generator/production', 'Lambda', 'thumbnail-generator-production-upload', 'thumbnail-generator-production-upload', 'Initialization', 'S3', 'S3', 'S3', 'S3', 'thumbnail-generator-production-thumbnail-generator', 'Dwell Time', 'Attempt #1', 'thumbnail-generator-production-thumbnail-generator', 'Initialization', 'S3', 'S3', 'S3', 'S3'], datetime.timedelta(microseconds=86000), datetime.timedelta(seconds=1, microseconds=99000), datetime.timedelta(microseconds=771000), datetime.timedelta(seconds=4, microseconds=142000), datetime.timedelta(seconds=5, microseconds=501000), datetime.timedelta(microseconds=59000), None, datetime.timedelta(seconds=3, microseconds=305000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('thumbnail_app')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_breakdown_thumbnail_app_warm():
    expected_breakdown = ['1-6049e32a-49e6a9866fc15c8e30479d09', 1615455019.055, 1615455027.436, datetime.timedelta(seconds=8, microseconds=381000), 'https://d574arqmjg.execute-api.us-east-1.amazonaws.com/prod/upload', 1, 0, 0, 0, ['AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::ApiGateway::Stage', 'AWS::Lambda', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket'], ['prod-thumbnail-generator/prod', 'Lambda', 'thumbnail-generator-prod-upload', 'thumbnail-generator-prod-upload', 'S3', 'S3', 'thumbnail-generator-prod-thumbnail-generator', 'Dwell Time', 'Attempt #1', 'thumbnail-generator-prod-thumbnail-generator', 'Initialization', 'S3', 'S3', 'S3', 'S3'], datetime.timedelta(microseconds=40000), datetime.timedelta(seconds=1, microseconds=44000), datetime.timedelta(microseconds=345000), datetime.timedelta(seconds=1, microseconds=29000), datetime.timedelta(seconds=4, microseconds=310000), datetime.timedelta(microseconds=76000), None, datetime.timedelta(seconds=1, microseconds=537000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('thumbnail_app_warm')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_breakdown_thumbnail_app_missing_root():
    """
    The root segment of the trace (6f58e0a0bce69065) is missing and created empty through
    the parent_id of the child node (60f93765ebcf2a58). This invalidates the trace duration
    because another node with the earliest start time is chosen as new root.
    Source:
    lg3/ec2-user/faas-migration/ThumbnailGenerator/Lambda/logs/2021-04-29_23-40-56
    """
    # Potential partial result (if we plan to support this, missing external_services!)
    expected_breakdown = ['1-608b4550-1929270a067637cfd701f545', 1619739984.606, 1619739985.731, datetime.timedelta(seconds=1, microseconds=125000), None, 0, 0, 0, 0, ['AWS::Lambda', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda::Function', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket'], ['thumbnail-generator-dev-upload', 'thumbnail-generator-dev-upload', 'S3', 'S3', 'thumbnail-generator-dev-thumbnail-generator', 'Dwell Time', 'Attempt #1', 'thumbnail-generator-dev-thumbnail-generator', 'S3', 'S3', 'S3', 'S3'], datetime.timedelta(microseconds=17000), datetime.timedelta(microseconds=800000), None, None, datetime.timedelta(microseconds=123000), datetime.timedelta(microseconds=49000), None, datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('thumbnail_app_missing_root')
    with pytest.raises(Exception) as e:
        assert_trace_breakdown(tp, expected_breakdown)
    assert str(e.value) == 'Incomplete trace 1-608b4550-1929270a067637cfd701f545 because the parent node 6f58e0a0bce69065 of node 60f93765ebcf2a58 is empty.'  # noqa: E501


def test_extract_trace_breakdown_thumbnail_app_in_progress():
    """
    The segment 55b8cdd122595924 is in_progress and therefore misses its 'end_time'.
    Source:
    lg3/ec2-user/faas-migration/ThumbnailGenerator/Lambda/logs/2021-04-29_23-40-56
    """
    expected_breakdown = ['1-608b4565-558f8ff60404afa17feb278c', 1619739984.606, 1619739985.731, datetime.timedelta(seconds=1, microseconds=125000), None, 0, 0, 0, 0, ['AWS::Lambda', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda::Function', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket'], ['thumbnail-generator-dev-upload', 'thumbnail-generator-dev-upload', 'S3', 'S3', 'thumbnail-generator-dev-thumbnail-generator', 'Dwell Time', 'Attempt #1', 'thumbnail-generator-dev-thumbnail-generator', 'S3', 'S3', 'S3', 'S3'], datetime.timedelta(microseconds=17000), datetime.timedelta(microseconds=800000), None, None, datetime.timedelta(microseconds=123000), datetime.timedelta(microseconds=49000), None, datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('thumbnail_app_in_progress')
    with pytest.raises(Exception) as e:
        assert_trace_breakdown(tp, expected_breakdown)
    assert str(e.value) == 'Subsegment 55b8cdd122595924 in progress.'


def test_extract_trace_breakdown_thumbnail_app_fault():
    """
    The segment 514db1f2511b92cf has a fault and returned HTTP status 500.
    Source:
    lg4/ec2-user/faas-migration/ThumbnailGenerator/Lambda/logs/2021-04-30_11-49-21
    """
    expected_breakdown = ['1-608bf96d-9be20cff02f9e96ff14ae178', 1619786093.459, 1619786093.469, datetime.timedelta(microseconds=10000), 'https://8vtxzfmw67.execute-api.us-west-2.amazonaws.com/dev/upload', 0, 0, 0, 1, ['AWS::ApiGateway::Stage', 'AWS::Lambda'], ['dev-thumbnail-generator/dev', 'Lambda', 'Lambda'], datetime.timedelta(microseconds=10000), None, None, None, None, None, None, None, datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('thumbnail_app_fault')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_breakdown_thumbnail_app_error_fault_throttle():
    """Trace with errors, faults, and throttle
    Source:
    lg4/ec2-user/faas-migration/ThumbnailGenerator/Lambda/logs/2021-04-30_02-58-28
    """
    expected_breakdown = ['1-608b7926-687718151c26192849c3d020', 1619753254.117, 1619753261.239, datetime.timedelta(seconds=7, microseconds=122000), 'https://ldblsc9z0j.execute-api.us-west-2.amazonaws.com/dev/upload', 0, 3, 2, 3, ['AWS::Lambda::Function', 'AWS::Lambda', 'AWS::ApiGateway::Stage', 'AWS::S3::Bucket'], ['dev-thumbnail-generator/dev', 'Lambda', 'thumbnail-generator-dev-upload', 'thumbnail-generator-dev-upload', 'S3', 'S3'], datetime.timedelta(microseconds=29000), None, None, None, datetime.timedelta(microseconds=115000), None, None, datetime.timedelta(seconds=6, microseconds=978000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('thumbnail_app_error_fault_throttle')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_breakdown_matrix_app():
    expected_breakdown = ['1-602d2f0b-7bd8e768607f9c8200690500', 1613573899.167, 1613573911.234, datetime.timedelta(seconds=12, microseconds=67000), 'https://tf51nutw60.execute-api.us-east-1.amazonaws.com/prod/run', 5, 0, 0, 0, ['AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::ApiGateway::Stage', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::StepFunctions::StateMachine'], ['prod-matrix-mul/prod', 'STEPFUNCTIONS', 'MatrixMul', 'CreateMatrix', 'Lambda', 'matrix-mul-prod-create_matrix', 'matrix-mul-prod-create_matrix', 'Initialization', 'ChooseVariant', 'AppendWorkerCount', 'DistributeWork', 'Lambda', 'matrix-mul-prod-paralell_mul_scheduler', 'matrix-mul-prod-paralell_mul_scheduler', 'Initialization', 'ParallelMul', 'Branch 2', 'AssignWorkerID3', 'MulWorker3', 'Lambda', 'matrix-mul-prod-mul_worker', 'matrix-mul-prod-mul_worker', 'Initialization', 'BuildResult', 'Lambda', 'matrix-mul-prod-result_builder', 'matrix-mul-prod-result_builder', 'Initialization', 'GenReport', 'Lambda', 'matrix-mul-prod-build_report', 'matrix-mul-prod-build_report', 'Initialization'], datetime.timedelta(microseconds=399000), datetime.timedelta(0), datetime.timedelta(seconds=2, microseconds=359000), datetime.timedelta(seconds=1, microseconds=243000), datetime.timedelta(seconds=8, microseconds=66000), None, None, None, datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('matrix_app')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_model_training_app():
    """ Different timestamp granularity at two places:
    1) AWS::Lambda segment (03c544ca90d5515d) with end_time 1624353531.865
       and the AWS::Lambda::Function segment (2d1ac1631da8de72) with end_time 1624353531.8654525
       The microsecond-based timestamp is +0.0004525s later and hence counts as async invocation
       because the child node has a later start time than the parent node. This is incorrect and
       left 1547 microseconds missing at the end of the trace when validating against the duration.
       This issue was fixed by adding a margin for imprecise timestamps (i.e., epsilon) in the
       is_async_invocation heuristic.
    2) The top-level API gateway end_time only has milliseconds (0.8669999 => 0.867)
    Source:
    exp31/serverless-faas-workbench/aws/cpu-memory/model_training/logs/2021-06-22_11-18-22
    """
    expected_breakdown = ['1-60d1aaf2-671e23cc0b33e597b9728177', 1624353522.835, 1624353531.867, datetime.timedelta(seconds=9, microseconds=32000), 'https://fabi09ztfd.execute-api.us-east-1.amazonaws.com/dev/train', 0, 0, 0, 0, ['AWS::Lambda::Function', 'AWS::Lambda', 'AWS::ApiGateway::Stage', 'AWS::S3::Bucket', 'AWS::S3::Bucket'], ['dev-model-training/dev', 'Lambda', 'model-training-dev-model-training', 'model-training-dev-model-training', 'Invocation', 'S3', 'S3', 'S3', 'S3', 'Overhead'], datetime.timedelta(microseconds=17530), None, None, None, datetime.timedelta(seconds=8, microseconds=818030), None, datetime.timedelta(microseconds=198), datetime.timedelta(microseconds=196242), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('model_training_app')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_realworld_app():
    """Official duration uses less accurate timestamp for start_time:
    0:00:00.035000 (official) vs 0:00:00.035189 (end_time - start_time).
    Fixed using a timestamp margin to ignore differences below a threshold (e.g., 1ms).
    Source:
    exp31/realworld-dynamodb-lambda/logs/2021-04-30_14-52-50
    """
    expected_breakdown = ['1-608c1bd4-8ceba73b6799988cd7aaee1a', 1619794900.85, 1619794900.8851886, datetime.timedelta(microseconds=35000), 'https://538uury0ga.execute-api.eu-west-1.amazonaws.com/dev/api/articles/8c90798198-vvwthh/comments', 0, 0, 0, 0, ['AWS::ApiGateway::Stage', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::DynamoDB::Table', 'AWS::DynamoDB::Table'], ['dev-realworld/dev', 'Lambda', 'realworld-dev-getComments', 'realworld-dev-getComments', 'Invocation', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'Overhead'], datetime.timedelta(microseconds=12043), None, None, None, datetime.timedelta(microseconds=3645), None, datetime.timedelta(microseconds=312), datetime.timedelta(microseconds=19000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('realworld_app')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_realworld_app_margin():
    """
    Fixed by using timestamp margin when comparing
    * the trace duration from X-Ray (50ms) against
    * the latency breakdown (49ms).
    Source:
    lg3/ec2-user/realworld-dynamodb-lambda/logs/2021-04-30_15-52-46
    """
    expected_breakdown = ['1-608c2b95-da77705249832f8715f095de', 1619798933.143, 1619798933.1929998, datetime.timedelta(microseconds=50000), 'https://myz35jktl7.execute-api.eu-west-1.amazonaws.com/dev/api/articles/110b06f1f4-kg38cx', 0, 0, 0, 0, ['AWS::ApiGateway::Stage', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::DynamoDB::Table', 'AWS::DynamoDB::Table', 'AWS::DynamoDB::Table'], ['dev-realworld/dev', 'Lambda', 'realworld-dev-getArticle', 'realworld-dev-getArticle', 'Invocation', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'Overhead'], datetime.timedelta(microseconds=13087), None, None, None, datetime.timedelta(microseconds=4614), None, datetime.timedelta(microseconds=299), datetime.timedelta(microseconds=31000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('realworld_app_margin')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_todo_app():
    """Reproduces a trace where the trace duration doesn't
    match the latency breakdown due to clock inaccuracy
    between the API gateway Lambda segment (045739a66c26a771, 1619774396.626)
    and the AWS::Lambda segment (6fd8f7cf8343d129, 1619774396.627).
    The API gateway synchronously invokes AWS::Lambda and should therefore end
    later and not 1ms earlier.
    Source:
    exp31/faas-migration-go/aws/logs/2021-04-30_09-06-52
    """
    expected_breakdown = ['1-608bcbbc-634420f19aa0dd283cbf7529', 1619774396.595, 1619774396.636, datetime.timedelta(microseconds=41000), 'https://bm0q7xberc.execute-api.eu-west-1.amazonaws.com/dev/lst', 0, 0, 0, 0, ['AWS::Lambda::Function', 'AWS::Lambda', 'AWS::ApiGateway::Stage', 'AWS::DynamoDB::Table'], ['dev-aws/dev', 'Lambda', 'aws-dev-lst', 'aws-dev-lst', 'DynamoDB', 'DynamoDB'], datetime.timedelta(microseconds=31000), None, None, None, datetime.timedelta(microseconds=1579), None, None, datetime.timedelta(microseconds=8421), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('todo_app')
    assert_trace_breakdown(tp, expected_breakdown)


def test_longest_path_sync():
    """Scenario where a synchronous invocation is the longest path"""
    start_time = 1619760991.000
    s1_start = start_time
    s2_start = start_time + 10
    s2_end = start_time + 20
    a_start = start_time + 25
    s3_start = start_time + 30
    a_end = start_time + 35
    s3_end = start_time + 40
    s1_end = start_time + 50

    segments = [
        ('s1', s1_start, s1_end),
        ('s2', s2_start, s2_end),
        ('a', a_start, a_end),
        ('s3', s3_start, s3_end)
    ]

    G = nx.DiGraph()
    G.graph['start'] = 's1'
    G.graph['end'] = 's1'
    for (id, start_time, end_time) in segments:
        s1 = {'id': id, 'start_time': start_time, 'end_time': end_time}
        node_attr = {'doc': s1, 'duration': duration(s1)}
        G.add_node(s1['id'], **node_attr)
    G.add_edge('s1', 's2')
    G.add_edge('s2', 'a')
    G.add_edge('s1', 's3')

    G.graph['call_stack'] = call_stack(G, 's1')
    assert ['s1', 's2', 's3'] == longest_path(G, 's1')


def test_longest_path_async():
    """Scenario where an asynchronous invocation is the longest path"""
    start_time = 1619760991.000
    s1_start = start_time
    s2_start = start_time + 10
    s2_end = start_time + 20
    s_start = start_time + 30
    s_end = start_time + 40
    s1_end = start_time + 50
    s3_start = start_time + 70
    s3_end = start_time + 80

    segments = [
        ('s1', s1_start, s1_end),
        ('s2', s2_start, s2_end),
        ('s', s_start, s_end),
        ('s3', s3_start, s3_end)
    ]

    G = nx.DiGraph()
    for (id, start_time, end_time) in segments:
        s1 = {'id': id, 'start_time': start_time, 'end_time': end_time}
        node_attr = {'doc': s1, 'duration': duration(s1)}
        G.add_node(s1['id'], **node_attr)
    G.add_edge('s1', 's2')
    G.add_edge('s1', 's')
    G.add_edge('s2', 's3')

    G.graph['call_stack'] = call_stack(G, 's3')
    assert ['s1', 's2', 's3'] == longest_path(G, 's1')


def test_longest_path_event_processing_app():
    """Reproduces an issue where the last returning child
    was appended to the longest path although not being part of it.
    Specifically, the overhead node `0d431` was appended at the end of the
    longest path but should not be part of it because the async transition
    from SNS `3d46` to the format function `6d05` consitutes a longer path.
    Source:
    exp31/faas-migration/Event-Processing/Lambda/logs/2021-04-30_05-34-22
    """
    # Manually validated based on trace map, timestamp inspection, and
    # comparison against networkx implementation of dag_longest_path
    expected_path = ['59d284e254912526', '7ddca1046ef1985c', '5d98752257e51041', '4c57c76218613840', 'ce71a9e6624497a6', '62a5b8bdc147d7dd', '3d46a9ec2871f006', '6d05055c18416f23', '09b064d0dfd77159', '1ac8a21aee22b4e3', '206c8bde4844d1da', '0968878f47f64916', '4e389a109ab7353c', '1a3fbbb81821e5dd', '02b8700a2f5e645f', 'e4546d09dde35985']  # noqa: E501
    tp = traces_path('event_processing_app')
    with open(tp) as json_file:
        trace = json.load(json_file)
        G = create_span_graph(trace)
        assert G.graph['longest_path'] == expected_path


def test_extract_trace_event_processing_app():
    """Reproduces a trace with a validation error on the trace duration:
    "Trace duration 0:00:00.125000 does not match latency breakdown 0:00:00.047000
    within margin 0:00:00.001001."
    Source:
    exp31/faas-migration/Event-Processing/Lambda/logs/2021-04-30_05-34-22
    """
    expected_breakdown = ['1-608b975f-82c9cf3915cf8d7c1093ada7', 1619760991.873, 1619760991.998, datetime.timedelta(microseconds=125000), 'https://aqk7l5ytj2.execute-api.eu-west-1.amazonaws.com/dev/ingest', 0, 0, 0, 0, ['AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::SNS', 'AWS::ApiGateway::Stage', 'AWS::Lambda::Function', 'AWS::SQS::Queue'], ['dev-event-processing/dev', 'Lambda', 'event-processing-dev-ingest', 'event-processing-dev-ingest', 'Invocation', 'SNS', 'SNS', 'event-processing-dev-format_state_change', 'Dwell Time', 'Attempt #1', 'event-processing-dev-format_state_change', 'Invocation', 'SQS', 'SQS', 'QueueTime', 'Overhead'], datetime.timedelta(microseconds=25523), datetime.timedelta(microseconds=11000), None, None, datetime.timedelta(microseconds=1807), datetime.timedelta(microseconds=32000), datetime.timedelta(microseconds=670), datetime.timedelta(microseconds=54000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('event_processing_app')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_event_processing_memory_leak():
    """Reproduces a trace that caused a memory leak in an infinite loop.
    Also occurred for 2022-01-07_07-02-02 and 2022-01-05_10-56-37.
    Infinite loop: ['766022ec80057fcd', '45b312fcf8d12d5b', '318f814c2e3a0712', '30613e47b2fec822', '8434b28c54ed67d3', '4aa09bbd2714c1c1']  # noqa: E501
    Source: lg12/ec2-user/faas-migration/Event-Processing/Lambda/logs/2022-01-05_10-56-37
    """
    with pytest.raises(Exception) as e:
        tp = traces_path('event_processing_memory_leak')
        assert_trace_breakdown(tp, None)
    assert str(e.value) == 'Detected infinite loop starting from node 766022ec80057fcd'


def test_extract_trace_hello_retail_app_error():
    """Reproduces a trace with the error:
    "Task Timed Out:
    'arn:aws:states:eu-west-1:0123456789012:activity:dev-hello-retail-product-photos-receive"
    Source:
    exp31/hello-retail/logs/2021-04-30_14-15-59
    """
    expected_breakdown = ['1-608c1487-8892c4a7bc5e24a223902a15', 1619793031.301, 1619793031.47, datetime.timedelta(microseconds=169000), 'https://luokbyeogl.execute-api.eu-west-1.amazonaws.com/dev/sms', 0, 2, 0, 2, ['AWS::Lambda::Function', 'AWS::Lambda', 'AWS::ApiGateway::Stage', 'AWS::DynamoDB::Table', 'AWS::S3::Bucket', 'AWS::stepfunctions'], ['dev-hello-retail-product-photos-receive/dev', 'Lambda', 'hello-retail-product-photos-receive-dev-receive', 'hello-retail-product-photos-receive-dev-receive', 'Invocation', 'DynamoDB', 'DynamoDB', 'S3', 'S3', 'stepfunctions', 'stepfunctions', 'Overhead'], datetime.timedelta(microseconds=52829), None, None, None, datetime.timedelta(microseconds=6511), None, datetime.timedelta(microseconds=660), datetime.timedelta(microseconds=109000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('hello_retail_app_error')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_image_processing_app_error():
    """Reproduces a trace with the expected error:
    "PhotoDoesNotMeetRequirementError"
    This case tests the error case.
    Source:
    exp31/aws-serverless-workshops/ImageProcessing/logs/2021-04-30_07-02-35
    trace_id=1-608bac5f-feef4e053d4b9fa008fcb044
    """
    expected_breakdown = ['1-608bac5f-feef4e053d4b9fa008fcb044', 1619766367.436, 1619766368.579, datetime.timedelta(seconds=1, microseconds=143000), 'https://s47zgw7ake.execute-api.eu-west-1.amazonaws.com/execute/', 0, 4, 0, 1, ['AWS::Lambda', 'AWS::StepFunctions::StateMachine', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::ApiGateway::Stage', 'AWS::Lambda::Function', 'AWS::rekognition'], ['APIGatewayToStepFunctions/execute', 'STEPFUNCTIONS', 'RiderPhotoProcessing-8gfRn3qHdsBb', 'FaceDetection', 'Lambda', 'wildrydes-FaceDetectionFunction-UB72KZMWRLCF', 'wildrydes-FaceDetectionFunction-UB72KZMWRLCF', 'Invocation', 'rekognition', 'rekognition', 'Overhead', 'PhotoDoesNotMeetRequirement', 'Lambda', 'wildrydes-NotificationPlaceholderFunction-KDTBMSLPJ0O2', 'wildrydes-NotificationPlaceholderFunction-KDTBMSLPJ0O2', 'Invocation', 'Overhead'], datetime.timedelta(microseconds=106497), datetime.timedelta(0), None, None, datetime.timedelta(microseconds=4818), None, datetime.timedelta(microseconds=685), datetime.timedelta(seconds=1, microseconds=31000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('image_processing_app_error')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_realworld_app_missing_coldstart():
    """Reproduces a trace where a coldstart remained undetected
    due to clock inaccuracy. An AWS::Lambda::Function segment
    shifts the end of the trace by +2ms (compared to gateway).
    This case is not handled and currently raises an assertion error.
    If might be possible to adjust the end time in cases where
    we can can ensure that our critical path is more reliable
    than wrong end nodes due to clock synchronization issues.
    Source:
    lg12/ec2-user/realworld-dynamodb-lambda/logs/2021-12-17_07-41-08
    trace_id=1-61bc3f1b-114c0cc33b4e39a3c3fb34ab
    """
    num_cold_starts = 1
    container_initialization = datetime.timedelta(microseconds=423838)
    runtime_initialization = datetime.timedelta(microseconds=540720)
    expected_breakdown = ['1-61bc3f1b-114c0cc33b4e39a3c3fb34ab', 1639726875.949, 1639726877.1055684, datetime.timedelta(seconds=1, microseconds=157000), 'https://e0i8q30zpb.execute-api.us-east-1.amazonaws.com/dev/api/profiles/username_16_0/follow', num_cold_starts, 0, 0, 0, ['AWS::Lambda::Function', 'AWS::Lambda', 'AWS::ApiGateway::Stage', 'AWS::DynamoDB::Table', 'AWS::DynamoDB::Table', 'AWS::DynamoDB::Table', 'AWS::DynamoDB::Table'], ['dev-realworld/dev', 'Lambda', 'realworld-dev-followUser', 'realworld-dev-followUser', 'Initialization', 'Invocation', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'Overhead'], datetime.timedelta(microseconds=20848), None, container_initialization, runtime_initialization, datetime.timedelta(microseconds=13571), None, datetime.timedelta(microseconds=4591), datetime.timedelta(microseconds=153000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('realworld_app_missing_coldstart')
    with pytest.raises(AssertionError) as assert_info:
        assert_trace_breakdown(tp, expected_breakdown)
    assert 'Trace duration 0:00:01.157000 does not match latency breakdown 0:00:01.154000 within margin 0:00:00.001001.' in str(assert_info.value)  # noqa: E501


def test_extract_trace_realworld_app_missing_coldstart2():
    """Reproduces a trace where a coldstart remained undetected
    due to clock inaccuracy where an AWS::Lambda::Function segment
    ends after its parent AWS::Lambda.
    Source:
    lg12/ec2-user/realworld-dynamodb-lambda/logs/2021-12-18_08-02-15
    trace_id=1-61bd95ca-b5e9738e3379edeed26b8a14
    """
    num_cold_starts = 1
    orchestration = datetime.timedelta(microseconds=25169)
    container_initialization = datetime.timedelta(microseconds=265577)
    runtime_initialization = datetime.timedelta(microseconds=544785)
    expected_breakdown = ['1-61bd95ca-b5e9738e3379edeed26b8a14', 1639814602.89, 1639814603.906, datetime.timedelta(seconds=1, microseconds=16000), 'https://dm7813466i.execute-api.us-east-1.amazonaws.com/dev/api/profiles/username_28_0/follow', num_cold_starts, 0, 0, 0, ['AWS::ApiGateway::Stage', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::DynamoDB::Table', 'AWS::DynamoDB::Table', 'AWS::DynamoDB::Table', 'AWS::DynamoDB::Table'], ['dev-realworld/dev', 'Lambda', 'realworld-dev-followUser', 'realworld-dev-followUser', 'Initialization', 'Invocation', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'DynamoDB', 'Overhead'], orchestration, None, container_initialization, runtime_initialization, datetime.timedelta(microseconds=18210), None, datetime.timedelta(microseconds=1259), datetime.timedelta(microseconds=161000), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('realworld_app_missing_coldstart2')
    assert_trace_breakdown(tp, expected_breakdown)


def test_extract_trace_matrix_app_same_end_time():
    """Reproduces a trace where multiple identical end times
    triggered a false positive validation exception.
    Source: lg12/ec2-user/aws-serverless-workshops/ImageProcessing/logs/2021-12-15_11-25-15
    """
    expected_breakdown = ['1-61bd75b1-6ef5c6f8ec5c4d9022d6e616', 1639806385.283, 1639806386.906, datetime.timedelta(seconds=1, microseconds=623000), 'https://icyvuu0re9.execute-api.us-east-1.amazonaws.com/dev/run', 0, 0, 0, 0, ['AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::Lambda', 'AWS::Lambda', 'AWS::Lambda::Function', 'AWS::StepFunctions::StateMachine', 'AWS::Lambda', 'AWS::Lambda', 'AWS::ApiGateway::Stage', 'AWS::Lambda::Function', 'AWS::Lambda::Function', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket', 'AWS::S3::Bucket'], ['dev-matrix-mul/dev', 'STEPFUNCTIONS', 'MatrixMul', 'CreateMatrix', 'Lambda', 'matrix-mul-dev-create_matrix', 'matrix-mul-dev-create_matrix', 'Invocation', 'S3', 'S3', 'Overhead', 'ChooseVariant', 'AppendWorkerCount', 'DistributeWork', 'Lambda', 'matrix-mul-dev-parallel_mul_scheduler', 'matrix-mul-dev-parallel_mul_scheduler', 'Invocation', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'Overhead', 'ParallelMul', 'Branch 3', 'AssignWorkerID5', 'MulWorker5', 'Lambda', 'matrix-mul-dev-mul_worker', 'matrix-mul-dev-mul_worker', 'Invocation', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'Overhead', 'BuildResult', 'Lambda', 'matrix-mul-dev-result_builder', 'matrix-mul-dev-result_builder', 'Invocation', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'Overhead', 'GenReport', 'Lambda', 'matrix-mul-dev-build_report', 'matrix-mul-dev-build_report', 'Invocation', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'S3', 'Overhead'], datetime.timedelta(microseconds=298034), datetime.timedelta(0), None, None, datetime.timedelta(microseconds=46499), None, datetime.timedelta(microseconds=1088), datetime.timedelta(seconds=1, microseconds=277379), datetime.timedelta(0)]  # noqa: E501
    tp = traces_path('matrix_app_same_end_time')
    assert_trace_breakdown(tp, expected_breakdown)


@pytest.mark.skip(reason="Just used for creating visualizer data.")
def test_extract_tmp_visualizer():
    """Just a tmp case for creating visualizer data
    """
    expected_breakdown = []  # noqa: E501
    tp = traces_path('realworld_app_missing_coldstart2')
    assert_trace_breakdown(tp, expected_breakdown)
