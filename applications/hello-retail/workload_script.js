import { check } from 'k6'
import http from 'k6/http'
import crypto from 'k6/crypto'

// Init stage.
const ew_url = __ENV.EVENT_WRITER_URL
const pc_url = __ENV.PRODUCT_CATALOG_URL
const pr_url = __ENV.PHOTO_RECEIVE_URL
const image_data = open(__ENV.IMAGE_FILE)

const vu_states = {}
const min_photo_id = 1000000000
const min_category_id = 0
const min_product_id = 1000000

const actions = [
	{
		name: "RegisterPhotographer",
		weight: 0.1,
		run: (state, xray_header) => {
			const photo_id = state.current_photo_id++
			
			const res = registerPhotographer(`photographer-${__VU}-${photo_id}`, photo_id, xray_header);
			// console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})
			// if (res.status != 200) console.log(JSON.stringify(res))
		},
	},
	{
		name: "NewProduct",
		weight: 0.1,
		run: (state, xray_header) => {
			const id = state.current_product_id++
			const new_cat_prob = Math.random()
			
			let cat_id = String(randomIntBetween(min_category_id, state.current_category_id+1))
			if (new_cat_prob > 0.9) {
				cat_id = String(++state.current_category_id)
			}
			const cat = `category-${cat_id}`
			
			const res = newProduct(`${__VU}000${id}`, cat, `name${id}`, `brand-${id}`, `description-${id}`, xray_header);
			// console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})
			// if (res.status != 200) console.log(JSON.stringify(res))
		},
	},
	{
		name: "ListCategories",
		weight: 0.3,
		run: (state, xray_header) => {
			const res = listCategories(xray_header)
			// console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})
			// if (res.status != 200) console.log(JSON.stringify(res))
		}
	},
	{
		name: "ListProductsByCategory",
		weight: 0.3,
		run: (state, xray_header) => {
			// Check if any categories have been initialized
			if (state.current_category_id < min_category_id) return

			const cat_id = randomIntBetween(min_category_id, state.current_category_id)
			const cat = `category-${cat_id}`
			
			const res = listProductsByCategory(cat, xray_header)
			// console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})
			// if (res.status != 200) console.log(JSON.stringify(res))
		}
	},
	{
		name: "ListProductsByID",
		weight: 0.1,
		run: (state, xray_header) => {
			// Check if any products have been initialized
			if (state.current_product_id < min_product_id) return
			const id = randomIntBetween(min_product_id, state.current_product_id)
			
			const res = listProductsByID(`${__VU}000${id}`, xray_header)
			// console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})
			// if (res.status != 200) console.log(JSON.stringify(res))
		}

	},
	{
		name: "CommitPhoto",
		weight: 0.1,
		run: (state, xray_header) => {
			// Check if any products and photographer have been initialized
			if (state.current_product_id < min_product_id) return
			if (state.current_photo_id < min_photo_id) return
			const id = randomIntBetween(min_product_id, state.current_product_id)
			const photo_id = randomIntBetween(min_photo_id, state.current_photo_id)
			
			const res = commitPhoto(`photographer-${__VU}-${photo_id}`, photo_id, `${__VU}000${id}`, image_data, xray_header)
			// console.log(JSON.stringify(res))
			check(res, {
				'status is 200': (res) => res.status === 200,
			})
			// if (res.status != 200) console.log(JSON.stringify(res))
		}

	}
]

export default function() {
	const state = vu_states[__VU] || {
		current_photo_id: min_photo_id-1,
		current_category_id: min_category_id-1,
		current_product_id: min_product_id-1
	}
	// console.log(`vu ${__VU}: ` + JSON.stringify(state))

	// Normalize the action weights
	const actions_total_weight = actions.map(x => x.weight).reduce((acc, weight) => acc + weight)

	// Select an action while accounting for weights
	let threshold = Math.random();
	const randomIndex = Math.floor(threshold * actions.length);
	const action = actions.find(candidate => {
		if (threshold < candidate.weight) {
			return true;
		}
		threshold -= candidate.weight;
		return false;
	}) || actions[randomIndex];
	// const action = actions[1]
	// console.log(`[vu ${__VU}] Action: ${action.name}`)

	const xray_header = getXrayTraceHeader()

	// Run action and persist the modified state
	action.run(state, xray_header)
	vu_states[__VU] = state
}

function registerPhotographer(pg_id, phone_number, xray_header) {
	const data = {
		'schema': 'com.nordstrom/user-info/update-phone/1-0-0',
		'id': pg_id.toString(),
		'phone': phone_number.toString(),  // random 10-digit number as String
		'origin': 'hello-retail/sb-register-photographer/dummy_id/dummy_name',
	}
	return http.post(`${ew_url}/event-writer`, JSON.stringify(data), {
		headers: {
			'Content-Type': 'application/json',
			'X-Amzn-Trace-Id': xray_header
		},
		tags: { // Each request is tagged in the metrics with the corresponding x-ray header
			'xray_header': xray_header,
		}
	})
}

function newProduct(prod_id, prod_category, prod_name, prod_brand, prod_desc, xray_header) {
	const data = {
		'schema': 'com.nordstrom/product/create/1-0-0',
		// String in JSON but needs to be numeric:
		// https://github.com/perfkit/hello-retail/blob/master/product-catalog/api/product-items-schema.json#L13
		'id': prod_id.toString(),
		'origin': 'hello-retail/sb-create-product/dummy_id/dummy_name',
		'category': prod_category.trim(),
		'name': prod_name.trim(),
		'brand': prod_brand.trim(),
		'description': prod_desc.trim(),
	}
	return http.post(`${ew_url}/event-writer`, JSON.stringify(data), {
		headers: {
			'Content-Type': 'application/json',
			'X-Amzn-Trace-Id': xray_header
		},
		tags: { // Each request is tagged in the metrics with the corresponding x-ray header
			'xray_header': xray_header,
		}
	})
}

function listCategories(xray_header) {
	return http.get(`${pc_url}/categories`, getXRayHttpParams(xray_header))
}

function listProductsByCategory(category, xray_header) {
	return http.get(`${pc_url}/products?category=${category}`, getXRayHttpParams(xray_header))  // category needs to be URI encoded!
}

function listProductsByID(product_id, xray_header) {
	return http.get(`${pc_url}/products?id=${product_id}`, getXRayHttpParams(xray_header))
}

function commitPhoto(pg_id, phone_number, item_id, image, xray_header) {
	const data = {
		'photographer': {
			'id': pg_id.toString(),
			'phone': phone_number.toString()
		},
		'For': item_id.toString(),
		'Media': image  // base64 encoded file
	}
	return http.post(`${pr_url}/sms`, JSON.stringify(data), {
		headers: {
			'Content-Type': 'application/json',
			'X-Amzn-Trace-Id': xray_header
		},
		tags: { // Each request is tagged in the metrics with the corresponding x-ray header
			'xray_header': xray_header,
		}
	})
}

function randomIntBetween(min, max) { // min and max included
	return Math.floor(Math.random() * (max - min + 1) + min);
}

// Returns the default k6 http parameters with XRay header and tagging
function getXRayHttpParams(xray_header) {
	return {
		headers: {
			'X-Amzn-Trace-Id': xray_header
		},
		tags: { // Each request is tagged in the metrics with the corresponding x-ray header
			'xray_header': xray_header,
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
