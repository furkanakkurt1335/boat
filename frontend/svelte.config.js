import adapterNode from '@sveltejs/adapter-node';
import adapterStatic from '@sveltejs/adapter-static';

const isTauri = !!process.env.TAURI_ENV_PLATFORM || process.env.TAURI === '1';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: isTauri
			? adapterStatic({ fallback: 'index.html' })
			: adapterNode(),
		alias: {
			$components: 'src/lib/components',
			$stores: 'src/lib/stores',
			$api: 'src/lib/api',
			$utils: 'src/lib/utils'
		}
	}
};

export default config;
