import { check } from 'k6'
import http from 'k6/http'
import crypto from 'k6/crypto'

const imageKeys = [
	__ENV.S3_KEY,
	__ENV.S3_KEY2
]

export default function() {
	const imageChoice = randomInt(imageKeys.length)
	const imageKey = imageKeys[imageChoice]
	// console.log(`image, ${imageKey}`)
	const body = JSON.stringify({
		"input": JSON.stringify({
			"userId": __ENV.USER_ID,
			"s3Bucket": __ENV.S3_BUCKET,
			"s3Key": imageKey,
		}),
		"stateMachineArn": __ENV.STATE_MACHINE_ARN
	})

	const xray_header = getXrayTraceHeader()
	const res = http.post(__ENV.URL, body, {
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
		// Need to use brackets around keys as they are computed keys and not static
		[imageKey + ' status is 200']: (res) => res.status === 200,
	})

}

function randomInt(max) { // min=0 and max included
	return Math.floor(Math.random() * max);
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
