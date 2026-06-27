import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';
import classNames from 'classnames';

interface Session {
  id: string;
  title: string;
  created_at: string;
}

interface SessionSidebarProps {
  onSelectSession: (id: string) => void;
  activeSessionId?: string;
}

const SessionSidebar: React.FC<SessionSidebarProps> = ({ onSelectSession, activeSessionId }) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const getSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<Session[]>('/api/chat/sessions');
      const sortedSessions = response.data.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setSessions(sortedSessions);
    } catch (err) {
      setError('Failed to fetch sessions.');
    } finally {
      setLoading(false);
    }
  };

  const createSession = async () => {
    setError(null);
    try {
      const response = await axios.post<Session>('/api/chat/sessions', { title: 'New Chat' });
      const newSession = response.data;
      setSessions((prev) => [newSession, ...prev]);
      onSelectSession(newSession.id);
    } catch (err) {
      setError('Failed to create a new session.');
    }
  };

  useEffect(() => {
    getSessions();
  }, []);

  return (
    <div className="w-64 bg-gray-100 h-full flex flex-col border-r border-gray-300">
      <div className="p-4 border-b border-gray-300">
        <button
          onClick={createSession}
          className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
        >
          New Chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 space-y-4">
            <div className="h-6 bg-gray-300 rounded animate-pulse"></div>
            <div className="h-6 bg-gray-300 rounded animate-pulse"></div>
            <div className="h-6 bg-gray-300 rounded animate-pulse"></div>
          </div>
        ) : error ? (
          <div className="p-4 text-red-500">{error}</div>
        ) : (
          <ul>
            {sessions.map((session) => (
              <li
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={classNames(
                  'p-4 cursor-pointer hover:bg-gray-200',
                  {
                    'border-l-4 border-blue-500 bg-gray-200': session.id === activeSessionId,
                  }
                )}
              >
                <div className="font-semibold truncate">{session.title.slice(0, 30)}</div>
                <div className="text-sm text-gray-500">
                  {formatDistanceToNow(new Date(session.created_at), { addSuffix: true })}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SessionSidebar;