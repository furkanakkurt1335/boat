/**
 * Bridge between the REST-style API client and Tauri invoke commands.
 * Dynamically imported from client.ts so web builds don't bundle @tauri-apps/api.
 */

let invoke: typeof import('@tauri-apps/api/core').invoke;

async function ensureInvoke() {
	if (!invoke) {
		const mod = await import('@tauri-apps/api/core');
		invoke = mod.invoke;
	}
}

/**
 * Route a REST-style API call through Tauri's `api_dispatch` command.
 * The Rust backend pattern-matches method+path to handle the request locally.
 */
export async function tauriRequest<T>(
	method: string,
	path: string,
	body?: unknown
): Promise<T> {
	await ensureInvoke();
	return invoke<T>('api_dispatch', {
		method,
		path,
		body: body ? JSON.stringify(body) : null
	});
}
