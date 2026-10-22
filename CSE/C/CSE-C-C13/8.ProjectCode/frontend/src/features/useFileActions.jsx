import { useCallback, useState } from 'react'
import { api } from '../lib/api'
import { fetchAndDecrypt, replaceFileContent, saveBlob, uploadFile } from '../lib/vault'
import { Button, Modal, useToast } from '../components/ui'
import { useAuth } from '../lib/auth'
import { useVaultKey } from './UnlockGate'

// Shared behaviour for file lists and the detail page: download, upload, replace, delete.
export function useFileActions(onChanged) {
  const toast = useToast()
  const { user } = useAuth()
  const ensureKey = useVaultKey()
  const [busyId, setBusyId] = useState(null)
  const [stage, setStage] = useState('')
  const [pendingDelete, setPendingDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const fail = (title, err) => toast({ tone: 'error', title, message: err.message, duration: 8000 })

  const download = useCallback(
    async (file) => {
      setBusyId(file.id)
      try {
        const key = await ensureKey()
        const { blob, name } = await fetchAndDecrypt(file.id, key)
        saveBlob(blob, name)
        toast({ title: 'Integrity verified', message: `${name} was decrypted locally and saved.` })
        onChanged?.()
      } catch (err) {
        fail('Download failed', err)
      } finally {
        setBusyId(null)
      }
    },
    [ensureKey, onChanged], // eslint-disable-line react-hooks/exhaustive-deps
  )

  const upload = useCallback(
    async (file) => {
      setBusyId('upload')
      try {
        await ensureKey()
        const rec = await uploadFile(file, user, setStage)
        toast({ title: 'Encrypted and uploaded', message: rec.original_filename })
        onChanged?.()
        return rec
      } catch (err) {
        fail('Upload failed', err)
        return null
      } finally {
        setBusyId(null)
        setStage('')
      }
    },
    [ensureKey, user, onChanged], // eslint-disable-line react-hooks/exhaustive-deps
  )

  const replace = useCallback(
    async (fileId, file) => {
      setBusyId('replace')
      try {
        const key = await ensureKey()
        await replaceFileContent(fileId, file, key, setStage)
        toast({ title: 'Content replaced', message: `${file.name} was re-encrypted with the existing file key.` })
        onChanged?.()
      } catch (err) {
        fail('Could not replace content', err)
      } finally {
        setBusyId(null)
        setStage('')
      }
    },
    [ensureKey, onChanged], // eslint-disable-line react-hooks/exhaustive-deps
  )

  const confirmDelete = async () => {
    setDeleting(true)
    try {
      await api.remove(pendingDelete.id)
      toast({ title: 'File deleted', message: pendingDelete.original_filename })
      const gone = pendingDelete
      setPendingDelete(null)
      onChanged?.(gone)
    } catch (err) {
      fail('Delete failed', err)
    } finally {
      setDeleting(false)
    }
  }

  const deleteDialog = (
    <Modal
      open={!!pendingDelete}
      onClose={() => !deleting && setPendingDelete(null)}
      title="Delete this file?"
      footer={
        <>
          <Button variant="ghost" onClick={() => setPendingDelete(null)} disabled={deleting}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete} loading={deleting}>
            Delete permanently
          </Button>
        </>
      }
    >
      <p className="muted">
        <strong>{pendingDelete?.original_filename}</strong> and its encrypted copy will be removed, along with every access grant. This cannot be undone. The audit log keeps a record.
      </p>
    </Modal>
  )

  return { busyId, stage, download, upload, replace, askDelete: setPendingDelete, deleteDialog }
}
