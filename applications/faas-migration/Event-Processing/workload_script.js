import { check } from 'k6'
import http from 'k6/http'
import crypto from 'k6/crypto'


export default function() {
	const event_generators = [
		createTemperatureEvent,
		createForecastEvent,
		createStateChangeEvent
	]

	const event_choice = randomIntBetween(0, 2)
	const event = event_generators[event_choice]()

	// The logged output will be read by the python script
	// Valid lines to be read by python will have a special string at the start
	// console.log('transfer,' + event.type + ',' + event.source)

	const xray_header = getXrayTraceHeader()
	const res = http.post(__ENV.URL + 'ingest', JSON.stringify(event), {
		headers: {
			'Content-Type': 'application/json',
			'X-Amzn-Trace-Id': xray_header
		},
		tags: { // Each request is tagged in the metrics with the corresponding x-ray header
			xray_header: xray_header,
		}
	})

	check(res, {
		// Need to use brackets around keys as they are computed keys and not static
		[event['type'] + ' event status is 200']: (res) => res.status === 200,
	})
}

function randomIntBetween(min, max) { // min and max included
	return Math.floor(Math.random() * (max - min + 1) + min);
}

function randomString(length) {
	return crypto.hexEncode(crypto.randomBytes(Math.floor(length/2)))
}

function createTemperatureEvent() {
	return {
		type: 'temperature',
		source: randomString(30),
		timestamp: Date.now(),
		value: randomIntBetween(0, 200)
	}
}

function createForecastEvent() {
	return {
		type: 'forecast',
		source: randomString(30),
		timestamp: Date.now(),
		forecast: randomIntBetween(0, 200),
		forecast_for: randomString(10),
		place: randomString(10)
	}
}

function createStateChangeEvent() {
	return {
		type: 'state_change',
		source: randomString(30),
		timestamp: Date.now(),
		message: randomString(30)
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
