import React from 'react';
import ReactDOM from 'react-dom/client';
import Workspace from './components/workspace/Workspace';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Workspace />
  </React.StrictMode>,
);
