import React, { useState, useEffect } from 'react';
import { Table, Button, Alert, Spinner, Badge } from 'react-bootstrap';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface Task {
    task_id: string;
    file_name: string;
    status: string;
    created_at: string;
    report_path?: string;
    output_file?: string;
}

const TaskList = () => {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchTasks = async () => {
        try {
            setLoading(true);
            const response = await axios.get(`${API_URL}/tasks`);
            setTasks(response.data.data.tasks);
            setError(null);
        } catch (err: any) {
            setError(err.response?.data?.message || 'Could not fetch tasks.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 5000); // Refresh every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const getStatusBadge = (status: string) => {
        switch (status.toLowerCase()) {
            case 'completed':
                return <Badge bg="success">Completed</Badge>;
            case 'running':
                return <Badge bg="primary">Running</Badge>;
            case 'pending':
                return <Badge bg="secondary">Pending</Badge>;
            case 'failed':
                return <Badge bg="danger">Failed</Badge>;
            default:
                return <Badge bg="light" text="dark">{status}</Badge>;
        }
    };

    const handleDownloadJtl = (fileName: string) => {
        window.open(`${API_URL}/download/jtl/${fileName}`, '_blank');
    };

    const handleDownloadReport = (taskId: string) => {
        window.open(`${API_URL}/download-report-zip/${taskId}`, '_blank');
    };

    const handleGenerateReport = async (taskId: string) => {
        try {
            const response = await axios.post(`${API_URL}/generate-report/${taskId}`);
            if (response.data.success) {
                // 刷新任务列表以获取最新的报告路径
                fetchTasks();
                alert('HTML report generated successfully!');
            } else {
                alert('Failed to generate HTML report: ' + response.data.message);
            }
        } catch (error: any) {
            alert('Error generating HTML report: ' + (error.response?.data?.detail || error.message));
        }
    };

    if (loading && tasks.length === 0) {
        return <Spinner animation="border" />;
    }

    if (error) {
        return <Alert variant="danger">{error}</Alert>;
    }

    return (
        <div className="task-list mt-5">
            <h2>Tasks</h2>
            <Button variant="secondary" onClick={fetchTasks} className="mb-3">Refresh Tasks</Button>
            <Table striped bordered hover responsive>
                <thead>
                    <tr>
                        <th>Task ID</th>
                        <th>File Name</th>
                        <th>Status</th>
                        <th>Created At</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {tasks.length > 0 ? tasks.map(task => (
                        <tr key={task.task_id}>
                            <td>{task.task_id}</td>
                            <td>{task.file_name}</td>
                            <td>{getStatusBadge(task.status)}</td>
                            <td>{new Date(task.created_at).toLocaleString()}</td>
                            <td>
                                {task.status.toLowerCase() === 'completed' && task.report_path && (
                                    <>
                                        <Button variant="primary" size="sm" href={`${API_URL}${task.report_path}`} target="_blank" className="me-2">
                                            View Report
                                        </Button>
                                        <Button variant="info" size="sm" onClick={() => handleDownloadReport(task.task_id)} className="me-2">
                                            Download Report
                                        </Button>
                                    </>
                                )}
                                {task.status.toLowerCase() === 'completed' && !task.report_path && (
                                    <Button variant="warning" size="sm" onClick={() => handleGenerateReport(task.task_id)} className="me-2">
                                        Generate Report
                                    </Button>
                                )}
                                {task.status.toLowerCase() === 'completed' && task.output_file && (
                                    <Button variant="secondary" size="sm" onClick={() => {
                                        if (task.output_file) {
                                            handleDownloadJtl(task.output_file);
                                        }
                                    }}>
                                        Download JTL
                                    </Button>
                                )}
                            </td>
                        </tr>
                    )) : (
                        <tr>
                            <td colSpan={5} className="text-center">No tasks found.</td>
                        </tr>
                    )}
                </tbody>
            </Table>
        </div>
    );
};

export default TaskList;
