import React from 'react';
import { Card } from 'react-bootstrap';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: string;
  className?: string;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, icon = 'bi-file-earmark-text', className = '' }) => {
  return (
    <Card className={`mb-4 ${className}`}>
      <Card.Body className="py-3">
        <div className="d-flex align-items-center">
          <i className={`bi ${icon} me-3 text-primary fs-4`}></i>
          <div>
            <h2 className="h3 mb-1">{title}</h2>
            {subtitle && <p className="text-muted mb-0">{subtitle}</p>}
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default PageHeader;