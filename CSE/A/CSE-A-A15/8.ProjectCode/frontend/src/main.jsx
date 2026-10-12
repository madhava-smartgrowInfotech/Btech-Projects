import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Keys from './pages/Keys'
import Send from './pages/Send'
import Receive from './pages/Receive'
import Analysis from './pages/Analysis'
import Robustness from './pages/Robustness'
import Log from './pages/Log'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route element={<Layout />}>
          <Route path="/keys" element={<Keys />} />
          <Route path="/send" element={<Send />} />
          <Route path="/receive" element={<Receive />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/robustness" element={<Robustness />} />
          <Route path="/log" element={<Log />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
