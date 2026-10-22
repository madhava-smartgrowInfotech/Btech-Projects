import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api, getToken, setToken, setUnauthorizedHandler } from './api'
import * as C from './vaultCrypto'

const AuthCtx = createContext(null)
export const useAuth = () => useContext(AuthCtx)

// The decrypted RSA private key lives only in memory; a page reload locks the vault again.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(() => !!getToken())
  const [privateKey, setPrivateKey] = useState(null)
  const keyRef = useRef(null)
  keyRef.current = privateKey

  const clear = useCallback(() => {
    setToken(null)
    setUser(null)
    setPrivateKey(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(clear)
  }, [clear])

  useEffect(() => {
    if (!getToken()) return
    api
      .me()
      .then(setUser)
      .catch(() => clear())
      .finally(() => setBooting(false))
  }, [clear])

  const unlock = useCallback(async (password) => {
    const { bundle } = await api.keyBundle()
    let b64
    try {
      b64 = await C.restorePrivateKey(bundle, password)
    } catch {
      throw new Error('Wrong password, or the stored key data is corrupted.')
    }
    const key = await C.importPrivateKey(b64)
    setPrivateKey(key)
    return key
  }, [])

  const login = useCallback(
    async (email, password) => {
      const { access_token } = await api.login(email, password)
      setToken(access_token)
      try {
        const me = await api.me()
        await unlock(password)
        setUser(me)
        return me
      } catch (err) {
        clear()
        throw err
      }
    },
    [unlock, clear],
  )

  const register = useCallback(
    async ({ name, email, password }) => {
      const keys = await C.createAccountKeys(password)
      await api.register({ name, email, password, ...keys })
      return login(email, password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      /* token may already be expired - still sign out locally */
    }
    clear()
  }, [clear])

  const lock = useCallback(() => setPrivateKey(null), [])

  const value = useMemo(
    () => ({ user, booting, privateKey, unlocked: !!privateKey, login, register, logout, unlock, lock, refresh: () => api.me().then(setUser) }),
    [user, booting, privateKey, login, register, logout, unlock, lock],
  )
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}
