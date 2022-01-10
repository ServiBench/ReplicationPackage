import { check } from 'k6'
import http from 'k6/http'
import crypto from 'k6/crypto'

// Init stage.
const url = __ENV.URL

const vu_states = {}

const actions = [
	{
		name: "DeleteTodo",
		weight: 0.1,
		is_runnable: (state) => {
			return state.todos.length > 0;
		},
		run: (state) => {
			const index = Math.floor(Math.random() * state.todos.length);
			const todo = state.todos[index]
			const res = deleteTodo(url, state.todos[index].id);
//			console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})

			state.todos.splice(index, 1);
		},
	},
	{
		name: "CreateTodo",
		weight: 0.1,
		is_runnable: (state) => {
			return state.todos.length < 10000;
		},
		run: (state) => {
			const res = createTodo(url, "hello world!", "sample description");
//			console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})

			state.todos.push({
				"id": JSON.parse(res.body).ID,
				"done": false,
			});
		},
	},
	{
		name: "ListTodos",
		weight: 0.4,
		is_runnable: (state) => true,
		run: (state) => {
			const res = listTodos(url);
//			console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})
		}
	},
	{
		name: "GetTodo",
		weight: 0.3,
		is_runnable: (state) => state.todos.length > 0,
		run: (state) => {
			const index = Math.floor(Math.random() * state.todos.length);
			const todo = state.todos[index]
			const res = getTodo(url, todo.id)
//			console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})
		}
	},
	{
		name: "MarkTodoAsDone",
		weight: 0.1,
		is_runnable: (state) => state.todos.find(x => !x.done),
		run: (state) => {
			const active_todos = state.todos.filter(x => !x.done);
			const index = Math.floor(Math.random() * active_todos.length);
			const todo = active_todos[index];
			const res = markTodoAsDone(url, todo.id)
//			console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})

			todo.done = true
		}

	}
]

export default function() {
	const state = vu_states[__VU] || { todos: [] }
//	console.log(`vu ${__VU}: ` + JSON.stringify(state))

	// Collect valid actions
	const valid_actions = actions.filter(action => action.is_runnable(state))
	if (!valid_actions) {
		throw "reached unexpected state; no valid actions to run"
	}

	// Normalize the action weights
	const valid_actions_total_weight = valid_actions.map(x => x.weight).reduce((acc, weight) => acc + weight)
	valid_actions.forEach(action => {
		action.nweight = action.weight / valid_actions_total_weight
	})
//	console.log("Candidates: " + JSON.stringify(valid_actions))

	// Select an action while accounting for weights
	let threshold = Math.random();
	const randomIndex = Math.floor(threshold * valid_actions.length);
	const action = valid_actions.find(candidate => {
		if (threshold < candidate.nweight) {
			return true;
		}
		threshold -= candidate.nweight;
		return false;
	}) || valid_actions[randomIndex];
	// console.log(`[vu ${__VU}] Action: ${action.name}`)

	// Run action and persist the modified state
	action.run(state)
	vu_states[__VU] = state
}

function listTodos(url) {
	return http.get(`${url}/lst`, getXRayHttpParams())
}

function createTodo(url, title, body) {
	let params = getXRayHttpParams()
	params['headers']['Content-Type'] = 'application/json'
	return http.request("POST", `${url}/put`, JSON.stringify({
		"title": title,
		"description": body,
	}), params )
}

function getTodo(url, id) {
	return http.get(`${url}/get?id=${id}`, getXRayHttpParams())
}

function deleteTodo(url, id) {
	return http.request("POST", `${url}/del?id=${id}`, '', getXRayHttpParams())
}

function markTodoAsDone(url, id) {
	return http.request("POST", `${url}/done?id=${id}`, '', getXRayHttpParams())
}

// Returns the default k6 http parameters with XRay header and tagging
function getXRayHttpParams() {
	const xray_header = getXrayTraceHeader()
	return {
		headers: {
			'X-Amzn-Trace-Id': xray_header
		},
		tags: { // Each request is tagged in the metrics with the corresponding x-ray header
			xray_header: xray_header,
		}
	}
}

function getXrayTraceHeader() {
	// https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html
	// 96-bit identifier
	const trace_id = crypto.hexEncode(crypto.randomBytes(12))
	const current_time_secs = Math.floor(Date.now() / 1000)

	let ab = new ArrayBuffer(4)
	let dv = new DataView(ab)
	dv.setInt32(0, current_time_secs)
	const current_time_hex = hex(ab)

	return `Root=1-${current_time_hex}-${trace_id}`
}

// Copied from https://stackoverflow.com/a/55200387
const byteToHex = [];

for (let n = 0; n <= 0xff; ++n)
{
	const hexOctet = n.toString(16).padStart(2, '0');
	byteToHex.push(hexOctet);
}

function hex(arrayBuffer)
{
	const buff = new Uint8Array(arrayBuffer);
	const hexOctets = []; // new Array(buff.length) is even faster (preallocates necessary array size), then use hexOctets[i] instead of .push()

	for (let i = 0; i < buff.length; ++i)
		hexOctets.push(byteToHex[buff[i]]);

	return hexOctets.join('');
}
