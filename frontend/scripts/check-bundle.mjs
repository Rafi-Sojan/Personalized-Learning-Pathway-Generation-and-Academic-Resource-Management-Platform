import { readdir, stat } from 'node:fs/promises'
import { join } from 'node:path'

const assetDir = join(process.cwd(), 'dist', 'assets')
const maxJavaScriptBytes = 450 * 1024
const files = await readdir(assetDir)
const failures = []
for (const file of files.filter((name) => name.endsWith('.js'))) {
  const size = (await stat(join(assetDir, file))).size
  if (size > maxJavaScriptBytes) failures.push(`${file} is ${size} bytes; limit is ${maxJavaScriptBytes}`)
}
if (failures.length) { console.error(failures.join('\n')); process.exit(1) }
console.log(`Bundle budget passed for ${files.filter((name) => name.endsWith('.js')).length} JavaScript assets.`)
