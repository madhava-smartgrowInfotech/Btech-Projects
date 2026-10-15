import api from '../api'

let current = null

/** Speak text aloud with the backend's offline text-to-speech. Resolves with the server latency in ms. */
export async function speak(text) {
  const res = await api.post('/tts', { text }, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  current?.pause()
  const audio = new Audio(url)
  current = audio
  audio.onended = () => URL.revokeObjectURL(url)
  await audio.play()
  return Number(res.headers['x-latency-ms'] || 0)
}
