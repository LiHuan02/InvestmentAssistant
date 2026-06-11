import { spawn } from 'child_process'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')

console.log('启动后端服务...')
const backend = spawn('uv', ['run', 'uvicorn', 'backend.main:app', '--reload', '--port', '8000'], {
  cwd: root,
  stdio: 'inherit',
  shell: true,
})

backend.on('error', (err) => console.error('后端启动失败:', err.message))

console.log('启动前端服务...')
const frontend = spawn('npx', ['vite'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true,
})

frontend.on('error', (err) => console.error('前端启动失败:', err.message))

process.on('SIGINT', () => { backend.kill(); frontend.kill(); process.exit() })
process.on('SIGTERM', () => { backend.kill(); frontend.kill(); process.exit() })
