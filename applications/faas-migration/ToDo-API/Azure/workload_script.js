import { check } from 'k6'
import http from 'k6/http'

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
	console.log(`[vu ${__VU}] Action: ${action.name}`)

	// Run action and persist the modified state
	action.run(state)
	vu_states[__VU] = state
}

function listTodos(url) {
	return http.get(`${url}/lst`, getTracingHttpParams())
}

function createTodo(url, title, body) {
	let params = getTracingHttpParams()
	params['headers']['Content-Type'] = 'application/json'
	return http.request("POST", `${url}/put`, JSON.stringify({
		"title": title,
		"description": body,
	}), params )
}

function getTodo(url, id) {
	return http.get(`${url}/get?id=${id}`, getTracingHttpParams())
}

function deleteTodo(url, id) {
	return http.request("POST", `${url}/del?id=${id}`, '', getTracingHttpParams())
}

function markTodoAsDone(url, id) {
	return http.request("POST", `${url}/done?id=${id}`, '', getTracingHttpParams())
}

// Returns the default k6 http parameters with additional tracing header and k6 tags
function getTracingHttpParams() {
	// TODO: implement Azure-specific tracing
	// const w3c_header = getW3cTraceHeader()
	return {
		headers: {
			// See Azure correlation headers: https://docs.microsoft.com/en-us/azure/azure-monitor/app/correlation#correlation-headers-using-w3c-tracecontext
			// W3C specification: https://w3c.github.io/trace-context/
			// 'traceparent': w3c_header
		},
		tags: { // Each request is tagged in the metrics with the corresponding x-ray header
			// w3c_header: w3c_header,
		}
	}
}
