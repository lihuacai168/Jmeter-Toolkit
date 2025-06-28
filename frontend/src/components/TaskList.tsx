import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Alert, Spinner, Badge, Form, Row, Col, InputGroup } from 'react-bootstrap';
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
    const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filter states
    const [fileNameSearch, setFileNameSearch] = useState<string>('');
    const [statusFilter, setStatusFilter] = useState<string>('');

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

    // Filter tasks based on search criteria
    const filterTasks = useCallback(() => {
        let filtered = tasks;

        // Filter by file name (fuzzy search)
        if (fileNameSearch.trim()) {
            const searchTerm = fileNameSearch.trim().toLowerCase();
            filtered = filtered.filter(task =>
                task.file_name.toLowerCase().includes(searchTerm)
            );
        }

        // Filter by status (exact match)
        if (statusFilter) {
            filtered = filtered.filter(task =>
                task.status.toLowerCase() === statusFilter.toLowerCase()
            );
        }

        setFilteredTasks(filtered);
    }, [tasks, fileNameSearch, statusFilter]);

    // Apply filters when tasks or filter criteria change
    useEffect(() => {
        filterTasks();
    }, [filterTasks]);

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 5000); // Refresh every 5 seconds
        return () => clearInterval(interval);
    }, []);

    // Filter handlers
    const handleFileNameSearchChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        setFileNameSearch(event.target.value);
    }, []);

    const handleStatusFilterChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
        setStatusFilter(event.target.value);
    }, []);

    const handleClearFileNameSearch = useCallback(() => {
        setFileNameSearch('');
    }, []);

    const handleClearStatusFilter = useCallback(() => {
        setStatusFilter('');
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
            <Row className="mb-2 align-items-center">
                <Col md={2}>
                    <h2 className="mb-0">Tasks</h2>
                </Col>
                <Col md={3}>
                    <InputGroup size="sm">
                        <Form.Control
                            type="text"
                            placeholder="Search file name..."
                            value={fileNameSearch}
                            onChange={handleFileNameSearchChange}
                        />
                        {fileNameSearch && (
                            <Button
                                variant="outline-secondary"
                                onClick={handleClearFileNameSearch}
                                style={{ borderLeft: 'none' }}
                                title="Clear search"
                            >
                                ✕
                            </Button>
                        )}
                    </InputGroup>
                </Col>
                <Col md={2}>
                    <Form.Select size="sm" value={statusFilter} onChange={handleStatusFilterChange}>
                        <option value="">All Status</option>
                        <option value="pending">Pending</option>
                        <option value="running">Running</option>
                        <option value="completed">Completed</option>
                        <option value="failed">Failed</option>
                    </Form.Select>
                </Col>
                <Col md={1}>
                    {statusFilter && (
                        <Button variant="outline-secondary" size="sm" onClick={handleClearStatusFilter} title="Clear status filter">
                            ✕
                        </Button>
                    )}
                </Col>
                <Col md={2}>
                    <Button variant="secondary" size="sm" onClick={fetchTasks}>Refresh Tasks</Button>
                </Col>
                <Col md={2}>
                    <span className="text-muted">
                        {filteredTasks.length} of {tasks.length} tasks
                    </span>
                </Col>
            </Row>
            <div style={{ height: '750px', overflowY: 'auto' }}>
                <Table striped bordered hover style={{ width: '100%', tableLayout: 'fixed' }} className="mb-0">
                <thead>
                    <tr>
                        <th style={{ width: '2%' }}>ID</th>
                        <th style={{ width: '13%' }}>Task ID</th>
                        <th style={{ width: '25%' }}>File Name</th>
                        <th style={{ width: '10%' }}>Status</th>
                        <th style={{ width: '20%' }}>Created At</th>
                        <th style={{ width: '30%' }}>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredTasks.length > 0 ? filteredTasks.map((task, index) => (
                        <tr key={task.task_id}>
                            <td style={{ width: '2%', textAlign: 'center' }}>{index + 1}</td>
                            <td
                                style={{
                                    width: '13%',
                                    whiteSpace: 'nowrap',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    maxWidth: '0'
                                }}
                                title={task.task_id}
                            >
                                {task.task_id}
                            </td>
                            <td
                                style={{
                                    width: '25%',
                                    whiteSpace: 'nowrap',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    maxWidth: '0'
                                }}
                                title={task.file_name}
                            >
                                {task.file_name}
                            </td>
                            <td style={{ width: '10%' }}>{getStatusBadge(task.status)}</td>
                            <td style={{ width: '20%', whiteSpace: 'nowrap' }}>{new Date(task.created_at).toLocaleString()}</td>
                            <td style={{ width: '30%' }}>
                                <div style={{ display: 'flex', flexWrap: 'nowrap', gap: '6px', fontSize: '0.875rem' }}>
                                    {task.status.toLowerCase() === 'completed' && task.report_path && (
                                        <>
                                            <Button variant="primary" size="sm" href={`${API_URL}${task.report_path}`} target="_blank" style={{ minWidth: 'auto', padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}>
                                                View Report
                                            </Button>
                                            <Button variant="info" size="sm" onClick={() => handleDownloadReport(task.task_id)} style={{ minWidth: 'auto', padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}>
                                                Download Report
                                            </Button>
                                        </>
                                    )}
                                    {task.status.toLowerCase() === 'completed' && !task.report_path && (
                                        <Button variant="warning" size="sm" onClick={() => handleGenerateReport(task.task_id)} style={{ minWidth: 'auto', padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}>
                                            Generate Report
                                        </Button>
                                    )}
                                    {task.status.toLowerCase() === 'completed' && task.output_file && (
                                        <Button variant="secondary" size="sm" onClick={() => {
                                            if (task.output_file) {
                                                handleDownloadJtl(task.output_file);
                                            }
                                        }} style={{ minWidth: 'auto', padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}>
                                            Download JTL
                                        </Button>
                                    )}
                                </div>
                            </td>
                        </tr>
                    )) : (
                        <tr>
                            <td colSpan={6} className="text-center">No tasks found.</td>
                        </tr>
                    )}
                </tbody>
            </Table>
            </div>
        </div>
    );
};

export default TaskList;
