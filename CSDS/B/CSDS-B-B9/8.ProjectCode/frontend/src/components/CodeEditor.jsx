import Editor, { loader } from '@monaco-editor/react'
import * as monaco from 'monaco-editor/esm/vs/editor/editor.api'
import 'monaco-editor/esm/vs/basic-languages/python/python.contribution'
import 'monaco-editor/esm/vs/basic-languages/cpp/cpp.contribution'
import 'monaco-editor/esm/vs/basic-languages/java/java.contribution'
import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'

// Serve Monaco from the local bundle (works offline, no CDN).
self.MonacoEnvironment = { getWorker: () => new EditorWorker() }
loader.config({ monaco })

const MONACO_LANG = { python: 'python', cpp: 'cpp', java: 'java' }

export default function CodeEditor({ language, value, onChange }) {
  return (
    <Editor
      height="100%"
      language={MONACO_LANG[language]}
      value={value}
      onChange={(v) => onChange(v ?? '')}
      theme="vs-dark"
      options={{ fontSize: 14, minimap: { enabled: false }, scrollBeyondLastLine: false, automaticLayout: true, tabSize: 4 }}
    />
  )
}
