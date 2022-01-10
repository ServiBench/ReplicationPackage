import { check } from 'k6'
import http from 'k6/http'
import crypto from 'k6/crypto'

const url = __ENV.URL
const body = __ENV.BODY
const data_replication = __ENV.DATA_REPLICATION
const dataset_object_key = __ENV.DATASET_OBJECT_KEY
const model_object_key = __ENV.MODEL_OBJECT_KEY



function randomIntBetween(min, max) { // min and max included
	return Math.floor(Math.random() * (max - min + 1) + min);
}

export default function() {
	const xray_header = getXrayTraceHeader()
	const data_to_use = randomIntBetween(0, data_replication-1)
	//dataset object key elements
	const dataset_key_splitted = dataset_object_key.split(".")
	const dataset_key_prefix = dataset_key_splitted[0]
	const dataset_key_suffix = dataset_key_splitted[1]

	//model object key elements
	const model_key_splitted = model_object_key.split(".")
	const model_key_prefix = model_key_splitted[0]
	const model_key_suffix = model_key_splitted[1]

	const temp = body.replace(dataset_object_key, dataset_key_prefix + "-" + data_to_use + "." + dataset_key_suffix)
	const modified_body = temp.replace(model_object_key, model_key_prefix + "-" + data_to_use + "." + model_key_suffix)

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
