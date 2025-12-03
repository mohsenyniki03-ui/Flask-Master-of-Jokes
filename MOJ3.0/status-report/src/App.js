import logo from './logo.svg';
import './App.css';

import React from 'react';
import UserCount from './components/UserCount';
import JokeCount from './components/JokeCount';


function App() {
  return (
    <div className="App">
      <header className='App-header'>
        <h1>Status Report</h1>
        <UserCount />
        <JokeCount />
      </header>
    </div>
  );
}

export default App;
