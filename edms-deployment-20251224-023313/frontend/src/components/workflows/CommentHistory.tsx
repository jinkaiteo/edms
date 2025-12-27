import React from 'react';

interface Comment {
  id: string;
  author: string;
  role: string;
  comment: string;
  timestamp: string;
  type: 'AUTHOR' | 'REVIEWER' | 'APPROVER' | 'SYSTEM';
  decision?: 'APPROVED' | 'REJECTED';
}

interface CommentHistoryProps {
  comments: Comment[];
  loading?: boolean;
}

const CommentHistory: React.FC<CommentHistoryProps> = ({ comments, loading = false }) => {
  const getCommentIcon = (type: string) => {
    switch (type) {
      case 'AUTHOR': return '✍️';
      case 'REVIEWER': return '👀';
      case 'APPROVER': return '✅';
      case 'SYSTEM': return '⚙️';
      default: return '💬';
    }
  };

  const getCommentStyle = (type: string, decision?: string) => {
    switch (type) {
      case 'AUTHOR':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'REVIEWER':
        if (decision === 'APPROVED') return 'bg-green-50 border-green-200 text-green-800';
        if (decision === 'REJECTED') return 'bg-red-50 border-red-200 text-red-800';
        return 'bg-purple-50 border-purple-200 text-purple-800';
      case 'APPROVER':
        if (decision === 'APPROVED') return 'bg-green-50 border-green-200 text-green-800';
        if (decision === 'REJECTED') return 'bg-red-50 border-red-200 text-red-800';
        return 'bg-indigo-50 border-indigo-200 text-indigo-800';
      case 'SYSTEM':
        return 'bg-gray-50 border-gray-200 text-gray-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="space-y-3">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-300 rounded w-1/4 mb-2"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!comments || comments.length === 0) {
    return (
      <div className="text-center py-6 text-gray-500">
        <div className="text-4xl mb-2">💬</div>
        <p>No comments in workflow history</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-900 flex items-center space-x-2">
        <span>📋</span>
        <span>Workflow Comment History</span>
      </h3>
      
      <div className="space-y-3 max-h-60 overflow-y-auto">
        {comments.map((comment) => (
          <div
            key={comment.id}
            className={`p-3 rounded-lg border ${getCommentStyle(comment.type, comment.decision)}`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className="text-lg">{getCommentIcon(comment.type)}</span>
                <div>
                  <span className="font-semibold text-sm">{comment.author}</span>
                  <span className="text-xs ml-2 opacity-75">({comment.role})</span>
                  {comment.decision && (
                    <span className={`ml-2 px-2 py-0.5 text-xs rounded font-medium ${
                      comment.decision === 'APPROVED' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {comment.decision}
                    </span>
                  )}
                </div>
              </div>
              <span className="text-xs opacity-60">{formatTimestamp(comment.timestamp)}</span>
            </div>
            <p className="text-sm leading-relaxed">{comment.comment}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CommentHistory;