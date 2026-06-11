import { spawn, spawnSync } from 'child_process'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')
const children = []
let exiting = false

function cleanup() {
  if (exiting) return
  exiting = true
  console.log('\n正在停止服务...')
  for (const child of children) {
    if (child && !child.killed) {
      try {
        if (process.platform === 'win32' && child.pid) {
          // Use taskkill on Windows to ensure child and its subtree are terminated
          try { spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F']); } catch (e) { /* ignore */ }
        } else {
          child.kill('SIGTERM')
        }
      } catch (e) {
        try { child.kill(); } catch (e) { /* ignore */ }
      }
    }
  }
  setTimeout(() => process.exit(0), 1000)
}

process.on('SIGINT', cleanup)
process.on('SIGTERM', cleanup)

console.log('启动后端服务...')
const backend = spawn('uv', ['run', 'uvicorn', 'backend.main:app', '--reload', '--port', '8000'], {
  cwd: root,
  stdio: 'inherit',
  shell: true,
})
backend.on('error', (err) => console.error('后端启动失败:', err.message))
children.push(backend)

console.log('启动前端服务...')
const frontend = spawn('npx', ['vite'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true,
})
frontend.on('error', (err) => console.error('前端启动失败:', err.message))
children.push(frontend)

backend.on('exit', (code) => {
  if (!exiting) {
    console.log(`后端已退出 (${code})`)
    cleanup()
  }
})

frontend.on('exit', (code) => {
  if (!exiting) {
    console.log(`前端已退出 (${code})`)
    cleanup()
  }
})
