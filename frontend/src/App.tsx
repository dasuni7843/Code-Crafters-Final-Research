import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { Layout } from './components/layout/Layout'
import { HomePage } from './pages/HomePage'
import { Module1Page } from './pages/Module1Page'
import { Module2Page } from './pages/Module2Page'
import { Module4Page } from './pages/Module4Page'
import { IntegratedPage } from './pages/IntegratedPage'
import { TrainingResultsPage } from './pages/TrainingResultsPage'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/module1" element={<Module1Page />} />
            <Route path="/module2" element={<Module2Page />} />
            <Route path="/module4" element={<Module4Page />} />
            <Route path="/integrated" element={<IntegratedPage />} />
            <Route path="/results" element={<TrainingResultsPage />} />
            <Route path="*" element={<HomePage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  )
}
