import React, { useState } from 'react';
import { reportAPI, documentAPI, type ReportRequest, type ReportResponse } from '../services/api';

const ReportGenerator: React.FC = () => {
  const [formData, setFormData] = useState<ReportRequest>({
    question: '',
    answer: '',
    sources: [],
    report_type: 'structured',
    send_email: false,
    email_recipient: ''
  });
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [downloadingReport, setDownloadingReport] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load reports on component mount
  React.useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const response = await reportAPI.listReports();
      setReports(response.reports);
    } catch (error) {
      console.error('Failed to load reports:', error);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.question || !formData.answer) {
      alert('请填写问题和答案');
      return;
    }

    setGeneratingReport(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await reportAPI.generateReport(formData);
      setSuccess('报告生成成功！');

      // Add to reports list
      setReports(prev => [{
        ...response,
        filename: response.file_path?.split('/').pop() || 'unknown.txt',
        created_at: response.timestamp
      }, ...prev]);

      // Reset form
      setFormData(prev => ({
        ...prev,
        question: '',
        answer: '',
        sources: []
      }));
    } catch (error) {
      setError('报告生成失败，请重试');
      console.error('Report generation error:', error);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleDownload = async (reportId: string, filename: string) => {
    setDownloadingReport(filename);
    try {
      const blob = await reportAPI.downloadReport(reportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('下载失败');
      console.error('Download error:', error);
    } finally {
      setDownloadingReport(null);
    }
  };

  const handleDelete = async (reportId: string) => {
    if (!confirm('确定要删除这份报告吗？')) return;

    try {
      await reportAPI.deleteReport(reportId);
      setReports(prev => prev.filter(report => report.report_id !== reportId));
    } catch (error) {
      alert('删除失败');
      console.error('Delete error:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">报告生成器</h1>

      {/* Generate Report Form */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">生成分析报告</h2>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-md mb-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border-l-4 border-green-400 p-4 rounded-md mb-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-green-700">{success}</p>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Question */}
          <div>
            <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-1">
              问题
            </label>
            <textarea
              id="question"
              name="question"
              value={formData.question}
              onChange={handleInputChange}
              placeholder="请输入您的问题"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              required
            />
          </div>

          {/* Answer */}
          <div>
            <label htmlFor="answer" className="block text-sm font-medium text-gray-700 mb-1">
              答案
            </label>
            <textarea
              id="answer"
              name="answer"
              value={formData.answer}
              onChange={handleInputChange}
              placeholder="请输入AI生成的答案"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={4}
              required
            />
          </div>

          {/* Sources */}
          <div>
            <label htmlFor="sources" className="block text-sm font-medium text-gray-700 mb-1">
              参考文档来源
            </label>
            <input
              type="text"
              id="sources"
              name="sources"
              value={formData.sources.join(', ')}
              onChange={handleInputChange}
              placeholder="用逗号分隔多个文档来源"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Report Type */}
          <div>
            <label htmlFor="report_type" className="block text-sm font-medium text-gray-700 mb-1">
              报告类型
            </label>
            <select
              id="report_type"
              name="report_type"
              value={formData.report_type}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="structured">结构化报告</option>
              <option value="detailed">详细报告</option>
            </select>
          </div>

          {/* Email Options */}
          <div className="border-t pt-6">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="send_email"
                name="send_email"
                checked={formData.send_email}
                onChange={handleInputChange}
                className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
              />
              <label htmlFor="send_email" className="text-sm font-medium text-gray-700">
                通过邮件发送报告
              </label>
            </div>

            {formData.send_email && (
              <div className="mt-3 ml-6">
                <label htmlFor="email_recipient" className="block text-sm text-gray-600 mb-1">
                  收件人邮箱
                </label>
                <input
                  type="email"
                  id="email_recipient"
                  name="email_recipient"
                  value={formData.email_recipient}
                  onChange={handleInputChange}
                  placeholder="example@email.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required={formData.send_email}
                />
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={generatingReport}
              className={`px-6 py-2 rounded-md text-white font-medium ${
                generatingReport
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              }`}
            >
              {generatingReport ? '生成中...' : '生成报告'}
            </button>
          </div>
        </form>
      </div>

      {/* Reports List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">历史报告</h2>

        {reports.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无历史报告</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    报告名称
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    生成时间
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reports.map((report, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <svg className="h-5 w-5 text-gray-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span className="text-sm font-medium text-gray-900">{report.filename}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(report.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleDownload(report.report_id, report.filename)}
                        disabled={downloadingReport === report.filename}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        {downloadingReport === report.filename ? '下载中...' : '下载'}
                      </button>
                      <button
                        onClick={() => handleDelete(report.report_id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportGenerator;