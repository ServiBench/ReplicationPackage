import logging
import json
from pathlib import Path
import csv
from datetime import datetime, timedelta
import networkx as nx
from more_itertools import peekable


"""
Useful resources in XRay docs: https://docs.aws.amazon.com/xray/latest/devguide/xray-api.html
* Getting data: https://docs.aws.amazon.com/xray/latest/devguide/xray-api-gettingdata.html
* XRay segment: https://docs.aws.amazon.com/xray/latest/devguide/xray-api-segmentdocuments.html
"""

"""Margin of error when comparing timestamps with potentially different accuracy.
This fixes an issue where AWS::Lambda segments used ms-based timestamps whereas
AWS::Lambda::Function segments used µs-based timestamps. Similarly,
AWS::ApiGateway::Stage also appears to use ms-based timestamps.
This margin is mainly used for the is_async_call heuristic.
A 1ms offset captures ms-based rounding issues and appears sufficient
based on analyzing millions of traces from AWS X-Ray for most cases.
However, there can be cases where timestamps are off by 3 ms.
For example, 1-61bc3f1b-114c0cc33b4e39a3c3fb34ab from the realworld_app
has a 3ms difference between the end time of AWS::Lambda and AWS::Lambda::Function.
"""
# Allow for a small margin of clock inaccuracy
TIMESTAMP_MARGIN = timedelta(microseconds=1_001)
# Throw exception if extreme time shifts occur in the latency breakdown extraction
TIMESTAMP_THRESHOLD = timedelta(microseconds=10_000)


def t(epoch) -> datetime:
    return datetime.fromtimestamp(epoch)


def ft(epoch) -> str:
    return t(epoch).strftime('%Y-%m-%d %H:%M:%S.%f')


def timediff(start_time, end_time) -> timedelta:
    return t(end_time) - t(start_time)


def create_span_graph(trace):
    """Returns a Networkx graph representing a single trace where
    each node represents a span (or trace segment in XRay terminology) and
    each edge represents a casual relationship.
    """
    # Detect missing trace duration
    if 'Duration' not in trace:
        raise Exception('Missing trace duration.')
    # Parse double JSON-encoded XRay segments
    segments = parse_trace_segments(trace)
    graph_attr = {
        'trace_id': trace['Id'],
        'duration': timedelta(seconds=trace['Duration']),
        'limit_exceeded': trace['LimitExceeded']
    }
    G = nx.DiGraph(**graph_attr)
    for segment in segments:
        # Optionally skip inferred segments because they are duplicates of their parents
        # if 'inferred' in segment and segment['inferred']:
        #     continue
        # Trace is not completed and hence some end_time is missing
        if segment.get('in_progress', False):
            raise Exception(f"Segment {segment['id']} in progress.")
        node_attr = {
            'doc': segment,
            'duration': duration(segment)
        }
        G.add_node(segment['id'], **node_attr)
        if 'parent_id' in segment:
            # Special case of missing parent: creates an empty parent node if
            # the segment for the given parent_id is missing.
            G.add_edge(segment['parent_id'], segment['id'])
        else:
            # Special case of missing root: the segment with the root might be missing.
            G.graph['start'] = segment['id']
        add_subsegments_recursive(G, segment)

    add_global_stats(G)
    return G


def parse_trace_segments(trace) -> list:
    return list(map(lambda s: parse_segment_json(s), trace['Segments']))


def parse_segment_json(segment_wrapper):
    return json.loads(segment_wrapper['Document'])


def invocation_type(parent_doc, child_doc) -> str:
    if is_async_call(parent_doc, child_doc):
        return 'async'
    else:
        return 'sync'


def is_async_call(parent_doc, child_doc) -> bool:
    """Heuristic to identify obvious asynchronous invocations.
    However, it might miss async calls that end before their parent
    because it is impossible to detect from traces (see qiu:20 FIRM paper).
    Hence, we cannot reliably identify synchronous invocations.
    Conceptually, child_doc['end_time'] > parent_doc['end_time']
    would implement this heuristic. However, timestamps with different
    precision (e.g., ms vs µs) can lead to calls being classified as
    async by mistake. Using a margin of precision error (e.g., 999µs)
    can mitigate this issue.
    Caveat: This can result in negative time differences in a latency breakdown!
    """
    # Additional heuristic to fix common clock inacurracy issue with Lambda.
    # We know that AWS::Lambda => AWS::Lambda::Function is always as synchronous invocation.
    # This prevents that the longest path ends prematurely in case of clock inaccuracies.
    # For example if the first AWS::Lambda::Function segment accidentally ends after
    # the AWS::Lambda segment.
    if child_doc.get('origin', None) == 'AWS::Lambda::Function':
        return False
    return parent_doc['end_time'] - child_doc['end_time'] + TIMESTAMP_MARGIN.total_seconds() < 0


def add_subsegments_recursive(G, segment):
    if 'subsegments' in segment:
        for subsegment in segment['subsegments']:
            # Trace is not completed and hence some end_time is missing
            if subsegment.get('in_progress', False):
                raise Exception(f"Subsegment {subsegment['id']} in progress.")
            attr = {
                'doc': subsegment,
                'duration': duration(subsegment),
                'subsegment': True
            }
            G.add_node(subsegment['id'], **attr)
            G.add_edge(segment['id'], subsegment['id'])
            add_subsegments_recursive(G, subsegment)
    return G


def duration(segment):
    return timediff(segment['start_time'], segment['end_time'])


def add_global_stats(G):
    """Enriches the span graph of a trace with additional metrics
    that can be accessed via G.graph[METRIC_NAME]."""
    # id of earliest time (i.e., start of trace)
    start = None
    start_time = None
    # id of latest time (i.e., end of trace)
    end = None
    end_time = None
    # List of trace ids with a downstream failure
    errors = []
    # List of trace ids causing a failure
    faults = []
    throttles = []
    G.graph['url'] = None
    G.graph['services'] = []
    # Iterate over all nodes to calculate global trace metrics
    for id, attr in G.nodes(data=True):
        if not attr:
            raise Exception(f"Node {id} has empty attributes.")
        doc = attr['doc']
        # Guess invocation type (i.e., how this trace has been invoked by its parent)
        # This cannot be done during graph construction due potentially missing parent.
        # It would naturally better fit into edges but it is mostly used in the invoked nodes.
        parent_id = next(G.predecessors(id), None)
        if parent_id is not None:
            parent_node = G.nodes[parent_id]
            if parent_node:
                parent_doc = parent_node['doc']
                attr['invocation_type'] = invocation_type(parent_doc, doc)
            else:
                msg = (
                    f"Incomplete trace {G.graph['trace_id']} because"
                    f" the parent node {parent_id} of node {id} is empty."
                )
                raise Exception(msg)
        else:  # trace root
            attr['invocation_type'] = 'client'
        # Identify trace start and end times
        if start_time is None or doc['start_time'] < start_time:
            start_time = doc['start_time']
            start = id
        if end_time is None or doc['end_time'] > end_time:
            end_time = doc['end_time']
            end = id
        # Identify relevant characteristics
        if 'origin' in doc:
            G.graph['services'].append(doc['origin'])
            if doc['origin'] == 'AWS::ApiGateway::Stage':
                G.graph['url'] = doc['http']['request']['url']
        # Keep track of special cases
        if 'error' in doc and doc['error']:
            errors.append(id)
        if 'fault' in doc and doc['fault']:
            faults.append(id)
        if 'throttle' in doc and doc['throttle']:
            throttles.append(id)

    # Validate if root node exists
    if 'start' not in G.graph:
        raise Exception('Logical root node missing.')
        # Alternative to exception: flag trace as incomplete and workaround the issue
        # Logical root missing. Assigning the earliest start time is the best we can do here.
        # logging.warning(msg)
        # G.graph['start_time'] = start_time
        # G.graph['incomplete'] = True
    # Validate logical against time-based start segment
    if G.graph['start'] == start:
        G.graph['start_time'] = start_time
    else:
        msg = (
            f"Logical first trace segment {G.graph['start']}"
            f" does not match the earliest time (sub)segment {start}."
            ' Ensure that the trace is fully connected and there are no clock issues.'
        )
        raise Exception(msg)
    # Validate trace duration against calculated trace duration but allowing for small margin
    if abs(G.graph['duration'] - timediff(start_time, end_time)) > TIMESTAMP_MARGIN:
        msg = (
            f"Trace duration {G.graph['duration']}"
            f" does not match the calculated trace duration {timediff(start_time, end_time)}"
            ' based on start and end times.'
            ' Ensure that the trace is fully connected and there are no clock issues.'
        )
        raise Exception(msg)

    # Assign globals
    G.graph['end'] = end
    G.graph['end_time'] = end_time
    G.graph['errors'] = len(errors)
    G.graph['faults'] = len(faults)
    G.graph['throttles'] = len(throttles)

    # Critical path
    G.graph['call_stack'] = call_stack(G, end)
    G.graph['longest_path'] = longest_path(G, start)
    return G


def call_stack(G, end):
    """Returns an asynchronous call stack without the root"""
    stack = []
    node = end
    while node:
        if node in stack:
            loop_start_index = stack.index(node)
            loop = stack[loop_start_index:]
            logging.debug(f"Infinite loop: {loop}")
            raise Exception(f"Detected infinite loop starting from node {node}")
        stack.append(node)
        node = next(G.predecessors(node), None)
    # Could indicate missing connection
    # assert node == G.graph['start']
    return stack


def longest_path(G, node):
    """Returns the critical path (i.e., the longest path). Initialize with the id of the start node.
    Implementation based on the paper qiu:20:
    * Url: https://www.usenix.org/conference/osdi20/presentation/qiu
    * Title: "FIRM: An Intelligent Fine-grained Resource Management Framework
              for SLO-Oriented Microservices"
    Note that line 8 `path.append(...)` produced a wrong order in the original pseudocode.
    Moving this line after the for loop (i.e., after line 13) fixed this issue.

    FIRM Implementation:
    https://gitlab.engr.illinois.edu/DEPEND/firm/-/blob/master/metrics/analysis/cpa-training-features.py#L111
    Their actual implementation uses a while loop instead of recursion and
    assumes ordered child_nodes.
    """
    path = []
    path.append(node)
    if G.out_degree(node) == 0:
        return path
    # Remove node from call stack if present
    if len(G.graph['call_stack']) > 0 and G.graph['call_stack'][-1] == node:
        G.graph['call_stack'].pop()
    sorted_children = get_sorted_children(G, node)
    last_returning_child = sorted_children[-1]
    for child in sorted_children:
        if happens_before(G, child, last_returning_child):
            last_doc = G.nodes[path[-1]]['doc']
            parent_doc = G.nodes[node]['doc']
            # Only recurse into synchronous calls if there is not already
            # a longer asynchronous call present
            if last_doc['end_time'] <= parent_doc['end_time']:
                path.extend(longest_path(G, child))
    # Conditionally recurse into last_returning_child
    parent_doc = G.nodes[node]['doc']
    child_doc = G.nodes[last_returning_child]['doc']
    if is_async_call(parent_doc, child_doc):
        # Check against call stack for asynchronous calls by only following calls that are
        # connected to the end node with the latest timestamp
        if len(G.graph['call_stack']) > 0 and G.graph['call_stack'][-1] == last_returning_child:
            path.extend(longest_path(G, last_returning_child))
    else:
        # Only recurse into synchronous calls if there is not already
        # a longer asynchronous call present
        last_doc = G.nodes[path[-1]]['doc']
        if last_doc['end_time'] <= parent_doc['end_time']:
            path.extend(longest_path(G, last_returning_child))

    return path


def get_sorted_children(G, node):
    """Returns a list of child ids sorted in ascending order
    primarily by end_time and secondarily by start_time.
    The secondary sort key is necessary to resolve special cases where
    two consecutive children have the same end_time (i.e., duration = 0ms)
    but one happens earlier indicated by an earlier start_time.
    Example timeline: start1<end1=start2=end2
    """
    succ_ids = G.successors(node)
    sorted_ids = sorted(succ_ids, key=lambda id: (G.nodes[id]['doc']['end_time'], G.nodes[id]['doc']['start_time']))  # noqa: E501
    return sorted_ids


def happens_before(G, first, second):
    """Returns true if first happens before second in sequential order."""
    first_doc = G.nodes[first]['doc']
    second_doc = G.nodes[second]['doc']
    return first_doc['end_time'] <= second_doc['start_time']


def calculate_breakdown(G):
    # Initialize cold start counter along critical path, updated along the way
    G.graph['num_cold_starts'] = 0
    longest_path = G.graph['longest_path']
    peek_iter = peekable(longest_path)
    critical_path = []
    for id in peek_iter:
        node = G.nodes[id]
        doc = G.nodes[id]['doc']
        next_id = peek_iter.peek(None)
        if next_id is not None:
            next_node = G.nodes[next_id]
            critical_path.extend(pair_path(G, peek_iter, node, next_node))
        else:
            # doc span itself
            critical_path.append({
                'start_time': doc['start_time'],
                'end_time': doc['end_time'],
                'duration': timediff(doc['start_time'], doc['end_time']),
                'resource': doc['id'],
                'type': 'span',
                'category': category_for_doc(G, doc)
            })
            # potential sync transition back to parent
            critical_path.extend(add_sync_return(G, doc))

            # OLD IMPL:
            # parent_doc_id = next(G.predecessors(id), None)
            # while parent_id and not is_async_call(parent_doc, current_doc)
            # if parent_doc_id is not None:
            #     parent_doc = G.nodes[parent_doc_id]['doc']
            #     # TODO: need to do this recursively up
            #     if not is_async_call(parent_doc, doc):
            #         critical_path.append({
            #             'start_time': doc['end_time'],
            #             'end_time': parent_doc['end_time'],
            #             'duration': timediff(doc['end_time'], parent_doc['end_time']),
            #             'source': parent_doc['id'],
            #     #        if exists ?! or from parent
            #             'category': 'sync-back'  # parent_doc['origin']
            #         })

    # Identify unique paths
    # NOTE: currently treats cold-start as a different path.
    # We might need some heuristic to identify services (alike in the XRay service map)
    G.graph['longest_path_arns'] = []
    G.graph['longest_path_names'] = []
    G.graph['longest_path_details'] = []
    for n in longest_path:
        doc = G.nodes[n]['doc']
        G.graph['longest_path_details'].append(
            {'id': doc['id'],
             'name': doc['name'],
             'start_time': doc['start_time'],
             'end_time': doc['end_time'],
             'origin': doc.get('origin', None),
             'invocation_type': G.nodes[n].get('invocation_type', None)}
        )
        G.graph['longest_path_names'].append(doc['name'])
        if 'resource_arn' in doc:
            G.graph['longest_path_arns'].append(doc['resource_arn'])
        else:
            pass
    # List critical path:
    critical_path_details = []
    curr_duration = timedelta()
    start = G.graph['start_time']
    G.graph['unclassified'] = timedelta()
    for e in critical_path:
        if e['category'] in G.graph:
            G.graph[e['category']] += e['duration']
        else:
            G.graph[e['category']] = e['duration']
        critical_path_details.append(f"{e['duration']} {e['type']}:{e['category']} \t{e['resource']}:{G.nodes[e['resource']]['doc']['name'] if e['resource'] else ''} \t{e.get('source', '')}=>{e.get('target', '')}")  # noqa: E501
        # Validation
        curr_duration += e['duration']
        assert curr_duration == timediff(start, e['end_time']), f"Summed duration {curr_duration} does not match difference to trace start_time."  # noqa: E501
    G.graph['critical_path'] = critical_path
    G.graph['critical_path_details'] = critical_path_details
    # Checks
    cp_last_target = G.graph['critical_path'][-1]['target']
    # Raise exception if the segment with the latest end time does not match the last target
    # of the critical path. Additional conditions to avoid false warnings:
    # 1) The second condition relaxes the assertion because if the last target
    # in the critical path is the same as the start node of the trace, then we can very likely
    # assume a fully synchronous trace and the non-matching end node is more likely caused by
    # a clock synchronization issue common in Lambda. Such an issue might subsequently trigger
    # the assertion failure below due to trace duration mismatch if exceeding the margin.
    # 2) The third condition ignores cases where the end node of the trace graph has
    # not been identified correctly due to exact same timestamps. The end node is identified
    # solely based on timestamps and does not consider causal relationships like the critical
    # path analysis. Hence, inspection of many traces has shown that the detailed latency breakdown
    # is correct but the identification of the end node might be wrong when done only based on time.
    # TODO: update end node identification based on causal information
    # MAYBE: think about adding flagging traces where we detect and adjust for
    # potential clock synchronization issues.
    if cp_last_target != G.graph['end'] and cp_last_target != G.graph['start'] and G.nodes[cp_last_target]['doc']['end_time'] != G.graph['end_time']:  # noqa: E501
        msg = f"Segment with latest end time ({G.graph['end']}) does not match last target ({cp_last_target}) of critical path."  # noqa: E501
        raise Exception(msg)
    assert abs(G.graph['duration'] - curr_duration) < TIMESTAMP_MARGIN, f"Trace duration {G.graph['duration']} does not match latency breakdown {curr_duration} within margin {TIMESTAMP_MARGIN}."  # noqa: E501
    # NOTE: Possible false positive if custom instrumentation uses the name 'Initialization'
    # Checking the origin for AWS::Lambda::Function and only looking at the first subsegment
    # could make this more robust if needed
    num_init_segments = G.graph['longest_path_names'].count('Initialization')
    err_msg = f"num_cold_starts ({G.graph['num_cold_starts']}) does not match the number of initialization segments ({num_init_segments})."  # noqa: E501
    assert G.graph['num_cold_starts'] == num_init_segments, err_msg
    return G


def add_sync_return(G, doc):
    critical_path = []
    parent_doc_id = next(G.predecessors(doc['id']), None)
    if parent_doc_id is not None:
        parent_doc = G.nodes[parent_doc_id]['doc']
        child = G.nodes[doc['id']]
        if child['invocation_type'] == 'sync':
            critical_path.append({
                'start_time': doc['end_time'],
                'end_time': parent_doc['end_time'],
                'duration': timediff(doc['end_time'], parent_doc['end_time']),
                'resource': parent_doc['id'],
                'source': doc['id'],
                'target': parent_doc['id'],
                'type': 'sync-receive',
                'category': category_for_doc(G, parent_doc)
            })
            critical_path.extend(add_sync_return(G, parent_doc))
    return critical_path


def pair_path(G, peek_iter, node, next_node):
    """Returns the critical sub-path for a pair of two consecutive nodes (i.e., doc, next_doc)"""
    doc = node['doc']
    next_doc = next_node['doc']
    critical_path = []
    # Handle special synchronous call into lambda function with coldstart first.
    # If is_async_call would not handle transitions from AWS::Lambda into AWS::Lambda::Function,
    # it could be categorized as async invocation by mistake due to clock synchronization issues.
    if is_cold_start_lambda_function(G, next_doc):
        G.graph['num_cold_starts'] += 1
        # This is a special case because the Initialization segment
        # caused by 'AWS::Lambda::Function' is before its parent in the timeline.
        init_doc_id = init_lambda_segment(G, next_doc)
        init_doc = G.nodes[init_doc_id]['doc']
        # implicit container init
        critical_path.append({
            'start_time': doc['start_time'],
            'end_time': init_doc['start_time'],
            'duration': timediff(doc['start_time'], init_doc['start_time']),
            'resource': doc['id'],
            'type': 'span-parent',
            'category': 'container_initialization'
        })
        # runtime init span
        critical_path.append({
            'start_time': init_doc['start_time'],
            'end_time': init_doc['end_time'],
            'duration': timediff(init_doc['start_time'], init_doc['end_time']),
            'resource': init_doc['id'],
            'type': 'span',
            'category': 'runtime_initialization'
        })
        # transition from runtime init to lambda function span
        critical_path.append({
            'start_time': init_doc['end_time'],
            'end_time': next_doc['start_time'],
            'duration': timediff(init_doc['end_time'], next_doc['start_time']),
            'resource': doc['id'],
            'source': init_doc['id'],
            'target': next_doc['id'],
            'type': 'span-parent',
            'category': category_for_doc(G, doc)
        })
        # skip two next spans being handled here as special case
        _ = next(peek_iter)  # function_id
        _ = next(peek_iter, None)  # init_id
        post_init_id = peek_iter.peek(None)
        # Handle lambda function and the span following initialization
        if post_init_id is not None:
            post_init = G.nodes[post_init_id]
            critical_path.extend(pair_path(G, peek_iter, next_node, post_init))
        else:
            # TODO: generalize and extract this code into a method (almost same as below)
            # span itself
            critical_path.append({
                'start_time': next_doc['start_time'],
                'end_time': next_doc['end_time'],
                'duration': timediff(next_doc['start_time'], next_doc['end_time']),
                'resource': next_doc['id'],
                'type': 'span',
                'category': category_for_doc(G, next_doc)
            })
            # b) time-based (alternative): current span end time <= end time of trace
            current_doc = next_doc
            # Follow predecessor of current_doc (i.e., parent)
            parent_id = next(G.predecessors(current_doc['id']))
            parent_doc = G.nodes[parent_id]['doc']
            # Ensure monotonically increasing time
            while parent_doc['end_time'] >= current_doc['end_time']:
                critical_path.append({
                    'start_time': current_doc['end_time'],
                    'end_time': parent_doc['end_time'],
                    'duration': timediff(current_doc['end_time'], parent_doc['end_time']),
                    'resource': parent_doc['id'],
                    'source': current_doc['id'],
                    'target': parent_doc['id'],
                    'type': 'sync-receive',
                    'category': category_for_doc(G, parent_doc)
                })
                current_doc = parent_doc
                # Follow predecessor of current_doc (i.e., parent)
                parent_id = next(G.predecessors(current_doc['id']), None)
                if parent_id is None:  # Returned till root
                    break
                parent_doc = G.nodes[parent_id]['doc']
    # Handle asynchronous invocations
    # NOTE: clock synchronization issues could make an invocation asynchronous
    elif next_node['invocation_type'] == 'async':
        # Adjust start if there is a different prior node in the longest path with a later end time
        latest_start = doc['start_time']
        # Count non-overlapping part in parent and overlapping part in child
        early_end = min(doc['end_time'], next_doc['start_time'])
        # doc span itself till potential adjusted end
        critical_path.append({
            'start_time': latest_start,
            'end_time': early_end,
            'duration': timediff(latest_start, early_end),
            'resource': doc['id'],
            'type': 'span',
            'category': category_for_doc(G, doc)
        })

        # Invalidate trace if detecting extreme time shifts,
        # for example due to clock synchronization issues.
        # This check ensures that time monotonically increases along the critical path
        # within a given tolerance threshold, hence avoiding negative timediff.
        if next_doc['start_time'] - doc['start_time'] + TIMESTAMP_THRESHOLD.total_seconds() < 0:
            raise Exception(f"Negative time difference between current ({doc['id']}) and next ({next_doc['id']}) segment.")  # noqa: E501

        # async doc transition to next_doc span
        critical_path.append({
            'start_time': early_end,
            'end_time': next_doc['start_time'],
            'duration': timediff(early_end, next_doc['start_time']),
            'resource': None,
            'source': doc['id'],
            'target': next_doc['id'],
            'type': 'async-send',
            'category': 'trigger'
        })
    else:  # assuming regular synchronous call (impossible to determine 100%)
        # Drill in where current doc is parent and next_doc a synchronous invocation
        if is_parent(G, doc['id'], next_doc['id']):
            # sync doc transition into next_doc span
            critical_path.append({
                'start_time': doc['start_time'],
                'end_time': next_doc['start_time'],
                'duration': timediff(doc['start_time'], next_doc['start_time']),
                'resource': doc['id'],
                'source': doc['id'],
                'target': next_doc['id'],
                'type': 'sync-send',
                'category': category_for_doc(G, doc)
            })
        else:
            # span itself
            critical_path.append({
                'start_time': doc['start_time'],
                'end_time': doc['end_time'],
                'duration': timediff(doc['start_time'], doc['end_time']),
                'resource': doc['id'],
                'type': 'span',
                'category': category_for_doc(G, doc)
            })
            # Returning synchronous call
            # critical_path.extend(add_sync_return(G, doc))
            # Handle returning calls until:
            # a) logical: current span has the same parent as the next_doc
            # parent_id = next(G.predecessors(doc['id']))
            # next_parent_id = next(G.predecessors(next_doc['id']))
            # while parent_id != next_parent_id:
            #     # Follow predecessor of current_doc (i.e., parent)
            #     current_doc = G.nodes[parent_id]['doc']
            #     parent_id = next(G.predecessors(parent_id))
            #     parent_doc = G.nodes[parent_id]['doc']
            #     # Synchronous returning
            #     critical_path.append({
            #         'start_time': current_doc['end_time'],
            #         'end_time': parent_doc['end_time'],
            #         'duration': timediff(current_doc['end_time'], parent_doc['end_time']),
            #         'source': parent_doc['id'],
            #         'category': 'return-span-broken'
            #     })

            # TODO: check whether we can re-use sync-return here?!
            # b) time-based (alternative): current span end time <= next_doc['start_time']
            current_doc = doc
            # Follow predecessor of current_doc (i.e., parent)
            parent_id = next(G.predecessors(current_doc['id']))
            parent_doc = G.nodes[parent_id]['doc']
            while parent_doc['end_time'] <= next_doc['start_time']:
                critical_path.append({
                    'start_time': current_doc['end_time'],
                    'end_time': parent_doc['end_time'],
                    'duration': timediff(current_doc['end_time'], parent_doc['end_time']),
                    'resource': parent_doc['id'],
                    'source': current_doc['id'],
                    'target': parent_doc['id'],
                    'type': 'sync-receive',
                    'category': category_for_doc(G, parent_doc)
                })
                current_doc = parent_doc
                # Follow predecessor of current_doc (i.e., parent)
                parent_id = next(G.predecessors(current_doc['id']))
                parent_doc = G.nodes[parent_id]['doc']

            # sync doc transition over and across to next_doc span via common parent
            parent_id = next(G.predecessors(next_doc['id']))
            parent_doc = G.nodes[parent_id]['doc']
            critical_path.append({
                'start_time': current_doc['end_time'],
                'end_time': next_doc['start_time'],
                'duration': timediff(current_doc['end_time'], next_doc['start_time']),
                'resource': parent_id,
                'source': current_doc['id'],
                'target': next_doc['id'],
                'type': 'span-parent',
                'category': category_for_doc(G, parent_doc)
            })

    return critical_path


def is_parent(G, candidate_parent_id, node_id):
    """Returns true if the candidate_parent_id is a predecessor
    node of the given node_id and false otherwise."""
    predecessors = G.predecessors(node_id)
    parent = next(predecessors, None)
    if parent is None:
        return False
    else:
        return parent == candidate_parent_id


def is_cold_start_lambda_function(G, doc):
    return 'origin' in doc and \
        doc['origin'] == 'AWS::Lambda::Function' and \
        init_lambda_segment(G, doc) is not None


# MAYBE: Could alternatively implement with lookahead of 3 elements
def init_lambda_segment(G, lambda_function_doc):
    """Returns the Initialization subsegment id of a lambda function or None if warm start."""
    lambda_subsegments = G.successors(lambda_function_doc['id'])
    init_subsegments = (s for s in lambda_subsegments if G.nodes[s]['doc']['name'] == 'Initialization')  # noqa: E501
    return next(init_subsegments, None)


def category_for_doc(G, doc) -> str:
    if 'origin' in doc:
        return category_for_origin(doc['origin'])

    parent_id = next(G.predecessors(doc['id']))
    parent_doc = G.nodes[parent_id]['doc']

    # special case for AWS::Lambda::Function
    # special Lambda cases
    if 'origin' in parent_doc:
        if parent_doc['origin'] == 'AWS::Lambda::Function':
            lambda_mappings = {
                'Overhead': 'overhead',
                'Invocation': 'computation',
                'Initialization': 'runtime_initialization',
                # AWS::Lambda
                'Dwell Time': 'queing'
            }
            return lambda_mappings.get(doc['name'], 'unclassified')
        if parent_doc['origin'] == 'AWS::Lambda' and doc['name'] == 'Dwell Time':
            return 'queing'

    # Use origin mapping of parent assuming that every valid trace segment has an origin field.
    return category_for_doc(G, parent_doc)


def category_for_origin(origin) -> str:
    # List of AWS resource types:
    # https://docs.aws.amazon.com/config/latest/developerguide/resource-config-reference.html
    category_mappings = {
        # Triggers
        'AWS::ApiGateway::Stage': 'orchestration',
        'AWS::StepFunctions::StateMachine': 'orchestration',
        'AWS::stepfunctions': 'orchestration',
        'AWS::STEPFUNCTIONS': 'orchestration',
        # AWS Lambda
        'AWS::Lambda': 'orchestration',
        'AWS::Lambda::Function': 'computation',
        # External services
        'AWS::S3::Bucket': 'external_service',
        'AWS::S3': 'external_service',
        'AWS::DynamoDB::Table': 'external_service',
        'AWS::SQS::Queue': 'external_service',
        'AWS::SNS': 'external_service',
        'Database::SQL': 'external_service',
        'AWS::Kinesis': 'external_service',
        'AWS::rekognition': 'external_service'
    }
    return category_mappings.get(origin, 'unclassified')


CSV_FIELDS = [
    'trace_id',
    'start_time',
    'end_time',
    'duration',
    'url',
    'num_cold_starts',
    'errors',
    'throttles',
    'faults',
    'services',
    'longest_path_names',
    # categories:
    'orchestration',
    'trigger',
    'container_initialization',
    'runtime_initialization',
    'computation',
    'queing',
    'overhead',
    'external_service',
    'unclassified'
]


def extract_trace_breakdown(trace, fields=CSV_FIELDS):
    G = create_span_graph(trace)
    G = calculate_breakdown(G)
    trace_breakdown = []
    for field in fields:
        trace_breakdown.append(G.graph.get(field, None))
    return trace_breakdown


class AwsTraceAnalyzer:
    """Parses traces.json files downloaded by the AwsTraceDownloader:
    1) Saves a trace summary into trace_breakdown.csv
    2) Saves a log of invalid trace into invalid_traces.csv
    """

    def __init__(self, log_path) -> None:
        self.log_path = log_path

    def analyze_traces(self):
        file = Path(self.log_path)
        breakdown_file = file.parent / 'trace_breakdown.csv'
        invalid_file = file.parent / 'invalid_traces.csv'

        num_valid_traces = 0
        num_invalid_traces = 0
        with open(file) as traces_json:
            with open(breakdown_file, 'w') as traces_csv, open(invalid_file, 'w') as invalid_csv:
                trace_writer = csv.writer(traces_csv, quoting=csv.QUOTE_MINIMAL)
                trace_headers = CSV_FIELDS
                trace_writer.writerow(trace_headers)
                invalid_writer = csv.writer(invalid_csv, quoting=csv.QUOTE_MINIMAL)
                invalid_headers = ['trace_id', 'message']
                invalid_writer.writerow(invalid_headers)
                for line in traces_json:
                    trace = json.loads(line)
                    try:
                        trace_breakdown = extract_trace_breakdown(trace, trace_headers)
                        trace_writer.writerow(trace_breakdown)
                        num_valid_traces += 1
                    except Exception as e:
                        trace_id = trace.get('Id')
                        message = str(e)
                        invalid_writer.writerow([trace_id, message])
                        logging.debug(f"Skip invalid trace {trace_id}. {message}")
                        num_invalid_traces += 1

        logging.info(f"Analyzed {num_valid_traces} valid traces. Written to {breakdown_file.name}.")
        if num_invalid_traces > 0:
            invalid_rate = round(num_invalid_traces / (num_valid_traces + num_invalid_traces) * 100, 2)  # noqa: E501
            logging.warning(f"Detected {num_invalid_traces} ({invalid_rate}%) invalid traces. Written to {invalid_file.name}.")  # noqa: E501
