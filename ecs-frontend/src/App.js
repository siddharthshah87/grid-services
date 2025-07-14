import React, { useEffect, useState } from 'react';

function App() {
  const [vens, setVens] = useState([]);

  useEffect(() => {
    const url = `${process.env.REACT_APP_BACKEND_API_URL}/vens`;
    fetch(url)
      .then(res => res.json())
      .then(setVens)
      .catch(err => console.error('Failed to fetch VENs:', err));
  }, []);

  return (
    <div style={{ padding: '1rem' }}>
      <h1>Energy Control Dashboard</h1>
      <h2>Registered VENs</h2>
      <ul>
        {vens.map(ven => (
          <li key={ven.id}>{ven.id} - Shed Capability: {ven.shed_kw || 'N/A'}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;
