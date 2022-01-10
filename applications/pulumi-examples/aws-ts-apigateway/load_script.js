import { check } from 'k6'
import http from 'k6/http'

export let options = {
    vus: 1,
    iterations: 3
}

export default function() {
	const res = http.get(__ENV.URL)

	// to debug
	// console.log(JSON.stringify(res))
	console.log(res.body)

	check(res, {
		'status is 200': (res) => res.status === 200,
	})
}
