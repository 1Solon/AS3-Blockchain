import React, { useState } from 'react';

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

const BlockCard: React.FC<{ block: Block; index: number }> = ({ block, index }) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const toggleTransactions = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6 mb-6">
      <h2 className="text-2xl font-semibold mb-2">Block {index + 1}</h2>
      <p><strong>Mined On:</strong> {block.timestamp}</p>
      <p><strong>Nonce:</strong> {block.nonce}</p>
      <p><strong>Difficulty:</strong> {block.difficulty}</p>
      <p><strong>Block Hash:</strong> {block.hash}</p>
      <button className="bg-blue-500 text-white px-4 py-2 rounded mt-4" onClick={toggleTransactions}>
        {isOpen ? 'Hide Transactions' : 'Show Transactions'}
      </button>
      {isOpen && (
        <div className="mt-4">
          <h3 className="text-xl font-semibold">Transactions</h3>
          {block.transactions.map((tx, idx) => (
            <div key={idx} className="bg-gray-100 p-4 rounded-lg mt-2">
              <p><strong>Transaction Version:</strong> {tx.version}</p>
              <h4 className="font-semibold mt-2">Outputs:</h4>
              {tx.outputs.map((out, oidx) => (
                <p key={oidx} className="ml-4">Output {oidx + 1}: {out.value} BTC</p>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BlockCard;
