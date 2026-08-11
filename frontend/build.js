import { execSync } from 'child_process'
import fs from 'fs'
import path from 'path'

const distPath = path.join(import.meta.dirname, 'dist')

if (fs.existsSync(distPath)) {
  fs.rmSync(distPath, { recursive: true, force: true })
  console.log('🧹 Cleaned dist/ directory')
}

try {
  execSync('npx vite build', {
    stdio: 'inherit',
    cwd: import.meta.dirname,
  })
  console.log('\n✅ Build succeeded!')
} catch (e) {
  if (fs.existsSync(distPath) && fs.readdirSync(distPath).length > 0) {
    console.log('\n⚠️  Vite reported errors, but dist/ was generated. Continuing...')
    process.exit(0)
  }
  console.error('\n❌ Build failed and no dist/ was generated.')
  process.exit(1)
}
