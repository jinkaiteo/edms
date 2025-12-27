import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import DocumentUploadNew from './DocumentUploadNew';

interface DocumentUploadNewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (document: any) => void;
}

const DocumentUploadNewModal: React.FC<DocumentUploadNewModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const handleSuccess = (result: any) => {
    
    // Call parent success handler to refresh document list
    if (onSuccess) {
      onSuccess(result);
    }
    
    // Close modal after successful upload
    onClose();
  };

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl sm:p-6">
                <div className="absolute right-0 top-0 hidden pr-4 pt-4 sm:block">
                  <button
                    type="button"
                    className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    onClick={onClose}
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  </button>
                </div>
                
                <div className="sm:flex sm:items-start">
                  <div className="w-full mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                    <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900 mb-6">
                      Upload New Document
                    </Dialog.Title>
                    
                    <div className="mt-2">
                      {/* Enhanced DocumentUploadNew component with success callback */}
                      <DocumentUploadNewWithModal onSuccess={handleSuccess} />
                    </div>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

// Wrapper component to add success handling to DocumentUploadNew
const DocumentUploadNewWithModal: React.FC<{ onSuccess: (result: any) => void }> = ({ onSuccess }) => {
  // We'll modify DocumentUploadNew to accept onSuccess prop
  // For now, let's create a wrapper that captures the success
  
  React.useEffect(() => {
    // Listen for successful document creation
    const handleDocumentCreated = (event: CustomEvent) => {
      onSuccess(event.detail);
    };

    window.addEventListener('documentCreated', handleDocumentCreated as EventListener);
    
    return () => {
      window.removeEventListener('documentCreated', handleDocumentCreated as EventListener);
    };
  }, [onSuccess]);

  return <DocumentUploadNew />;
};

export default DocumentUploadNewModal;