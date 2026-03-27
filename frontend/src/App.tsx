import React, { useState, useEffect } from 'react';
import QueryInterface from './components/QueryInterface';
import DocumentManager from './components/DocumentManager';
import ReportGenerator from './components/ReportGenerator';
import './App.css';

interface Tab {
  id: string;
  label: string;
  component: React.ComponentType;
}

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('query');
  const [isInitialized, setIsInitialized] = useState(false);

  // Check if app is initialized
  useEffect(() => {
    setIsInitialized(true);
    console.log('App initialized');
  }, []);

  const tabs: Tab[] = [
    {
      id: 'query',
      label: '智能问答',
      component: QueryInterface
    },
    {
      id: 'documents',
      label: '文档管理',
      component: DocumentManager
    },
    {
      id: 'reports',
      label: '报告生成',
      component: ReportGenerator
    }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || QueryInterface;

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <svg className="h-8 w-8 text-blue-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h1 className="text-xl font-semibold text-gray-900">保险文档智能问答系统</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">LangChain + LlamaIndex</span>
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto">
        <ActiveComponent />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            © 2024 保险文档智能问答系统 - Powered by LangChain & LlamaIndex
          </p>
        </div>
      </footer>
    </div>
  );
};

export default App;