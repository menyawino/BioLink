import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PatientHeader } from '../PatientHeader';

describe('PatientHeader', () => {
  const mockPatient = {
    id: 'TEST001',
    mrn: 'MRN001',
    name: 'John Doe',
    age: 45,
    gender: 'Male',
    dateOfBirth: '1979-01-15',
    phone: '+1-555-0123',
    address: '123 Main St, Cairo',
    riskLevel: 'moderate' as const,
    lastVisit: '2024-01-15',
  };

  it('renders patient information correctly', () => {
    render(<PatientHeader patient={mockPatient} />);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('45 years')).toBeInTheDocument();
    expect(screen.getByText('Male')).toBeInTheDocument();
  });

  it('displays risk level badge', () => {
    render(<PatientHeader patient={mockPatient} />);
    
    expect(screen.getByText(/moderate/i)).toBeInTheDocument();
  });

  it('shows patient ID and MRN', () => {
    render(<PatientHeader patient={mockPatient} />);
    
    expect(screen.getByText(/TEST001/)).toBeInTheDocument();
    expect(screen.getByText(/MRN001/)).toBeInTheDocument();
  });
});
