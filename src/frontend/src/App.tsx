import React, { useEffect, useState } from 'react';
import BlockCard from './Card';
import './App.css';

interface Output {
  value: number;
}

interface Transaction {
  version: number;
  outputs: Output[];
}

interface Block {
  timestamp: string;
  nonce: number;
  difficulty: number;
  hash: string;
  transactions: Transaction[];
}

const App: React.FC = () => {
  const [blocks, setBlocks] = useState<Block[]>([]);

  useEffect(() => {
    const fetchBlocks = async () => {
      const response = await fetch('http://localhost:5000/blocks');
      const data = await response.json();
      console.log('Fetched blocks:', data);
      setBlocks(data);
    };

    fetchBlocks();
    const interval = setInterval(fetchBlocks, 10000); // Fetch every 10 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 py-10">
      <header className="text-center mb-10">
        <h1 className="text-4xl font-bold text-gray-800">Bitcoin Block Viewer</h1>
      </header>
      <div className="max-w-5xl mx-auto px-4">
        {blocks.map((block, index) => (
          <BlockCard key={index} block={block} index={index} />
        ))}
      </div>
    </div>
  );
};

export default App;
