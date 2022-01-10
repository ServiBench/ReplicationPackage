import { check } from 'k6'
import http from 'k6/http'
import crypto from 'k6/crypto'

const num_different_images = parseInt(__ENV.NUM_IMAGES)
// Init stage. Each file only needs to be loaded once for many tests
const image_data_array = []
for (let i=0; i<num_different_images; i++) {
	image_data_array.push(open(__ENV.IMAGE_FILE_PREFIX + i.toString() + '.jpg'))
}
const base_url = __ENV.BASE_URL

export default function() {
	const xray_header = getXrayTraceHeader()

	const image_to_use = randomIntBetween(0, num_different_images-1)

	const res = http.request('POST', `${base_url}/upload?filename=img-${image_to_use}.jpg`, image_data_array[image_to_use], {
		headers: {
			'Content-Type': 'image/png',
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

function randomIntBetween(min, max) { // min and max included
	return Math.floor(Math.random() * (max - min + 1) + min);
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
