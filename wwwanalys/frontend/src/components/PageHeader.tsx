import React from 'react';
import { Card } from 'react-bootstrap';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  className?: string;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, className = '' }) => {
  return (
    <Card className={`mb-4 ${className}`}>
      <Card.Body className="py-3">
        <div className="d-flex align-items-center">
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