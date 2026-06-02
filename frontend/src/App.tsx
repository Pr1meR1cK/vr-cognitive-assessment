import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Subjects from './pages/Subjects';
import SubjectDetail from './pages/SubjectDetail';
import Correlation from './pages/Correlation';
import ModelMetrics from './pages/ModelMetrics';
import DataImport from './pages/DataImport';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/subjects" element={<Subjects />} />
          <Route path="/subjects/:id" element={<SubjectDetail />} />
          <Route path="/correlation" element={<Correlation />} />
          <Route path="/model" element={<ModelMetrics />} />
          <Route path="/import" element={<DataImport />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
