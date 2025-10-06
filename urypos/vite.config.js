import path from 'path';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [vue()],
	server: {
		port: 8080,
		proxy: {
			'^/(app|api|assets|files)': {
				target: 'http://localhost:8000',
				ws: true,
				changeOrigin: true
			}
		}
	},
	resolve: {
		alias: {
			'@': path.resolve(__dirname, 'src')
		}
	},
	build: {
		outDir: '../ury/public/urypos',
		emptyOutDir: true,
		target: 'es2015',
	},
});
