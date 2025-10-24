const BASE_URL = 'http://localhost:8000' // 如后端端口不同，改这里

export async function analyzeSchema(file, agents) {
  // agents: 数组，如 ['binary','process']；发给后端时转为 JSON 字符串
  const form = new FormData()
  form.append('schema_file', file)
  form.append('agents', JSON.stringify(agents))

  const res = await fetch(`${BASE_URL}/analyze/`, {
    method: 'POST',
    body: form
  })
  if (!res.ok) {
    const txt = await res.text().catch(()=>'')
    throw new Error(`后端 ${res.status}: ${txt || res.statusText}`)
  }
  return res.json()
}
