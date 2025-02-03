import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';

const GameLogger = () => {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const logGameChoice = (event) => {
      const newLog = {
        timestamp: new Date().toISOString(),
        gameId: sessionStorage.getItem('gameId') || 'unknown',
        round: event.detail.round,
        quadrant: event.detail.quadrant,
        choice: event.detail.choice,
        color: event.detail.color
      };

      setLogs(prevLogs => [...prevLogs, newLog]);
      
      // Send to server
      fetch('/log_choice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newLog)
      }).catch(error => console.error('Logging error:', error));
    };

    // Set up game ID on component mount
    if (!sessionStorage.getItem('gameId')) {
      sessionStorage.setItem('gameId', `game_${Date.now()}`);
    }

    // Listen for game events
    window.addEventListener('gameChoice', logGameChoice);
    return () => window.removeEventListener('gameChoice', logGameChoice);
  }, []);

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader className="text-lg font-bold">Game Logs</CardHeader>
      <CardContent>
        <div className="h-64 overflow-y-auto">
          {logs.map((log, index) => (
            <div key={index} className="mb-2 p-2 bg-gray-100 rounded">
              <div className="text-sm text-gray-600">
                {new Date(log.timestamp).toLocaleString()}
              </div>
              <div>
                Round: {log.round} | Quadrant: {log.quadrant} |
                Choice: {log.choice} | Color: {log.color}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default GameLogger;