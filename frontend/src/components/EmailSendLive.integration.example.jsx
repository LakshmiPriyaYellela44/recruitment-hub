/**
 * INTEGRATION EXAMPLE: How to use EmailSendLive in your existing pages
 * 
 * This shows how to add the live email sending feature to your candidate
 * detail page or search results.
 */

import React, { useState } from 'react';
import EmailSendLive from '../components/EmailSendLive';
import { useAuth } from '../context/AuthContext'; // Your auth context

/**
 * Example: Candidate Profile Page with Email Button
 */
export const CandidateProfileExample = ({ candidate }) => {
  const [showEmailModal, setShowEmailModal] = useState(false);
  const { token } = useAuth();

  return (
    <div className="candidate-profile">
      <h1>{candidate.name}</h1>
      <p>Email: {candidate.email}</p>
      <p>Skills: {candidate.skills?.join(', ')}</p>
      
      {/* Add this button to open email modal */}
      <button 
        className="btn-send-email"
        onClick={() => setShowEmailModal(true)}
      >
        📧 Send Email
      </button>

      {/* WebSocket Email Component - Add this */}
      {showEmailModal && (
        <EmailSendLive
          candidateId={candidate.id}
          candidateName={candidate.name}
          token={token}
          onSuccess={(result) => {
            console.log('Email sent successfully:', result.message_id);
            setShowEmailModal(false);
            // Optional: Show toast notification
            // toast.success('Email sent successfully!');
          }}
          onError={(error) => {
            console.error('Email sending failed:', error.message);
            // Optional: Show toast notification
            // toast.error('Failed to send email: ' + error.message);
          }}
          onClose={() => setShowEmailModal(false)}
        />
      )}

      {/* Rest of your page content */}
    </div>
  );
};

/**
 * Example: Search Results with Email Action
 */
export const CandidateSearchResultsExample = ({ candidates }) => {
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const { token } = useAuth();

  const handleEmailClick = (candidate) => {
    setSelectedCandidate(candidate);
    setShowEmailModal(true);
  };

  return (
    <div className="search-results">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Skills</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map(candidate => (
            <tr key={candidate.id}>
              <td>{candidate.name}</td>
              <td>{candidate.email}</td>
              <td>{candidate.skills?.join(', ')}</td>
              <td>
                {/* Add this action button */}
                <button 
                  className="btn-action"
                  onClick={() => handleEmailClick(candidate)}
                  title="Send email"
                >
                  📧 Email
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* WebSocket Email Component - Add this */}
      {showEmailModal && selectedCandidate && (
        <EmailSendLive
          candidateId={selectedCandidate.id}
          candidateName={selectedCandidate.name}
          token={token}
          onSuccess={(result) => {
            console.log('Email sent:', result.message_id);
            setShowEmailModal(false);
            // Optional: Update candidate status in table
            // Refresh the candidates list
          }}
          onError={(error) => {
            console.error('Failed:', error.message);
          }}
          onClose={() => {
            setShowEmailModal(false);
            setSelectedCandidate(null);
          }}
        />
      )}
    </div>
  );
};

/**
 * Example: Bulk Email to Multiple Candidates
 */
export const BulkEmailExample = ({ selectedCandidates }) => {
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const { token } = useAuth();

  const handleEmailSuccess = (result) => {
    console.log(`Email ${currentIndex + 1}/${selectedCandidates.length} sent:`, result.message_id);
    
    // Move to next candidate
    if (currentIndex + 1 < selectedCandidates.length) {
      setCurrentIndex(currentIndex + 1);
      // Component will re-render with new candidate
    } else {
      // All emails sent
      console.log('All emails sent!');
      setShowEmailModal(false);
      setCurrentIndex(0);
    }
  };

  if (!showEmailModal) {
    return (
      <button onClick={() => setShowEmailModal(true)}>
        📧 Send Email to {selectedCandidates.length} Candidates
      </button>
    );
  }

  const currentCandidate = selectedCandidates[currentIndex];

  return (
    <div>
      <p>Sending email {currentIndex + 1} of {selectedCandidates.length}</p>
      <progress value={currentIndex} max={selectedCandidates.length}></progress>
      
      <EmailSendLive
        candidateId={currentCandidate.id}
        candidateName={currentCandidate.name}
        token={token}
        onSuccess={handleEmailSuccess}
        onError={(error) => {
          console.error('Error sending to', currentCandidate.name, ':', error.message);
          // Skip and continue to next
          handleEmailSuccess({ message_id: 'skipped' });
        }}
        onClose={() => {
          setShowEmailModal(false);
          setCurrentIndex(0);
        }}
      />
    </div>
  );
};

/**
 * Step-by-Step Integration Instructions:
 * 
 * 1. Import the component in your existing page:
 *    import EmailSendLive from '../components/EmailSendLive';
 * 
 * 2. Add state for managing modal visibility:
 *    const [showEmailModal, setShowEmailModal] = useState(false);
 *    const { token } = useAuth(); // Get token from your auth context
 * 
 * 3. Add a button to trigger the modal:
 *    <button onClick={() => setShowEmailModal(true)}>
 *      📧 Send Email
 *    </button>
 * 
 * 4. Conditionally render the component:
 *    {showEmailModal && (
 *      <EmailSendLive
 *        candidateId={candidate.id}
 *        candidateName={candidate.name}
 *        token={token}
 *        onSuccess={(result) => {
 *          console.log('Email sent:', result.message_id);
 *          setShowEmailModal(false);
 *        }}
 *        onError={(error) => {
 *          console.error('Failed:', error.message);
 *        }}
 *        onClose={() => setShowEmailModal(false)}
 *      />
 *    )}
 * 
 * 5. That's it! The component handles:
 *    ✓ WebSocket connection
 *    ✓ Real-time status updates
 *    ✓ Form validation
 *    ✓ Error handling
 *    ✓ Loading states
 *    ✓ Success/error UI
 */
