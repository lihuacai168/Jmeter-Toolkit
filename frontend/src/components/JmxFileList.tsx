import React, { useState, useEffect } from 'react';
import { Table, Button, Alert, Spinner, Toast, ToastContainer } from 'react-bootstrap';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface JmxFile {
    name: string;
    size: number;
    modified: number;
}

interface ToastMessage {
    id: number;
    title: string;
    body: string;
    variant: 'success' | 'danger';
}

const JmxFileList = () => {
    const [files, setFiles] = useState<JmxFile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    const fetchFiles = async () => {
        try {
            setLoading(true);
            const response = await axios.get(`${API_URL}/files?file_type=jmx`);
            setFiles(response.data.data.files);
            setError(null);
        } catch (err: any) {
            setError(err.response?.data?.message || 'Could not fetch JMX files.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFiles();
    }, []);

    const addToast = (title: string, body: string, variant: 'success' | 'danger') => {
        const newToast: ToastMessage = { id: Date.now(), title, body, variant };
        setToasts(prev => [...prev, newToast]);
    };

    const handleExecute = async (fileName: string) => {
        try {
            const response = await axios.post(`${API_URL}/execute`, { file_name: fileName });
            addToast('Success', `Task ${response.data.data.task_id} started for ${fileName}.`, 'success');
        } catch (err: any) {
            const errorMessage = err.response?.data?.message || 'Execution failed';
            addToast('Error', `Failed to start test for ${fileName}: ${errorMessage}`, 'danger');
        }
    };

    const handleDownload = (fileName: string) => {
        window.open(`${API_URL}/download/jmx/${fileName}`, '_blank');
    };

    if (loading) {
        return <div className="text-center"><Spinner animation="border" /></div>;
    }

    if (error) {
        return <Alert variant="danger">{error}</Alert>;
    }

    return (
        <div className="jmx-file-list">
            <Button variant="outline-secondary" size="sm" onClick={fetchFiles} className="mb-3">
                Refresh
            </Button>
            <Table striped bordered hover responsive size="sm">
                <thead>
                    <tr>
                        <th>File Name</th>
                        <th>Size</th>
                        <th>Last Modified</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {files.length > 0 ? files.map(file => (
                        <tr key={file.name}>
                            <td>{file.name}</td>
                            <td>{`${(file.size / 1024).toFixed(2)} KB`}</td>
                            <td>{new Date(file.modified * 1000).toLocaleString()}</td>
                            <td>
                                <Button variant="success" size="sm" onClick={() => handleExecute(file.name)}>
                                    Execute
                                </Button>{' '}
                                <Button variant="info" size="sm" onClick={() => handleDownload(file.name)}>
                                    Download
                                </Button>
                            </td>
                        </tr>
                    )) : (
                        <tr>
                            <td colSpan={4} className="text-center">No JMX files found.</td>
                        </tr>
                    )}
                </tbody>
            </Table>
            <ToastContainer position="bottom-end" className="p-3">
                {toasts.map(toast => (
                    <Toast key={toast.id} onClose={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} delay={5000} autohide bg={toast.variant}>
                        <Toast.Header>
                            <strong className="me-auto">{toast.title}</strong>
                            <small>now</small>
                        </Toast.Header>
                        <Toast.Body className={toast.variant === 'success' ? 'text-white' : ''}>{toast.body}</Toast.Body>
                    </Toast>
                ))}
            </ToastContainer>
        </div>
    );
};

export default JmxFileList;
