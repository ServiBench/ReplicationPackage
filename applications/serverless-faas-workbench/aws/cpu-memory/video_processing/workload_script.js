import { check } from 'k6'
import http from 'k6/http'
import crypto from 'k6/crypto'

const url = __ENV.URL
const body = __ENV.BODY

const data_replication = __ENV.DATA_REPLICATION
const object_key = __ENV.OBJECT_KEY


function randomIntBetween(min, max) { // min and max included
	return Math.floor(Math.random() * (max - min + 1) + min);
}

export default function() {
	const xray_header = getXrayTraceHeader()
	const data_to_use = randomIntBetween(0, data_replication-1)
	//object key elements
	const obj_key_splitted = object_key.split(".")
	const obj_key_prefix = obj_key_splitted[0]
	const obj_key_suffix = obj_key_splitted[1]

	const modified_body = body.replace(object_key, obj_key_prefix + "-" + data_to_use + "." + obj_key_suffix )
	const res = http.request('POST', url, modified_body, {
		headers: {
			'Content-Type': 'application/json',
			'X-Amzn-Trace-Id': xray_header
		},
		tags: { // Each request is tagged in the metrics with the corresponding x-ray header
			xray_header: xray_header,
		}
	})

	// to debug
	// console.log(JSON.stringify(res))

	check(res, {
		'status is 200': (res) => res.status === 200,
	})
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
