// Remembers the last assessment inputs / result (replaces the Flask session baseline).
const INPUT_KEY = 'finsight-baseline'
const RESULT_KEY = 'finsight-result'

function read(key) {
  try {
    return JSON.parse(sessionStorage.getItem(key) || 'null')
  } catch {
    return null
  }
}
function write(key, value) {
  try {
    sessionStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* storage blocked */
  }
}

export const loadBaseline = () => read(INPUT_KEY)
export const saveBaseline = (v) => write(INPUT_KEY, v)
export const loadResult = () => read(RESULT_KEY)
export const saveResult = (v) => write(RESULT_KEY, v)
